import streamlit as st
from google import genai
import re
from pypdf import PdfReader
import time

# ==========================================
# 🎨 デザイン定義（サイバー×エネルギッシュ）
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
        overflow: hidden;
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
    [data-testid="stMetricValue"] { font-size: 2rem !important; color: #00E5FF !important; text-shadow: 0 0 10px rgba(0, 229, 255, 0.6); }
</style>
""", unsafe_allow_html=True)

# --- 1. セキュリティ（ログイン） ---
LOGIN_PASSWORD = "HR9237" 

def check_password():
    if "password_correct" not in st.session_state: st.session_state.password_correct = False
    if st.session_state.password_correct: return True
    st.title("システムログイン")
    pwd = st.text_input("アクセスコードを入力してください", type="password")
    if st.button("ログイン", type="primary"):
        if pwd == LOGIN_PASSWORD:
            st.session_state.password_correct = True
            st.rerun()
        else: st.error("アクセスコードが正しくありません")
    return False

if not check_password(): st.stop()

# --- ファイル解読関数 ---
def read_files(files):
    content = ""
    for f in files:
        if f.name.endswith('.txt'): content += f.getvalue().decode("utf-8") + "\n"
        elif f.name.endswith('.pdf'):
            try:
                pdf = PdfReader(f)
                for page in pdf.pages:
                    extracted = page.extract_text()
                    if extracted: content += extracted + "\n"
            except Exception: content += f"[PDF読み込みエラー: {f.name}]\n"
    return content

# --- 2. AIクライアント設定 ---
# Gemini 2.5 Flashは思考機能を備え、コスト効率と精度のバランスに優れています
client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
st.set_page_config(page_title="AIエージェントシステム", page_icon="🤖", layout="wide")

# ==========================================
# 🎛️ メインメニュー
# ==========================================
with st.sidebar:
    st.markdown("### 🎛️ メインメニュー")
    app_mode = st.radio("使用するツールを選択してください", ["1. 求職者ランク判定", "2. 企業×求職者 マッチング分析"])
    st.divider()
    st.header("♠アドバイザー情報")
    my_name = st.text_input("あなたの氏名", value="山田 太郎")

# --- セクション抽出用ヘルパー関数 ---
def get_section(name, text):
    pattern = f"【{name}】(.*?)(?=【|$)"
    match = re.search(pattern, text, re.DOTALL)
    return match.group(1).strip() if match else ""

# ==========================================
# 画面A：求職者ランク判定
# ==========================================
if app_mode == "1. 求職者ランク判定":
    st.title("求職者ランク判定プロ")
    mode = st.radio("分析モードを選択", ["1. 簡易分析", "2. 通常分析", "3. 詳細分析（書類作成あり）"], horizontal=True)

    with st.sidebar:
        st.header("👤 基本情報入力")
        age = st.number_input("年齢", 18, 65, 25, key="rank_age")
        job_changes = st.number_input("転職回数", 0, 15, 1)
        short_term = st.number_input("短期離職数", 0, 10, 0)
        st.header("🏢 志望企業情報")
        target_industry = st.text_input("志望業種", placeholder="例：IT・Web業界")
        target_job = st.text_input("志望職種", placeholder="例：エンジニア")

    achievement_text, uploaded_files = "", []
    if mode == "2. 通常分析":
        achievement_text = st.text_area("職務経歴・実績", height=150)
    elif mode == "3. 詳細分析（書類作成あり）":
        achievement_text = st.text_area("追加の実績・面談メモ", height=100)
        uploaded_files = st.file_uploader("資料を添付 (PDF/TXT)", accept_multiple_files=True, type=['txt', 'pdf'])

    if st.button("分析を開始する", type="primary"):
        with st.spinner("AI Engine ディープスキャン中..."):
            try:
                safe_ind = target_industry if target_industry else "全業種"
                safe_job = target_job if target_job else "職種全般"
                file_contents = read_files(uploaded_files)
                
                prompt = f"""あなたはプロの厳格なキャリアアドバイザーです。
【{safe_ind}】の【{safe_job}】志望者を評価し、詳細分析の場合は事実に基づいた書類作成を行ってください。虚偽は一切厳禁です。

必ず以下の形式で出力してください。
【点数】(0〜10の数字のみ)
【評価理由】(具体的理由)
【改善アドバイス】(具体的対策)
【自己PR例】(事実ベースで400字程度。詳細分析時のみ)
【志望動機例】(事実ベースで450字程度。詳細分析時のみ)
【推薦文】(詳細分析時のみ。メール口調で作成)

---
アドバイザー：株式会社ライフアップ {my_name}
実績：{achievement_text}\n資料：{file_contents}"""

                response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
                full = response.text
                
                ai_score = int(re.search(r'【点数】\s*(\d+)', full).group(1)) if re.search(r'【点数】\s*(\d+)', full) else 5
                
                total_score = (5 if 22<=age<=35 else 0) + (5 if job_changes<=2 else 0) + ai_score - (short_term * 4)
                if total_score >= 18: cn, rc = "優秀 (Class-S)", "#00ff00"
                elif total_score >= 15: cn, rc = "良好 (Class-A)", "#00e5ff"
                elif total_score >= 12: cn, rc = "標準 (Class-B)", "#ffff00"
                elif total_score >= 9: cn, rc = "要努力 (Class-C)", "#ff9900"
                else: cn, rc = "厳しい (Class-D)", "#ff0000"

                # 演出
                st.toast("成功しました", icon="🤖")
                flash_id = str(time.time())
                st.markdown(f'<div id="f-{flash_id}" style="position:fixed;top:0;left:0;width:100vw;height:100vh;background:rgba(0,229,255,0.4);z-index:9999;pointer-events:none;animation:flash-fade 0.7s forwards;"></div>', unsafe_allow_html=True)

                st.markdown('<div class="cyber-panel scan-effect">', unsafe_allow_html=True)
                st.markdown(f"### 総合評価: <span style='color:{rc}'>{cn}</span>", unsafe_allow_html=True)
                st.progress(max(0.0, min(total_score / 20.0, 1.0)))
                
                c1, c2, c3 = st.columns(3)
                c1.metric("👤 基本情報", f"{(5 if 22<=age<=35 else 0) + (5 if job_changes<=2 else 0)} pt")
                c2.metric("🤖 AI 実績", f"{ai_score} pt")
                c3.metric("⚠️ リスク", f"-{short_term * 4} pt", delta_color="inverse")
                
                st.divider()
                st.markdown(f"#### 📝 AI 評価理由\n<div class='fb-box'>{get_section('評価理由', full)}</div>", unsafe_allow_html=True)
                st.markdown(f"#### 💡 改善アドバイス\n<div class='fb-box' style='border-left-color:#00ff00;'>{get_section('改善アドバイス', full)}</div>", unsafe_allow_html=True)
                
                if mode == "3. 詳細分析（書類作成あり）":
                    st.subheader("📄 生成された応募書類")
                    st.caption("自己PR (約400字)")
                    st.code(get_section("自己PR例", full), language="text")
                    st.caption("志望動機 (約450字)")
                    st.code(get_section("志望動機例", full), language="text")
                    st.caption("企業様向け推薦メール")
                    st.code(get_section("推薦文", full), language="text")
                st.markdown("</div>", unsafe_allow_html=True)
            except Exception as e: st.error(f"❌ エラー: {e}")

# ==========================================
# 画面B：マッチング分析
# ==========================================
elif app_mode == "2. 企業×求職者 マッチング分析":
    st.title("企業×求職者 マッチング分析")
    m_mode = st.radio("分析モード", ["1. 簡易マッチング", "2. 詳細マッチング（推薦文あり）"], horizontal=True)

    c_txt, c_files, s_txt, s_files = "", [], "", []
    if m_mode == "1. 簡易マッチング":
        with st.sidebar:
            st.header("👤 求職者情報")
            m_age = st.number_input("年齢", 18, 65, 25, key="m_age")
            m_ind = st.text_input("志望業種", placeholder="例：IT・Web業界", key="m_ind")
            m_ei = st.radio("業種経験", ["あり", "なし"], index=1, horizontal=True)
            m_job = st.text_input("志望職種", placeholder="例：エンジニア", key="m_job")
            m_ej = st.radio("職種経験", ["あり", "なし"], index=1, horizontal=True)
    else:
        col1, col2 = st.columns(2)
        with col1:
            c_txt = st.text_area("企業要件", height=150, placeholder="募集要項など")
            c_files = st.file_uploader("企業資料", accept_multiple_files=True, type=['txt', 'pdf'], key="cf")
        with col2:
            s_txt = st.text_area("求職者情報", height=150, placeholder="経歴や面談メモ")
            s_files = st.file_uploader("求職者資料", accept_multiple_files=True, type=['txt', 'pdf'], key="sf")

    if st.button("マッチング分析を実行", type="primary"):
        with st.spinner("AIが相性を解析中..."):
            try:
                cfc, sfc = read_files(c_files), read_files(s_files)
                if m_mode == "1. 簡易マッチング":
                    prompt = f"ヘッドハンターとして、{m_age}歳、志望業種:{m_ind}(経験:{m_ei})、志望職種:{m_job}(経験:{m_ej})の内定可能性を100点満点で判定して。【マッチ度】【評価理由】【面接突破戦略】の形式で答えて。"
                else:
                    prompt = f"""凄腕ヘッドハンターとしてマッチング分析を行い、推薦メールを作成してください。
メールは「○○会社採用ご担当者様 お世話になっております。株式会社ライフアップの{my_name}です。」から開始。事実に忠実に作成。

【マッチ度】(数字のみ)
【評価理由】
【面接突破戦略】
【推薦文】
---
企業：{c_txt}\n{cfc}\n求職者：{s_txt}\n{sfc}"""

                response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
                full = response.text
                ms = int(re.search(r'【マッチ度】\s*(\d+)', full).group(1)) if re.search(r'【マッチ度】\s*(\d+)', full) else 50
                
                st.toast("解析完了", icon="🤖")
                flash_id = str(time.time())
                st.markdown(f'<div id="f-{flash_id}" style="position:fixed;top:0;left:0;width:100vw;height:100vh;background:rgba(0,229,255,0.4);z-index:9999;pointer-events:none;animation:flash-fade 0.7s forwards;"></div>', unsafe_allow_html=True)

                st.markdown('<div class="cyber-panel scan-effect">', unsafe_allow_html=True)
                st.subheader(f"マッチ判定スコア: {ms} / 100")
                st.progress(ms / 100)
                st.divider()
                st.markdown(f"#### ⚖️ マッチング評価理由\n<div class='fb-box'>{get_section('評価理由', full)}</div>", unsafe_allow_html=True)
                st.markdown(f"#### ⚔️ 面接突破・推薦戦略\n<div class='fb-box' style='border-left-color:#00ff00;'>{get_section('面接突破戦略', full)}</div>", unsafe_allow_html=True)
                
                if m_mode == "2. 詳細マッチング（推薦文あり）":
                    st.subheader("📧 企業様向け推薦メール")
                    st.code(get_section("推薦文", full), language="text")
                st.markdown("</div>", unsafe_allow_html=True)
            except Exception as e: st.error(f"❌ 解析エラー: {e}")





