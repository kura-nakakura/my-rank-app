import streamlit as st
from google import genai
import re

# ==========================================
# 🎨 カスタムCSS（サイバーデザイン＆LEDランプ）
# ==========================================
st.markdown("""
<style>
    .stApp {
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
    @keyframes scan {
        0% { top: -150%; }
        100% { top: 150%; }
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

    st.title(":lock: システムログイン")
    pwd = st.text_input("アクセスコードを入力してください", type="password")
    if st.button("認証", type="primary"):
        if pwd == LOGIN_PASSWORD:
            st.session_state.password_correct = True
            st.rerun()
        else:
            st.error("アクセスコードが拒否されました")
    return False

if not check_password(): st.stop()

# --- 2. AIクライアント設定 ---
client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
st.set_page_config(page_title="AIエージェントシステム", page_icon="🤖", layout="wide")

# ==========================================
# 🎛️ メインメニュー（画面切り替え）
# ==========================================
with st.sidebar:
    st.markdown("### 🎛️ メインメニュー")
    app_mode = st.radio(
        "使用するツールを選択してください",
        ["1. 求職者ランク判定", "2. 企業×求職者 マッチング分析"]
    )
    st.divider()

# ==========================================
# 画面A：求職者ランク判定（既存機能）
# ==========================================
if app_mode == "1. 求職者ランク判定":
    st.title(":chart_with_upwards_trend: 求職者ランク判定プロ")
    
    mode = st.radio("分析モード", ["1. 簡易分析", "2. 通常分析（実績AI判定あり）", "3. 詳細分析（資料添付あり）"], horizontal=True)

    with st.sidebar:
        st.header(":bust_in_silhouette: 基本情報入力")
        age = st.number_input("年齢", 18, 65, 25, key="rank_age")
        job_changes = st.number_input("転職回数", 0, 15, 1)
        short_term = st.number_input("短期離職数", 0, 10, 0)
        
        st.header(":office: 志望企業情報")
        target_industry = st.text_input("志望業種", value="IT/Web業界")
        target_job = st.text_input("志望職種", value="職種全般")

    achievement_text = ""
    uploaded_files = []

    if mode == "2. 通常分析（実績AI判定あり）":
        achievement_text = st.text_area("職務経歴・実績", height=150)
    elif mode == "3. 詳細分析（資料添付あり）":
        achievement_text = st.text_area("追加の実績・補足事項（任意）", height=100)
        uploaded_files = st.file_uploader("資料を添付", accept_multiple_files=True, type=['txt'])

    if st.button("分析を開始する", type="primary"):
        with st.spinner("AIがデータをディープスキャン中..."):
            try:
                ai_score = 5  
                reason_text = "簡易分析のためフィードバックなし"
                advice_text = "詳細アドバイスは通常分析以上をご利用ください"
                
                if mode != "1. 簡易分析":
                    file_contents = "".join([f.getvalue().decode("utf-8") + "\n" for f in uploaded_files if f.name.endswith('.txt')]) if uploaded_files else ""
                    
                    prompt = f"""プロのキャリアアドバイザーとして、【{target_industry}】の【{target_job}】志望者の市場価値を10点満点で厳しく採点してください。
【点数】(0〜10の数字のみ)
【評価理由】(業界プロ目線での具体的な理由)
【改善アドバイス】(面接や書類の具体的な改善点)
---
実績：{achievement_text}
資料内容：{file_contents}"""
                    
                    response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
                    full_text = response.text
                    
                    if re.search(r'【点数】\s*(\d+)', full_text): ai_score = int(re.search(r'【点数】\s*(\d+)', full_text).group(1))
                    elif re.search(r'\d+', full_text): ai_score = int(re.search(r'\d+', full_text).group())

                    if "【評価理由】" in full_text and "【改善アドバイス】" in full_text:
                        reason_text = full_text.split("【評価理由】")[1].split("【改善アドバイス】")[0].strip()
                        advice_text = full_text.split("【改善アドバイス】")[1].strip()
                    else:
                        reason_text = full_text

                total_score = (5 if 22<=age<=35 else 0) + (5 if job_changes<=2 else 0) + ai_score - (short_term * 4)

                if total_score >= 18: rank, color_name, rank_color = "S", "優秀 (Class-S)", "#00ff00"
                elif total_score >= 15: rank, color_name, rank_color = "A", "良好 (Class-A)", "#00e5ff"
                elif total_score >= 12: rank, color_name, rank_color = "B", "標準 (Class-B)", "#ffff00"
                elif total_score >= 9: rank, color_name, rank_color = "C", "要努力 (Class-C)", "#ff9900"
                elif total_score >= 5: rank, color_name, rank_color = "D", "厳しい (Class-D)", "#ff0000"
                else: rank, color_name, rank_color = "Z", "測定不能 (Error)", "#888888"

                st.markdown('<div class="cyber-panel scan-effect">', unsafe_allow_html=True)
                st.markdown("## 📊 AI キャリア分析レポート")
                st.markdown(f"""
                <div style='display: flex; align-items: center; margin-bottom: 15px;'>
                    <div style='width: 22px; height: 22px; border-radius: 50%; background-color: {rank_color}; box-shadow: 0 0 20px {rank_color}, inset 0 0 8px rgba(255,255,255,0.6); margin-right: 15px;'></div>
                    <h3 style='color: {rank_color}; text-shadow: 0 0 15px {rank_color}; margin: 0;'>総合評価: {color_name}</h3>
                </div>
                """, unsafe_allow_html=True)
                st.progress(max(0, min(total_score / 20, 1.0)))
                
                col1, col2, col3 = st.columns(3)
                col1.metric("👤 基本情報", f"{(5 if 22<=age<=35 else 0) + (5 if job_changes<=2 else 0)} pt")
                col2.metric("🤖 AI 実績", f"{ai_score} pt")
                col3.metric("⚠️ リスク", f"-{short_term * 4} pt", delta_color="inverse")
                st.divider()
                st.markdown("#### 📝 AI 評価理由")
                st.markdown(f'<div class="fb-box">{reason_text}</div>', unsafe_allow_html=True)
                st.markdown("#### 💡 改善アドバイス")
                st.markdown(f'<div class="fb-box" style="border-left-color:#00ff00;">{advice_text}</div>', unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

            except Exception as e:
                st.error(f"❌ エラーが発生しました: {e}")

# ==========================================
# 画面B：企業×求職者 マッチング分析（新機能）
# ==========================================
elif app_mode == "2. 企業×求職者 マッチング分析":
    st.title("🤝 企業×求職者 マッチング分析")
    
    # ★追加：マッチング機能内の2つのモード切り替え
    match_mode = st.radio(
        "分析モードを選択してください",
        ["1. 簡易マッチング（基本情報・経験のみ）", "2. 詳細マッチング（資料・詳細テキストあり）"],
        horizontal=True
    )
    st.markdown("---")

    # 変数の初期化
    m_age = 25
    m_target_industry = ""
    m_target_job = ""
    m_exp_industry = "なし"
    m_exp_job = "なし"
    company_text = ""
    company_files = []
    seeker_text = ""
    seeker_files = []

    # --- モード別のUI表示 ---
    if match_mode == "1. 簡易マッチング（基本情報・経験のみ）":
        st.markdown("#### 👤 求職者の基本情報と経験")
        col1, col2, col3 = st.columns(3)
        with col1:
            m_age = st.number_input("年齢", 18, 65, 25, key="match_age")
        with col2:
            m_target_industry = st.text_input("志望業種", value="IT/Web業界", key="match_ind")
            m_exp_industry = st.radio("業種経験", ["あり", "なし"], index=1, horizontal=True)
        with col3:
            m_target_job = st.text_input("志望職種", value="エンジニア", key="match_job")
            m_exp_job = st.radio("職種経験", ["あり", "なし"], index=1, horizontal=True)

    elif match_mode == "2. 詳細マッチング（資料・詳細テキストあり）":
        st.info("💡 企業・求職者それぞれの情報（文章入力、またはテキストファイルの添付）を行ってください。両方組み合わせることも可能です。")
        col_corp, col_seeker = st.columns(2)
        with col_corp:
            st.subheader("🏢 企業側の情報")
            company_text = st.text_area("募集要項・求める人物像（文章入力）", height=150)
            company_files = st.file_uploader("企業資料を添付（複数可・txt形式）", accept_multiple_files=True, type=['txt'], key="c_files")
        with col_seeker:
            st.subheader("👤 求職者側の情報")
            seeker_text = st.text_area("経歴・スキル・面談メモ（文章入力）", height=150)
            seeker_files = st.file_uploader("履歴書・職務経歴書・面談文字起こし（複数可・txt形式）", accept_multiple_files=True, type=['txt'], key="s_files")

    if st.button("マッチング分析を実行", type="primary"):
        with st.spinner("AIがカルチャーフィットとスキルギャップを解析中..."):
            try:
                # --- モード別のAIプロンプト生成 ---
                if match_mode == "1. 簡易マッチング（基本情報・経験のみ）":
                    match_prompt = f"""あなたは凄腕のヘッドハンターです。
以下の求職者の基本情報をもとに、一般的な市場における【{m_target_industry}】の【{m_target_job}】へのマッチング度（相性・内定獲得の可能性）を100点満点で推測・判定してください。

【求職者情報】
・年齢: {m_age}歳
・志望業種: {m_target_industry} （経験: {m_exp_industry}）
・志望職種: {m_target_job} （経験: {m_exp_job}）

必ず以下のフォーマットで出力してください。

【マッチ度】
(0〜100の数字のみ)

【評価理由】
(年齢や経験の有無から推測される、この業界・職種への転職ハードルやポテンシャルの評価)

【面接突破戦略】
(未経験の場合はどうポテンシャルをアピールすべきか、経験者の場合はどう即戦力性を伝えるべきかの簡単なアドバイス)
"""
                else: # 詳細マッチング
                    c_file_content = "".join([f.getvalue().decode("utf-8") + "\n" for f in company_files]) if company_files else ""
                    s_file_content = "".join([f.getvalue().decode("utf-8") + "\n" for f in seeker_files]) if seeker_files else ""
                    
                    match_prompt = f"""あなたは凄腕のヘッドハンターです。以下の【企業の要件】と【求職者の情報】を深く比較し、マッチング度（相性）を100点満点で判定してください。
必ず以下のフォーマットで出力してください。

【マッチ度】
(0〜100の数字のみ)

【評価理由】
(なぜそのマッチ度なのか。スキル要件の合致度、カルチャーフィット、懸念点などを具体的に)

【面接突破戦略】
(この求職者が面接を通過するためには、履歴書・職務経歴書のどこを修正すべきか、どの経験をアピールし、どの弱点をどうカバーすべきかの具体的な対策)

---
【企業の要件（テキスト）】
{company_text}
【企業の要件（資料）】
{c_file_content}

【求職者の情報（テキスト）】
{seeker_text}
【求職者の情報（資料）】
{s_file_content}
"""

                # AIへのリクエスト送信
                response = client.models.generate_content(model='gemini-2.5-flash', contents=match_prompt)
                full_text = response.text
                
                match_score = 50
                reason_text = ""
                strategy_text = ""

                if re.search(r'【マッチ度】\s*(\d+)', full_text):
                    match_score = int(re.search(r'【マッチ度】\s*(\d+)', full_text).group(1))
                
                if "【評価理由】" in full_text and "【面接突破戦略】" in full_text:
                    reason_text = full_text.split("【評価理由】")[1].split("【面接突破戦略】")[0].strip()
                    strategy_text = full_text.split("【面接突破戦略】")[1].strip()

                # マッチング度のランク分け
                if match_score >= 90: rank, color_name, rank_color = "S", "運命の出会い (Match 90%+)", "#00ff00"
                elif match_score >= 75: rank, color_name, rank_color = "A", "高確率で内定 (Match 75%+)", "#00e5ff"
                elif match_score >= 60: rank, color_name, rank_color = "B", "選考通過ライン (Match 60%+)", "#ffff00"
                elif match_score >= 40: rank, color_name, rank_color = "C", "懸念あり (Match 40%+)", "#ff9900"
                else: rank, color_name, rank_color = "D", "ミスマッチの可能性大 (Match 39%-)", "#ff0000"

                # 🎨 画面への描画
                st.markdown('<div class="cyber-panel scan-effect">', unsafe_allow_html=True)
                st.markdown("## 🎯 AI マッチング解析レポート")
                
                st.markdown(f"""
                <div style='display: flex; align-items: center; margin-bottom: 15px;'>
                    <div style='width: 22px; height: 22px; border-radius: 50%; background-color: {rank_color}; box-shadow: 0 0 20px {rank_color}, inset 0 0 8px rgba(255,255,255,0.6); margin-right: 15px;'></div>
                    <h3 style='color: {rank_color}; text-shadow: 0 0 15px {rank_color}; margin: 0;'>判定: {color_name}</h3>
                </div>
                """, unsafe_allow_html=True)
                st.progress(max(0, min(match_score / 100, 1.0)))
                st.caption(f"AI算出マッチングスコア: {match_score}点 / 100点")
                
                st.divider()
                st.markdown("#### ⚖️ マッチング評価理由")
                st.markdown(f'<div class="fb-box">{reason_text}</div>', unsafe_allow_html=True)
                st.markdown("#### ⚔️ 面接突破・書類修正アドバイス")
                st.markdown(f'<div class="fb-box" style="border-left-color:#00ff00;">{strategy_text}</div>', unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

                # エージェント向けアラート
                if match_score >= 75:
                    st.success("🔥 **【エージェント指示】** 非常に高いマッチ度です！すぐに推薦状を作成し、面接対策のスケジュールを組んでください。")
                elif match_score < 50:
                    st.error("🚨 **【エージェント指示】** ミスマッチの可能性が高いです。推薦する場合は、企業側に事前のフォローを入れるか、別案件の打診を検討してください。")

            except Exception as e:
                st.error(f"❌ 解析中にエラーが発生しました: {e}")


