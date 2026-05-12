import streamlit as st
from google import genai
import re
from pypdf import PdfReader
import time
from io import BytesIO
import requests
from bs4 import BeautifulSoup
import gspread
from google.oauth2.service_account import Credentials
import datetime
import openpyxl
from googleapiclient.discovery import build

# ==========================================
# システム設定・マスタ管理
# ==========================================
AGENT_SHEETS = {
    "中倉": "1mPf7VGMYEIN6hYiUWEsFEmDfLNGnx9c4fQM26dhhrM0",
    "福島": "1clnbuoPvHC3yJ9NtWpVGZihi_o5PfQO5JWC_I8h3UCU",
    "木村": "1aJzGK9LMVIjToOTD6Pe4fiGVxV1FXUDaOxY4FqhcIUc",
    "仲本": "1s1whowg_T8IloYB6XrWbK0zEKzurOU1MhwDQFz-TBZI",
    # "山田": "山田用のスプレッドシートID",
}
AGENT_LIST = list(AGENT_SHEETS.keys())


# ==========================================
# 究極のAPI通信システム（自動キーローテーション完全版）
# ==========================================
def safe_generate_content(contents, model='gemini-2.5-flash'):
    raw_keys = st.secrets.get("GEMINI_API_KEY", "")
    api_keys = [k.strip() for k in raw_keys.split(",") if k.strip()]
    if not api_keys:
        raise Exception("APIキーが設定されていません。secrets.tomlを確認してください。")

    if "current_key_idx" not in st.session_state:
        st.session_state.current_key_idx = 0

    max_retries = len(api_keys) * 2
    last_error = ""

    for attempt in range(max_retries):
        current_key = api_keys[st.session_state.current_key_idx]
        temp_client = genai.Client(api_key=current_key)

        try:
            time.sleep(1)
            resp = temp_client.models.generate_content(model=model, contents=contents)
            return resp

        except Exception as e:
            last_error = str(e)

            if "429" in last_error or "RESOURCE_EXHAUSTED" in last_error or "503" in last_error:
                if len(api_keys) > 1:
                    st.session_state.current_key_idx = (st.session_state.current_key_idx + 1) % len(api_keys)
                    st.toast(f"⚠️ 制限検知。バックアップ回線（キー{st.session_state.current_key_idx + 1}）に切り替えて再試行します...", icon="🔄")
                    time.sleep(2)
                    continue
                else:
                    st.info("⏳ 制限到達。キーが1つしかないため、枠の回復まで65秒待機します...")
                    time.sleep(65)
                    continue
            else:
                raise Exception(f"Google APIエラー発生: {last_error}")

    raise Exception(f"すべてのAPIキーが制限に達したため、処理を中断しました。数分〜数十分おいてからお試しください。\n【最終エラー】: {last_error}")


# ==========================================
# ファイル読み込み関数
# ==========================================
def read_files(files):
    content = ""
    for f in files:
        file_text = ""
        if f.name.endswith('.txt'):
            file_text = f.getvalue().decode("utf-8")
        elif f.name.endswith('.pdf'):
            try:
                pdf = PdfReader(f)
                for page in pdf.pages:
                    file_text += (page.extract_text() or "") + "\n"
                    if len(file_text) > 5000:
                        break
            except:
                file_text = f"[Error: {f.name}]\n"

        truncated_text = file_text[:5000]
        if len(file_text) > 5000:
            truncated_text += "\n...（※データ量が多すぎるため、システムが一部を省略しました）"

        content += f"■【ファイル名：{f.name}】\n{truncated_text}\n\n"

    return content


# ==========================================
# Google Docs作成機能（共有ドライブ対応・完全版）
# ==========================================
def create_google_doc(title, text_content):
    try:
        credentials_dict = dict(st.secrets["gcp_service_account"])
        scopes = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/documents']
        creds = Credentials.from_service_account_info(credentials_dict, scopes=scopes)

        docs_service = build('docs', 'v1', credentials=creds)
        drive_service = build('drive', 'v3', credentials=creds)

        FOLDER_ID = "14VDvkr4NtH6NdOa_q2G-C3vwU_Ys5E2p"
        YOUR_EMAIL = "hr@lifeap.co"

        file_metadata = {
            'name': title,
            'parents': [FOLDER_ID],
            'mimeType': 'application/vnd.google-apps.document'
        }
        doc_file = drive_service.files().create(
            body=file_metadata,
            fields='id',
            supportsAllDrives=True
        ).execute()
        document_id = doc_file.get('id')

        requests_body = [{'insertText': {'location': {'index': 1}, 'text': text_content}}]
        docs_service.documents().batchUpdate(documentId=document_id, body={'requests': requests_body}).execute()

        drive_service.permissions().create(
            fileId=document_id,
            body={
                'type': 'user',
                'role': 'writer',
                'emailAddress': YOUR_EMAIL
            },
            fields='id',
            supportsAllDrives=True
        ).execute()

        doc_url = f"https://docs.google.com/document/d/{document_id}/edit"
        return True, doc_url
    except Exception as e:
        return False, f"Google Docs作成エラー: {e}"


# ==========================================
# URL読み取り関数
# ==========================================
def get_url_text(url):
    try:
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.content, 'html.parser')
        for script in soup(["script", "style"]):
            script.extract()
        text = soup.get_text(separator='\n')
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        return text[:3000]
    except Exception as e:
        return f"[URL読み取りエラー: {e}]"


# ==========================================
# セクション抽出関数
# ==========================================
def get_section(name, text):
    pattern = f"【{name}】(.*?)(?=【|$)"
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else f"{name}の情報が生成されませんでした。プロンプトを再確認してください。"


# ==========================================
# Excelテンプレートの文字置き換え関数
# ==========================================
def fill_excel_template(template_file, replacement_dict):
    wb = openpyxl.load_workbook(template_file)

    for sheet in wb.worksheets:
        for row in sheet.iter_rows():
            for cell in row:
                if cell.value and isinstance(cell.value, str):
                    for key, val in replacement_dict.items():
                        if key in cell.value:
                            cell.value = cell.value.replace(key, str(val))

    bio = BytesIO()
    wb.save(bio)
    return bio.getvalue()


# ==========================================
# スプレッドシート転記・詳細入力メイン関数
# ==========================================
def export_to_spreadsheet(agent_name, seeker_name, interview_date, additional_data=None):
    try:
        credentials_dict = dict(st.secrets["gcp_service_account"])
        scopes = ['https://www.googleapis.com/auth/spreadsheets']
        creds = Credentials.from_service_account_info(credentials_dict, scopes=scopes)
        gc = gspread.authorize(creds)

        if agent_name in AGENT_SHEETS:
            sheet_id = AGENT_SHEETS[agent_name]
        else:
            return False, f"登録されていないエージェント名です: {agent_name}"

        sh = gc.open_by_key(sheet_id)

        try:
            original_ws = sh.worksheet("原本")
            new_sheet_name = f"{seeker_name}"

            existing_sheets = [ws.title for ws in sh.worksheets()]
            if new_sheet_name in existing_sheets:
                new_sheet_name = f"{seeker_name}_{datetime.datetime.now().strftime('%m%d%H%M')}"

            new_ws = original_ws.duplicate(insert_sheet_index=1, new_sheet_name=new_sheet_name)
            new_ws_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit#gid={new_ws.id}"

        except Exception as e:
            return False, f"原本コピー失敗: {e}"

        try:
            new_ws.update_acell('A1', f"{seeker_name} ")

            if additional_data:
                new_ws.update_acell('B4', additional_data.get("company_name", ""))
                raw_age = additional_data.get("age", "")
                age_match = re.search(r'\d+', raw_age)
                if age_match:
                    age_digits = age_match.group()
                else:
                    age_digits = ""

                new_ws.update_acell('D2', age_digits)
                new_ws.update_acell('E2', additional_data.get("change_count", ""))
                new_ws.update_acell('F2', additional_data.get("short_term_leave", ""))

                m_exp = additional_data.get("management", "")
                is_m_checked = True if "あり" in m_exp or "経験あり" in m_exp else False
                new_ws.update_acell('G2', is_m_checked)

        except Exception as e:
            st.warning(f"個別シートへの詳細書き込みに一部失敗しました: {e}")

        try:
            list_ws = sh.worksheet("求職者管理表")
            next_row = len(list_ws.col_values(5)) + 1

            final_date = interview_date if interview_date not in ["不明", "記載なし", "なし", ""] else datetime.datetime.now().strftime("%Y/%m/%d")
            hyperlink_formula = f'=HYPERLINK("{new_ws_url}", "{seeker_name}")'

            list_ws.update_cell(next_row, 5, hyperlink_formula)
            list_ws.update_cell(next_row, 6, final_date)

        except Exception as e:
            return False, f"管理表への追記失敗: {e}"

        return True, f"「{new_sheet_name}」を作成し、データを入力しました！"

    except Exception as e:
        return False, f"エラー: {e}"
