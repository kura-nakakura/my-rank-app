import streamlit as st
from google import genai
import re
from pypdf import PdfReader
import time # ★追加：エフェクトのタイミング制御用

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
        content: '';
        position: absolute;
        top: -50%; left: -50%; width: 200%; height: 200%;
        background: linear-gradient(to bottom, transparent, rgba(0, 229, 255, 0.4) 50%, transparent);
        transform: rotate(45deg);
        animation: scan 2.5s ease-in-out forwards;
        pointer-events: none;
    }
    @keyframes scan { 0% { top: -150%; } 100% { top: 150%; } }
    
    /* 閃光エフェクトの定義 */
    @keyframes flash-fade {
        0% { opacity: 1; }
        100% { opacity: 0; }
    }

    [data-testid="stMetricValue"] {
        font-size: 2rem !important;
        color: #00E5FF !important;
        text-shadow: 0 0 10px rgba(0, 229, 255, 0.6);
    }
    .fb-box {
        background: rgba(255, 255, 255, 0.05);
        border-left: 4px solid #00E5FF;
        padding: 15px;
        margin-bottom: 15px;
        border-radius: 0 5px 5px 0;
    }
</style>
""", unsafe_allow_html=True)

# --- 1. セキュリティ（ログイン） ---
LOGIN_PASSWORD = "HR9237" 

def check_password():
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False
    if st.session_state.password_correct: return True

    st.title("🔐 システムログイン")
    pwd = st.text_input("アクセスコードを入力してください", type="password")
    if st.button("ログイン", type="primary"):
        if pwd == LOGIN_PASSWORD:
            st.session_state.password_correct = True
            st.rerun()
        else:
            st.error("アクセスコードが正しくありません")
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
                content += f"[PDF読み込みエラー: {f.name}]\n"
    return content

# --- 2. AIクライアント設定 ---
# Gemini 2.5 Flashはコスト効率が良く、価格とパフォーマンスのバランスが最適化されています
# また、思考機能を搭載しているため、精度の高い分析が可能です
client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
st.set_page_config(page_title="AIエージェントシステム", page_icon="🤖", layout="wide")

# ==========================================
# 🎛️ メインメニュー
# ==========================================
with st.sidebar:
    st.markdown("### 🎛️ メインメニュー")
    app_mode = st.radio("使用するツールを選択してください", ["1. 求職者ランク判定", "2. 企業×求職者 マッチング分析"])
    st.divider()

# ==========================================
# 画面A：求職者ランク判定
# ==========================================
if app_mode == "1. 求職者ランク判定":
    st.title("📈 求職者ランク判定プロ")
    mode = st.radio("分析モードを選択してください", ["1. 簡易分析", "2. 通常分析（実績AI判定あり）", "3. 詳細分析（資料添付あり）"], horizontal=True)

    with st.sidebar:
        st.header("👤 基本情報入力")
        age = st.number_input("年齢", 18, 65, 25, key="rank_age")
        job_changes = st.number_input("転職回数", 0, 15, 1)
        short_term = st.number_input("短期離職数", 0, 10, 0)
        
        st.header("🏢 志望企業情報")
        target_industry = st.text_input("志望業種", value="", placeholder="例：IT・Web業界、製造業")
        target_job = st.text_input("志望職種", value="", placeholder="例：エンジニア、営業、経理")

    achievement_text, uploaded_files = "", []
    if mode == "2. 通常分析（実績AI判定あり）":
        achievement_text = st.text_area("職務経歴・実績", height=150)
    elif mode == "3. 詳細分析（資料添付あり）":
        achievement_text = st.text_area("追加の実績・補足事項（任意）", height=100)
        uploaded_files = st.file_uploader("資料を添付 (PDF/TXT)", accept_multiple_files=True, type=['txt', 'pdf'])

    if st.button("🔥 分析を開始する", type="primary"):
        with st.spinner("AIがデータをディープスキャン中..."):
            try:
                safe_ind = target_industry if target_industry else "全業種"
                safe_job = target_job if target_job else "職種全般"
                ai_score, reason_text, advice_text = 5, "簡易分析のためフィードバックなし", "詳細アドバイスは通常分析以上をご利用ください"
                
                if mode != "1. 簡易分析":
                    file_contents = read_files(uploaded_files)
                    prompt = f"""あなたはプロの厳格なキャリアアドバイザーです。【{safe_ind}】の【{safe_job}】志望者の市場価値を10点満点で採点してください。
【点数】(0〜10の数字のみ)
【評価理由】(具体的理由)
【改善アドバイス】(面接や書類の具体的な改善点)
---
実績：{achievement_text}\n資料内容：{file_contents}"""
                    response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
                    full_text = response.text
                    score_match = re.search(r'【点数】\s*(\d+)', full_text)
                    ai_score = int(score_match.group(1)) if score_match else ai_score
                    if "【評価理由】" in full_text and "【改善アドバイス】" in full_text:
                        reason_text = full_text.split("【評価理由】")[1].split("【改善アドバイス】")[0].strip()
                        advice_text = full_text.split("【改善アドバイス】")[1].strip()

                total_score = (5 if 22<=age<=35 else 0) + (5 if job_changes<=2 else 0) + ai_score - (short_term * 4)

                if total_score >= 18: r, cn, rc = "S", "優秀 (Class-S)", "#00ff00"
                elif total_score >= 15: r, cn, rc = "A", "良好 (Class-A)", "#00e5ff"
                elif total_score >= 12: r, cn, rc = "B", "標準 (Class-B)", "#ffff00"
                elif total_score >= 9: r, cn, rc = "C", "要努力 (Class-C)", "#ff9900"
                elif total_score >= 5: r, cn, rc = "D", "厳しい (Class-D)", "#ff0000"
                else: r, cn, rc = "Z", "測定不能 (Error)", "#888888"

                # --- 閃光＆トースト演出（確実発動版） ---
                st.toast("✅ スキャン完了：高精度レポートを生成しました", icon="🚀")
                flash_id = str(time.time())
                st.markdown(f"""
                    <div id="f-{flash_id}" style="position:fixed; top:0; left:0; width:100vw; height:100vh; background-color:rgba(0,229,255,0.5); z-index:9999; pointer-events:none; animation:flash-fade 0.7s ease-out forwards;"></div>
                """, unsafe_allow_html=True)

                st.markdown(f"""
                <div style="background-color: rgba(0, 229, 255, 0.2); padding: 10px; border-radius: 5px; border-left: 5px solid #00E5FF;">
                    ✨ <b>Analysis Complete:</b> 【{safe_ind} / {safe_job}】専門AIによるスキャンが完了しました。
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown('<div class="cyber-panel scan-effect">', unsafe_allow_html=True)
                st.markdown("## 📊 AI キャリア分析レポート")
                st.markdown(f"<div style='display:flex; align-items:center;'><div style='width:22px; height:22px; border-radius:50%; background:{rc}; box-shadow:0 0 20px {rc}; margin-right:15px;'></div><h3 style='color:{rc}; text-shadow:0 0 15px {rc}; margin:0;'>総合評価: {cn}</h3></div>", unsafe_allow_html=True)
                st.progress(max(0, min(total_score / 20, 1.0)))
                
                c1, c2, c3 = st.columns(3)
                c1.metric("👤 基本情報", f"{(5 if 22<=age<=35 else 0) + (5 if job_changes<=2 else 0)} pt")
                c2.metric("🤖 AI 実績", f"{ai_score} pt")
                c3.metric("⚠️ リスク", f"-{short_term * 4} pt", delta_color="inverse")
                st.divider()
                st.markdown("#### 📝 AI 評価理由")
                st.markdown(f'<div class="fb-box">{reason_text}</div>', unsafe_allow_html=True)
                st.markdown("#### 💡 改善アドバイス")
                st.markdown(f'<div class="fb-box" style="border-left-color:#00ff00;">{advice_text}</div>', unsafe_allow_html=True)
                
                report = f"REPORT: {cn}\nSCORE: {total_score}/20\nREASON: {reason_text}\nADVICE: {advice_text}"
                st.download_button("📥 レポートをダウンロード (TXT)", report, f"report_{r}.txt")
                st.markdown("</div>", unsafe_allow_html=True)

            except Exception as e: st.error(f"❌ 解析エラー: {e}")

# ==========================================
# 画面B：マッチング分析
# ==========================================
elif app_mode == "2. 企業×求職者 マッチング分析":
    st.title("🤝 企業×求職者 マッチング分析")
    m_mode = st.radio("分析モードを選択してください", ["1. 簡易マッチング（基本情報・経験のみ）", "2. 詳細マッチング（資料・詳細テキストあり）"], horizontal=True)

    if m_mode == "1. 簡易マッチング（基本情報・経験のみ）":
        with st.sidebar:
            st.header("👤 求職者情報")
            m_age = st.number_input("年齢", 18, 65, 25, key="m_age")
            m_ind = st.text_input("志望業種", value="", placeholder="例：SaaS、人材", key="m_ind")
            m_ei = st.radio("業種経験", ["あり", "なし"], index=1, horizontal=True)
            m_job = st.text_input("志望職種", value="", placeholder="例：法人営業", key="m_job")
            m_ej = st.radio("職種経験", ["あり", "なし"], index=1, horizontal=True)

    elif m_mode == "2. 詳細マッチング（資料・詳細テキストあり）":
        st.info("💡 企業・求職者それぞれの情報（文章入力、またはファイルの添付）を行ってください。")
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("🏢 企業側の情報")
            c_text = st.text_area("募集要項・求める人物像", height=150)
            c_files = st.file_uploader("企業資料を添付", accept_multiple_files=True, type=['txt', 'pdf'], key="cf")
        with col2:
            st.subheader("👤 求職者側の情報")
            s_text = st.text_area("経歴・スキル・面談メモ", height=150)
            s_files = st.file_uploader("履歴書などを添付", accept_multiple_files=True, type=['txt', 'pdf'], key="sf")

    if st.button("✨ マッチング分析を実行", type="primary"):
        with st.spinner("AIが相性を解析中..."):
            try:
                if m_mode == "1. 簡易マッチング（基本情報・経験のみ）":
                    prompt = f"ヘッドハンターとして、{m_age}歳、志望業種:{m_ind}(経験:{m_ei})、志望職種:{m_job}(経験:{m_ej})の内定可能性を100点満点で判定して。【マッチ度】(数字のみ)【評価理由】【面接突破戦略】の形式で答えて。"
                else:
                    cfc, sfc = read_files(c_files), read_files(s_files)
                    prompt = f"企業要件：{c_text}\n{cfc}\n求職者情報：{s_text}\n{sfc}\nを比較し相性を100点満点で判定して。【マッチ度】(数字のみ)【評価理由】【面接突破戦略】の形式で答えて。"
                
                response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
                full_text = response.text
                ms = int(re.search(r'【マッチ度】\s*(\d+)', full_text).group(1)) if re.search(r'【マッチ度】\s*(\d+)', full_text) else 50
                reason = full_text.split("【評価理由】")[1].split("【面接突破戦略】")[0].strip() if "【評価理由】" in full_text else full_text
                strategy = full_text.split("【面接突破戦略】")[1].strip() if "【面接突破戦略】" in full_text else ""

                if ms >= 90: r, cn, rc = "S", "運命の出会い (90%+)", "#00ff00"
                elif ms >= 75: r, cn, rc = "A", "高確率で内定 (75%+)", "#00e5ff"
                elif ms >= 60: r, cn, rc = "B", "選考通過ライン (60%+)", "#ffff00"
                elif ms >= 40: r, cn, rc = "C", "懸念あり (40%+)", "#ff9900"
                else: r, cn, rc = "D", "ミスマッチの可能性大 (39%-)", "#ff0000"

                # --- 閃光＆トースト演出（確実発動版） ---
                st.toast("✅ 解析完了：最適な戦略を算出しました", icon="🎯")
                flash_id = str(time.time())
                st.markdown(f"""
                    <div id="f-{flash_id}" style="position:fixed; top:0; left:0; width:100vw; height:100vh; background-color:rgba(0,229,255,0.5); z-index:9999; pointer-events:none; animation:flash-fade 0.7s ease-out forwards;"></div>
                """, unsafe_allow_html=True)

                st.markdown('<div class="cyber-panel scan-effect">', unsafe_allow_html=True)
                st.markdown("## 🎯 AI マッチング解析レポート")
                st.markdown(f"<div style='display:flex; align-items:center;'><div style='width:22px; height:22px; border-radius:50%; background:{rc}; box-shadow:0 0 20px {rc}; margin-right:15px;'></div><h3 style='color:{rc}; text-shadow:0 0 15px {rc}; margin:0;'>判定: {cn}</h3></div>", unsafe_allow_html=True)
                st.progress(max(0, min(ms / 100, 1.0)))
                st.divider()
                st.markdown("#### ⚖️ マッチング評価理由")
                st.markdown(f'<div class="fb-box">{reason}</div>', unsafe_allow_html=True)
                st.markdown("#### ⚔️ 面接突破・書類修正アドバイス")
                st.markdown(f'<div class="fb-box" style="border-left-color:#00ff00;">{strategy}</div>', unsafe_allow_html=True)
                if ms >= 75: st.success("🔥 **【エージェント向け】** 優先度：高！すぐ推薦しましょう！")
                elif ms < 50: st.error("🚨 **【エージェント向け】** 優先度：低。慎重なフォローが必要です。")
                st.markdown("</div>", unsafe_allow_html=True)
            except Exception as e: st.error(f"❌ 解析エラー: {e}")


