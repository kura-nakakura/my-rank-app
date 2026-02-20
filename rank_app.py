import streamlit as st
from google import genai  # ★旧 google.generativeai から新しいライブラリに変更
import re

# --- 1. セキュリティ設定 ---
# ログインパスワード（好きなものに変えてください）
LOGIN_PASSWORD = "HR9237" 

def check_password():
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False
    if st.session_state.password_correct:
        return True

    st.title(":lock: ログインが必要です")
    pwd = st.text_input("パスワードを入力してください", type="password")
    if st.button("ログイン"):
        if pwd == LOGIN_PASSWORD:
            st.session_state.password_correct = True
            st.rerun()
        else:
            st.error("パスワードが正しくありません")
    return False

if not check_password():
    st.stop()

# --- 2. AIの設定 ---
# st.secrets を使って、隠された場所からキーを呼び出します
client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])


st.set_page_config(page_title="プロ仕様・求職者ランク判定", page_icon=":chart_with_upwards_trend:")
st.title(":chart_with_upwards_trend: 求職者ランク判定プロ")

# --- 3. 分析モード選択 ---
mode = st.radio(
    "分析モードを選択してください",
    ["1. 簡易分析（基本情報のみ）", "2. 通常分析（実績AI判定あり）", "3. 詳細分析（資料添付あり）"],
    horizontal=True
)

# --- 4. 入力エリア ---
with st.sidebar:
    st.header(":bust_in_silhouette: 基本情報入力")
    age = st.number_input("年齢", 18, 65, 25)
    job_changes = st.number_input("転職回数", 0, 15, 1)
    short_term = st.number_input("短期離職数", 0, 10, 0)

achievement_text = ""
uploaded_files = []

if mode == "2. 通常分析（実績AI判定あり）":
    achievement_text = st.text_area("職務経歴・実績", placeholder="例：営業でMVP獲得...", height=150)

elif mode == "3. 詳細分析（資料添付あり）":
    achievement_text = st.text_area("追加の実績・補足事項（任意）", height=100)
    uploaded_files = st.file_uploader("履歴書・職務経歴書・企業資料を添付", accept_multiple_files=True, type=['pdf', 'txt'])

# --- 5. 判定ロジック ---
if st.button("分析を開始する"):
    with st.spinner("プロの視点で分析中..."):
        try:
            ai_score = 5  # デフォルト値
            
            # モードに応じたAIプロンプト
            if mode != "1. 簡易分析（基本情報のみ）":
                
                # ★モード3：ファイルの中身を読み込んでAIに渡す処理を追加
                file_contents = ""
                if mode == "3. 詳細分析（資料添付あり）" and uploaded_files:
                    for file in uploaded_files:
                        if file.name.endswith('.txt'):
                            file_contents += file.getvalue().decode("utf-8") + "\n"
                        # ※PDFを読み込む場合は別途 PyPDF2 などのライブラリの導入が必要です

                if mode == "2. 通常分析（実績AI判定あり）":
                    prompt = f"キャリアアドバイザーとして以下の実績を厳しく10点満点で採点し、『点数：〇点』とだけ答えて。実績：{achievement_text}"
                else:
                    prompt = f"資料と実績に基づき、求職者の市場価値を10点満点で採点し『点数：〇点』とだけ答えて。実績：{achievement_text}\n資料内容：\n{file_contents}"
                
                # ★新しいライブラリでのAI実行処理
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt
                )
                
                score_match = re.search(r'\d+', response.text)
                if score_match:
                    ai_score = int(score_match.group())

            # 総合スコア計算
            base_score = 0
            if 22 <= age <= 35: base_score += 5
            if job_changes <= 2: base_score += 5
            
            total_score = base_score + ai_score - (short_term * 4)

            # --- 修正後のランク判定ロジック ---
            if total_score >= 18: 
                rank, color = "S", "red"
            elif total_score >= 15: 
                rank, color = "A", "orange" 
            elif total_score >= 12: 
                rank, color = "B", "yellow" 
            elif total_score >= 9: 
                rank, color = "C", "green"  
            elif total_score >= 5: 
                rank, color = "D", "blue"   
            else: 
                rank, color = "Z", "gray"   

            # 表示
            st.balloons()
            st.subheader("分析結果")
            st.markdown(f"### 総合評価: :{color}[ランク {rank}] （{total_score}点 / 20点）")
            
            col1, col2, col3 = st.columns(3)
            col1.metric("基本スコア", f"{base_score}点")
            col2.metric("AI実績スコア", f"{ai_score}点")
            col3.metric("マイナス評価", f"-{short_term * 4}点")

        except Exception as e:
            st.error(f"エラーが発生しました。設定を確認してください：{e}")












