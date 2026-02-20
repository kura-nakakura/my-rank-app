import streamlit as st
from google import genai
import re
from pypdf import PdfReader
from datetime import datetime

# ==========================================
# 🎨 プロ仕様（エンタープライズ）カスタムCSS
# ==========================================
st.markdown("""
<style>
    .stApp {
        background-color: #0A192F;
        background-image: linear-gradient(rgba(10, 25, 47, 0.95), rgba(10, 25, 47, 0.95)),
                          url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%2300e5ff' fill-opacity='0.03'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
        color: #E6F1FF;
    }
    
    .cyber-panel {
        background: rgba(17, 34, 64, 0.8);
        border: 1px solid rgba(0, 229, 255, 0.3);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        border-radius: 4px;
        padding: 25px;
        margin-top: 20px;
        position: relative;
        overflow: hidden;
    }

    .scan-effect::before {
        content: '';
        position: absolute;
        top: -50%; left: -50%; width: 200%; height: 200%;
        background: linear-gradient(to bottom, transparent, rgba(0, 229, 255, 0.4) 50%, transparent);
        transform: rotate(45deg);
        animation: scan 2.5s ease-in-out forwards;
        pointer-events: none;
    }
    @keyframes scan { 0% { top: -150%; } 100% { top: 150%; } }

    .system-notice {
        background-color: rgba(0, 229, 255, 0.1);
        border-left: 3px solid #00E5FF;
        padding: 12px 15px;
        font-size: 0.9rem;
        margin-bottom: 20px;
        color: #A8B2D1;
    }
    
    .standby-screen {
        border: 1px dashed rgba(0, 229, 255, 0.3);
        background: rgba(10, 25, 47, 0.5);
        padding: 50px 20px;
        text-align: center;
        border-radius: 4px;
        margin-top: 30px;
        color: #8892B0;
    }
    .standby-screen h3 { color: #00E5FF; letter-spacing: 2px; }
    
    .fb-box {
        background: rgba(255, 255, 255, 0.05);
        border-left: 4px solid #00E5FF;
        padding: 15px;
        margin-bottom: 15px;
        border-radius: 0 5px 5px 0;
    }
    [data-testid="stMetricValue"] { font-size: 1.8rem !important; color: #00E5FF !important; }
</style>
""", unsafe_allow_html=True)

# --- 1. セキュリティ設定 ---
LOGIN_PASSWORD = "HR9237" 

def check_password():
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False
    if st.session_state.password_correct: return True

    st.markdown("<h2 style='color:#E6F1FF; letter-spacing:3px;'>SYSTEM ACCESS</h2>", unsafe_allow_html=True)
    pwd = st.text_input("ENTER ACCESS CODE", type="password")
    if st.button("AUTHENTICATE", type="primary"):
        if pwd == LOGIN_PASSWORD:
            st.session_state.password_correct = True
            st.rerun()
        else:
            st.error("ACCESS DENIED.")
    return False

if not check_password(): st.stop()

# --- ファイル解読関数 ---
def read_files(files):
    content = ""
    for f in files:
        if f.name.endswith('.txt'):
            content += f.getvalue().decode("utf-8") + "\n"
        elif f.name.endswith('.pdf'):
            try:
                pdf = PdfReader(f)
                for page in pdf.pages:
                    extracted = page.extract_text()
                    if extracted: content += extracted + "\n"
            except Exception:
                content += f"[PDF READ ERROR: {f.name}]\n"
    return content

# --- AIクライアント設定 ---
client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
st.set_page_config(page_title="AI Agent System", layout="wide")

# ==========================================
# 🎛️ メインメニュー（サイドバー）
# ==========================================
with st.sidebar:
    st.markdown("<h3 style='color:#00E5FF; font-size:1.1rem;'>SYSTEM MODULES</h3>", unsafe_allow_html=True)
    app_mode = st.radio("モジュール選択", ["1. 求職者ランク判定", "2. マッチング分析"])
    st.divider()

# ==========================================
# 画面A：求職者ランク判定
# ==========================================
if app_mode == "1. 求職者ランク判定":
    st.markdown("<h2>求職者ランク判定 MODULE</h2>", unsafe_allow_html=True)
    mode = st.radio("解析モード", ["1. 簡易解析", "2. 通常解析（実績入力）", "3. 詳細解析（資料添付）"], horizontal=True)

    with st.sidebar:
        st.markdown("<h4 style='color:#8892B0; font-size:0.8rem;'>[ BASIC PARAMETERS ]</h4>", unsafe_allow_html=True)
        age = st.number_input("年齢", 18, 65, 25, key="rank_age")
        job_changes = st.number_input("転職回数", 0, 15, 1)
        short_term = st.number_input("短期離職数", 0, 10, 0)
        st.markdown("<br><h4 style='color:#8892B0; font-size:0.8rem;'>[ TARGET CRITERIA ]</h4>", unsafe_allow_html=True)
        target_ind = st.text_input("志望業種", placeholder="例：IT・Web業界、製造業")
        target_job = st.text_input("志望職種", placeholder="例：プロジェクトマネージャー、営業")

    achievement_text, uploaded_files = "", []
    if mode == "2. 通常解析（実績入力）":
        achievement_text = st.text_area("経歴・実績概要", height=150)
    elif mode == "3. 詳細解析（ファイル添付）":
        achievement_text = st.text_area("補足情報（任意）", height=80)
        uploaded_files = st.file_uploader("資料アップロード (PDF/TXT)", accept_multiple_files=True, type=['txt', 'pdf'])

    if st.button("ANALYSIS START", type="primary"):
        with st.spinner("AI Engine is scanning..."):
            try:
                safe_ind = target_ind if target_ind else "全業種"
                safe_job = target_job if target_job else "全職種"
                ai_score, reason_text, advice_text = 5, "簡易解析のため省略", "通常解析以上をご利用ください"
                
                if mode != "1. 簡易解析":
                    file_contents = read_files(uploaded_files)
                    prompt = f"""プロの厳格なキャリアアドバイザーとして、【{safe_ind}】の【{safe_job}】志望者を評価してください。
【点数】(0〜10の数字のみ)
【評価理由】(具体的理由)
【改善アドバイス】(修正提案)
---
実績：{achievement_text}\n資料：{file_contents}"""
                    response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
                    full_text = response.text
                    score_match = re.search(r'【点数】\s*(\d+)', full_text)
                    ai_score = int(score_match.group(1)) if score_match else ai_score
                    if "【評価理由】" in full_text and "【改善アドバイス】" in full_text:
                        reason_text = full_text.split("【評価理由】")[1].split("【改善アドバイス】")[0].strip()
                        advice_text = full_text.split("【改善アドバイス】")[1].strip()

                total_score = (5 if 22<=age<=35 else 0) + (5 if job_changes<=2 else 0) + ai_score - (short_term * 4)
                
                # ランク定義
                if total_score >= 18: r, cn, rc = "S", "Class-S (Excellent)", "#00ff00"
                elif total_score >= 15: r, cn, rc = "A", "Class-A (Good)", "#00e5ff"
                elif total_score >= 12: r, cn, rc = "B", "Class-B (Standard)", "#ffff00"
                elif total_score >= 9: r, cn, rc = "C", "Class-C (Needs Effort)", "#ff9900"
                elif total_score >= 5: r, cn, rc = "D", "Class-D (High Risk)", "#ff0000"
                else: r, cn, rc = "Z", "Error (Out of range)", "#888888"

                st.markdown(f'<div class="system-notice">[ SYSTEM ] {safe_ind} / {safe_job} スキャン完了</div>', unsafe_allow_html=True)
                st.markdown('<div class="cyber-panel scan-effect">', unsafe_allow_html=True)
                st.markdown(f"<div style='display:flex; align-items:center;'><div style='width:14px; height:14px; border-radius:50%; background:{rc}; box-shadow:0 0 10px {rc}; margin-right:15px;'></div><h2 style='color:{rc}; margin:0;'>{cn}</h2></div>", unsafe_allow_html=True)
                st.progress(max(0, min(total_score / 20, 1.0)))
                c1, c2, c3 = st.columns(3)
                c1.metric("BASE", f"{(5 if 22<=age<=35 else 0) + (5 if job_changes<=2 else 0)} pt")
                c2.metric("AI EVAL", f"{ai_score} pt")
                c3.metric("RISK", f"-{short_term * 4} pt", delta_color="inverse")
                st.markdown(f"<p style='color:#A8B2D1; font-weight:bold;'>[ EVALUATION ]</p><p>{reason_text}</p>", unsafe_allow_html=True)
                st.markdown(f"<p style='color:#A8B2D1; font-weight:bold;'>[ ADVICE ]</p><p>{advice_text}</p>", unsafe_allow_html=True)
                
                # 書き出しボタン
                report = f"REPORT: {cn}\nSCORE: {total_score}/20\nREASON: {reason_text}\nADVICE: {advice_text}"
                st.download_button("EXPORT REPORT (TXT)", report, f"report_{r}.txt")
                st.markdown("</div>", unsafe_allow_html=True)
            except Exception as e: st.error(f"Error: {e}")
    else: st.markdown('<div class="standby-screen"><h3>SYSTEM STANDBY</h3><p>パラメータを設定し解析を開始してください。</p></div>', unsafe_allow_html=True)

# ==========================================
# 画面B：マッチング分析
# ==========================================
elif app_mode == "2. マッチング分析":
    st.markdown("<h2>マッチング分析 MODULE</h2>", unsafe_allow_html=True)
    m_mode = st.radio("解析モード", ["1. 簡易解析", "2. 詳細解析（資料添付）"], horizontal=True)

    m_age, m_ind, m_job, m_ei, m_ej = 25, "", "", "なし", "なし"
    c_text, c_files, s_text, s_files = "", [], "", []

    if m_mode == "1. 簡易解析":
        with st.sidebar:
            st.markdown("<h4 style='color:#8892B0; font-size:0.8rem;'>[ QUICK SCAN ]</h4>", unsafe_allow_html=True)
            m_age = st.number_input("年齢", 18, 65, 25, key="m_age")
            m_ind = st.text_input("志望業種", placeholder="例：SaaS、人材", key="m_ind")
            m_ei = st.radio("業種経験", ["あり", "なし"], index=1, horizontal=True)
            m_job = st.text_input("志望職種", placeholder="例：カスタマーサクセス", key="m_job")
            m_ej = st.radio("職種経験", ["あり", "なし"], index=1, horizontal=True)
    else:
        st.markdown("<div class='system-notice'>企業要件と求職者データを入力してください。</div>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("<h4 style='color:#00E5FF;'>[ CORP ]</h4>", unsafe_allow_html=True)
            c_text = st.text_area("募集要項", height=150)
            c_files = st.file_uploader("企業資料 (PDF/TXT)", accept_multiple_files=True, type=['txt', 'pdf'], key="cf")
        with col2:
            st.markdown("<h4 style='color:#00E5FF;'>[ SEEKER ]</h4>", unsafe_allow_html=True)
            s_text = st.text_area("経歴・メモ", height=150)
            s_files = st.file_uploader("求職者資料 (PDF/TXT)", accept_multiple_files=True, type=['txt', 'pdf'], key="sf")

    if st.button("ANALYSIS START", type="primary"):
        with st.spinner("Analyzing fit..."):
            try:
                if m_mode == "1. 簡易解析":
                    prompt = f"ヘッドハンターとして、{m_age}歳、志望業種:{m_ind}(経験:{m_ei})、志望職種:{m_job}(経験:{m_ej})の内定可能性を100点満点で判定して。【マッチ度】(数字のみ)【評価理由】(理由)【面接突破戦略】(助言)の形式で答えて。"
                else:
                    cfc, sfc = read_files(c_files), read_files(s_files)
                    prompt = f"企業要件：{c_text}\n{cfc}\n求職者：{s_text}\n{sfc}\nを比較し100点満点でマッチング判定して。【マッチ度】(数字のみ)【評価理由】【面接突破戦略】の形式で。"
                
                response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
                full_text = response.text
                ms = int(re.search(r'【マッチ度】\s*(\d+)', full_text).group(1)) if re.search(r'【マッチ度】\s*(\d+)', full_text) else 50
                reason = full_text.split("【評価理由】")[1].split("【面接突破戦略】")[0].strip() if "【評価理由】" in full_text else full_text
                strategy = full_text.split("【面接突破戦略】")[1].strip() if "【面接突破戦略】" in full_text else ""

                if ms >= 90: r, cn, rc = "S", "Optimal Match (90%+)", "#00ff00"
                elif ms >= 75: r, cn, rc = "A", "High Probability (75%+)", "#00e5ff"
                elif ms >= 60: r, cn, rc = "B", "Borderline (60%+)", "#ffff00"
                elif ms >= 40: r, cn, rc = "C", "Concern (40%+)", "#ff9900"
                else: r, cn, rc = "D", "Mismatch (39%-)", "#ff0000"

                st.markdown('<div class="cyber-panel scan-effect">', unsafe_allow_html=True)
                st.markdown(f"<div style='display:flex; align-items:center;'><div style='width:14px; height:14px; border-radius:50%; background:{rc}; box-shadow:0 0 10px {rc}; margin-right:15px;'></div><h2 style='color:{rc}; margin:0;'>{cn}</h2></div>", unsafe_allow_html=True)
                st.progress(max(0, min(ms / 100, 1.0)))
                st.markdown(f"<p style='color:#A8B2D1; font-weight:bold;'>[ REASON ]</p><p>{reason}</p>", unsafe_allow_html=True)
                st.markdown(f"<p style='color:#A8B2D1; font-weight:bold;'>[ STRATEGY ]</p><p>{strategy}</p>", unsafe_allow_html=True)
                if ms >= 75: st.success("ACTION: PRIORITY HIGH")
                elif ms < 50: st.error("ACTION: PRIORITY LOW")
                st.markdown("</div>", unsafe_allow_html=True)
            except Exception as e: st.error(f"Error: {e}")
    else: st.markdown('<div class="standby-screen"><h3>SYSTEM STANDBY</h3><p>解析条件を入力し、スキャンを開始してください。</p></div>', unsafe_allow_html=True)
