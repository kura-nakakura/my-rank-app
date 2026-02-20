import streamlit as st
from google import genai
import re
from pypdf import PdfReader
import time

# ==========================================
# 🎨 デザイン定義
# ==========================================
st.markdown("""
<style>
    .stApp {
        background-color: #0A192F;
        background-image: linear-gradient(rgba(10, 25, 47, 0.9), rgba(10, 25, 47, 0.9)),
                          url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%2300e5ff' fill-opacity='0.05'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
    }
    @keyframes flash-fade { 0% { opacity: 1; } 100% { opacity: 0; } }
    .cyber-panel {
        background: rgba(23, 42, 70, 0.7);
        border: 1px solid #00E5FF;
        box-shadow: 0 0 20px rgba(0, 229, 255, 0.4), inset 0 0 10px rgba(0, 229, 255, 0.2);
        border-radius: 10px;
        padding: 25px;
        margin-top: 20px;
        backdrop-filter: blur(5px);
        position: relative;
    }
    .scan-effect::before {
        content: ''; position: absolute; top: -50%; left: -50%; width: 200%; height: 200%;
        background: linear-gradient(to bottom, transparent, rgba(0, 229, 255, 0.4) 50%, transparent);
        transform: rotate(45deg); animation: scan 2.5s ease-in-out forwards; pointer-events: none;
    }
    @keyframes scan { 0% { top: -150%; } 100% { top: 150%; } }
    .fb-box {
        background: rgba(255, 255, 255, 0.05);
        border-left: 4px solid #00E5FF;
        padding: 15px; margin-bottom: 15px; border-radius: 0 5px 5px 0;
    }
    /* コピー用エリアのスタイル */
    .stCodeBlock { border: 1px solid #00E5FF !important; }
</style>
""", unsafe_allow_html=True)

# --- 1. セキュリティ ---
LOGIN_PASSWORD = "HR9237" 
def check_password():
    if "password_correct" not in st.session_state: st.session_state.password_correct = False
    if st.session_state.password_correct: return True
    st.title("システムログイン")
    pwd = st.text_input("アクセスコード", type="password")
    if st.button("ログイン"):
        if pwd == LOGIN_PASSWORD:
            st.session_state.password_correct = True
            st.rerun()
        else: st.error("不正なコードです")
    return False

if not check_password(): st.stop()

# --- ファイル解読 ---
def read_files(files):
    content = ""
    for f in files:
        if f.name.endswith('.txt'): content += f.getvalue().decode("utf-8") + "\n"
        elif f.name.endswith('.pdf'):
            try:
                pdf = PdfReader(f)
                for page in pdf.pages:
                    txt = page.extract_text()
                    if txt: content += txt + "\n"
            except: content += f"[ERROR: {f.name}]\n"
    return content

# --- 2. AIクライアント設定 ---
# Gemini 2.5 Flashは思考機能を備え、コスト効率と精度のバランスに優れています
client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
st.set_page_config(page_title="AI Agent OS", page_icon="🤖", layout="wide")

with st.sidebar:
    st.markdown("### 🎛️ メインメニュー")
    app_mode = st.radio("ツール選択", ["1. 求職者ランク判定", "2. 企業×求職者 マッチング分析"])
    st.divider()
    st.header("✍️ あなたの情報")
    my_name = st.text_input("アドバイザー氏名", value="山田 太郎")

# ==========================================
# 画面A：求職者ランク判定
# ==========================================
if app_mode == "1. 求職者ランク判定":
    st.title("求職者ランク判定プロ")
    mode = st.radio("モード", ["1. 簡易", "2. 通常", "3. 詳細(書類作成あり)"], horizontal=True)

    with st.sidebar:
        st.header("👤 基本情報")
        age = st.number_input("年齢", 18, 65, 25)
        job_ch = st.number_input("転職回数", 0, 15, 1)
        st_t = st.number_input("短期離職", 0, 10, 0)
        target_ind = st.text_input("志望業種", placeholder="例：IT・Web業界")
        target_job = st.text_input("志望職種", placeholder="例：エンジニア")

    ach_txt, up_files = "", []
    if mode == "2. 通常": ach_txt = st.text_area("実績", height=150)
    elif mode == "3. 詳細(書類作成あり)":
        ach_txt = st.text_area("補足(面談メモなど)", height=100)
        up_files = st.file_uploader("資料添付 (PDF/TXT)", accept_multiple_files=True, type=['txt', 'pdf'])

    if st.button("分析を開始する", type="primary"):
        with st.spinner("AI Engine Scanning..."):
            try:
                ai_score, reason_text, advice_text, pr_text, motive_text, letter_text = 5, "", "", "", "", ""
                file_contents = read_files(up_files)
                
                prompt = f"""あなたはプロのキャリアアドバイザーです。【{target_ind}】の【{target_job}】志望者を評価してください。
詳細分析の場合は、提供された事実（履歴書・文字起こし等）に基づき、一切の嘘を排除した書類作成も行います。

必ず以下の形式で出力してください。
【点数】(0〜10の数字のみ)
【評価理由】(具体的理由)
【改善アドバイス】(具体的対策)
【自己PR例】(事実ベースで400字程度。詳細分析時のみ)
【志望動機例】(事実ベースで450字程度。詳細分析時のみ)
【推薦文】(詳細分析時のみ。メール口調で作成)
---
アドバイザー名：{my_name}
実績：{ach_txt}\n資料：{file_contents}"""

                response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
                full = response.text
                
                # 抽出ロジック
                ai_score = int(re.search(r'【点数】\s*(\d+)', full).group(1)) if re.search(r'【点数】\s*(\d+)', full) else 5
                def get_section(name, text):
                    parts = text.split(f"【{name}】")
                    if len(parts) > 1: return parts[1].split("【")[0].strip()
                    return ""

                reason_text = get_section("評価理由", full)
                advice_text = get_section("改善アドバイス", full)
                pr_text = get_section("自己PR例", full)
                motive_text = get_section("志望動機例", full)
                letter_text = get_section("推薦文", full)

                total_score = (5 if 22<=age<=35 else 0) + (5 if job_ch<=2 else 0) + ai_score - (st_t * 4)
                if total_score >= 18: cn, rc = "優秀 (Class-S)", "#00ff00"
                elif total_score >= 15: cn, rc = "良好 (Class-A)", "#00e5ff"
                elif total_score >= 12: cn, rc = "標準 (Class-B)", "#ffff00"
                elif total_score >= 9: cn, rc = "要努力 (Class-C)", "#ff9900"
                else: cn, rc = "厳しい (Class-D)", "#ff0000"

                # 演出
                st.toast("解析完了", icon="🤖")
                st.markdown(f'<div style="position:fixed;top:0;left:0;width:100vw;height:100vh;background:rgba(0,229,255,0.4);z-index:9999;pointer-events:none;animation:flash-fade 0.7s forwards;"></div>', unsafe_allow_html=True)
                
                st.markdown('<div class="cyber-panel scan-effect">', unsafe_allow_html=True)
                st.markdown(f"### 総合評価: <span style='color:{rc}'>{cn}</span>", unsafe_allow_html=True)
                st.progress(max(0.0, min(total_score / 20.0, 1.0)))
                st.markdown(f"#### 📝 AI 評価理由\n{reason_text}")
                
                if mode == "3. 詳細(書類作成あり)":
                    st.divider()
                    st.subheader("📄 生成された応募書類 (コピーして利用可)")
                    st.caption("自己PR (約400字)")
                    st.code(pr_text, language="text")
                    st.caption("志望動機 (約450字)")
                    st.code(motive_text, language="text")
                    st.caption("企業様向け推薦メール")
                    st.code(letter_text, language="text")
                st.markdown("</div>", unsafe_allow_html=True)
            except Exception as e: st.error(f"Error: {e}")

# ==========================================
# 画面B：マッチング分析
# ==========================================
elif app_mode == "2. 企業×求職者 マッチング分析":
    st.title("企業×求職者 マッチング分析")
    m_mode = st.radio("モード", ["1. 簡易", "2. 詳細(推薦文あり)"], horizontal=True)

    c_txt, c_files, s_txt, s_files = "", [], "", []
    if m_mode == "2. 詳細(推薦文あり)":
        col1, col2 = st.columns(2)
        with col1:
            c_txt = st.text_area("企業要件", height=150)
            c_files = st.file_uploader("企業資料", accept_multiple_files=True, type=['txt', 'pdf'], key="cf")
        with col2:
            s_txt = st.text_area("求職者メモ", height=150)
            s_files = st.file_uploader("求職者資料", accept_multiple_files=True, type=['txt', 'pdf'], key="sf")

    if st.button("分析を実行", type="primary"):
        with st.spinner("Analyzing Match..."):
            try:
                cfc, sfc = read_files(c_files), read_files(s_files)
                prompt = f"""あなたは凄腕ヘッドハンターです。企業と求職者の相性を100点満点で判定し、企業への推薦文を作成してください。
推薦文はメール口調で、「○○会社採用ご担当者様 お世話になっております。キャリアアドバイザー株式会社ライフアップの{my_name}です。」から始めてください。
虚偽は一切含めず、提出された資料の事実のみを使ってください。

【マッチ度】(数字のみ)
【評価理由】
【面接突破戦略】
【推薦文】
---
企業要件：{c_txt}\n{cfc}\n求職者：{s_txt}\n{sfc}"""

                response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
                full = response.text
                ms = int(re.search(r'【マッチ度】\s*(\d+)', full).group(1)) if re.search(r'【マッチ度】\s*(\d+)', full) else 50
                
                def get_section(name, text):
                    parts = text.split(f"【{name}】")
                    if len(parts) > 1: return parts[1].split("【")[0].strip()
                    return ""

                st.toast("解析完了", icon="🤖")
                st.markdown(f'<div style="position:fixed;top:0;left:0;width:100vw;height:100vh;background:rgba(0,229,255,0.4);z-index:9999;pointer-events:none;animation:flash-fade 0.7s forwards;"></div>', unsafe_allow_html=True)

                st.markdown('<div class="cyber-panel">', unsafe_allow_html=True)
                st.subheader(f"判定スコア: {ms} / 100")
                st.progress(ms / 100)
                st.markdown(f"**理由:** {get_section('評価理由', full)}")
                
                if m_mode == "2. 詳細(推薦文あり)":
                    st.divider()
                    st.subheader("📧 企業様向け推薦メール (コピー可)")
                    st.code(get_section("推薦文", full), language="text")
                st.markdown("</div>", unsafe_allow_html=True)
            except Exception as e: st.error(f"Error: {e}")





