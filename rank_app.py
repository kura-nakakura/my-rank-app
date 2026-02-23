import streamlit as st
from google import genai
import re
from pypdf import PdfReader
import time

# ==========================================
# 🎨 デザイン定義（サイバー×エネルギッシュ）
# ==========================================
st.set_page_config(page_title="AIエージェントシステム", page_icon="🤖", layout="wide")

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
    padding: 25px; margin-top: 20px;
    backdrop-filter: blur(5px); position: relative; overflow: hidden;
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

# --- 1. セキュリティ設定 ---
LOGIN_PASSWORD = "HR9237"

def check_password():
    if "password_correct" not in st.session_state: st.session_state.password_correct = False
    if st.session_state.password_correct: return True
    st.title("🛡️ システムログイン")
    pwd = st.text_input("アクセスコードを入力してください", type="password")
    if st.button("ログイン", type="primary"):
        if pwd == LOGIN_PASSWORD:
            st.session_state.password_correct = True
            st.rerun()
        else: st.error("アクセスコードが正しくありません")
    return False

if not check_password(): st.stop()

# --- 共通関数 ---
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

def get_section(name, text):
    if not text: return ""
    pattern = f"【{name}】\n?(.*?)(?=【|$)"
    match = re.search(pattern, text, re.DOTALL)
    return match.group(1).strip() if match else f"{name}の抽出に失敗しました。"

# --- AIクライアント設定 ---
client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

# ==========================================
# 🎛️ メインメニュー
# ==========================================
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/artificial-intelligence.png", width=80)
    st.markdown("### 🎛️ 運用フェーズ")
    app_mode = st.radio("現在のステップを選択", [
        "1. 応募時 (簡易ランク付け)", 
        "2. 初回面談後 (詳細分析/書類作成)", 
        "3. 書類作成後 (マッチ度/推薦文)"
    ])
    st.divider()
    st.header("アドバイザー情報")
    my_name = st.text_input("アドバイザー氏名", placeholder="例：山田 太郎")
    if not my_name:
        st.warning("推薦文作成のため氏名を入力してください")

# ==========================================
# Phase 1: 応募時 (簡易ランク付け)
# ==========================================
if app_mode == "1. 応募時 (簡易ランク付け)":
    st.title("Phase 1: 応募時 (簡易ランク付け)")
    st.markdown("応募情報を入力して、対応の優先度を判定します。")
    
    with st.container():
        col1, col2, col3 = st.columns(3)
        with col1: age = st.number_input("年齢", 18, 65, 25)
        with col2: job_changes = st.number_input("転職回数", 0, 15, 1)
        with col3: short_term = st.number_input("短期離職数", 0, 10, 0)
    
    if st.button("ランクを判定する", type="primary"):
        # 年齢スコア
        if age < 20: age_s = -8
        elif 20 <= age <= 21: age_s = 8
        elif 22 <= age <= 25: age_s = 10
        elif 26 <= age <= 29: age_s = 8
        elif 30 <= age <= 35: age_s = 7
        else: age_s = 5

        # 転職回数評価
        job_bonus = 0
        if age <= 24 and job_changes == 0: job_bonus = 10
        elif 25 <= age <= 29 and job_changes <= 1: job_bonus = 10
        elif 30 <= age <= 35 and job_changes <= 2: job_bonus = 10
        elif job_changes <= 1: job_bonus = 5

        # ペナルティ判定
        job_penalty = 0
        if job_changes == 2: job_penalty = -5
        elif job_changes == 3: job_penalty = -10
        elif job_changes >= 5: job_penalty = -20
        
        st_penalty = short_term * 10
        total_score = age_s + job_bonus + job_penalty - st_penalty + 5 # 補正値

        if total_score >= 23: cn, rc = "優秀 (Class-S)", "#00ff00"
        elif total_score >= 18: cn, rc = "良好 (Class-A)", "#00e5ff"
        elif total_score >= 13: cn, rc = "標準 (Class-B)", "#ffff00"
        elif total_score >= 8: cn, rc = "要努力 (Class-C)", "#ff9900"
        else: cn, rc = "測定不能 (Class-Z)", "#ff0000"

        st.markdown(f"""
        <div class="cyber-panel scan-effect">
            <h3 style="margin-top:0;">初期ランク: <span style="color:{rc};">{cn}</span></h3>
            <p>年齢pt: {age_s} / 経歴pt: {job_bonus} / 減点: {job_penalty - st_penalty}</p>
        </div>
        """, unsafe_allow_html=True)
        
        if total_score >= 15: st.success("✅ **優先度：高** 即面談を打診してください。")
        else: st.info("ℹ️ **優先度：中〜低** 書類を精査し、面談での確認事項を整理しましょう。")

# ==========================================
# Phase 2: 初回面談後 (詳細分析/書類作成)
# ==========================================
elif app_mode == "2. 初回面談後 (詳細分析/書類作成)":
    st.title("Phase 2: 初回面談後 (詳細分析/書類作成)")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📋 基本入力")
        t_industry = st.text_input("志望業種")
        t_job = st.text_input("志望職種")
        interview_notes = st.text_area("面談メモ・実績", height=150, placeholder="面談で聞いた実績、強み、人柄など")
    with col2:
        st.subheader("📂 書類添付")
        u_files = st.file_uploader("既存の履歴書・職務経歴書 (PDF/TXT)", accept_multiple_files=True)

    if st.button("AI書類生成を開始", type="primary"):
        with st.spinner("プロフェッショナルな書類を作成中..."):
            file_data = read_files(u_files)
            prompt = f"""
            あなたは人材紹介会社のプロキャリアライター兼採用目線の職務経歴書編集者です。
            以下の情報を元に、高品質な職務経歴書、自己PR、志望動機を作成してください。

            【入力情報】
            志望業種：{t_industry} / 職種：{t_job}
            面談実績：{interview_notes}
            資料内容：{file_data}

            ---
            ▼出力フォーマット
            【評価スコア】
            (0〜10の数字)
            【評価の理由】
            (理由を簡潔に)
            【エージェントへのアドバイス】
            (書類作成や推薦で見抜くべき視点)

            【職務経歴書】
            ■構成：作成日・氏名、職務経歴（会社名/雇用形態/事業内容/役職/業務内容/成果）、自己PR(400字)。
            ■ルール：「業務内容/成果」は常体、「自己PR」は敬体。具体的な数値・改善実績を盛り込む。AI特有の記号「」””・は使用しない。

            【志望動機】
            (企業に合わせた内容で450字程度。敬体。事実ベースで、嘘や推測は避ける。AI特有の記号は使用しない。)
            """
            try:
                resp = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
                res_text = resp.text
                
                st.markdown(f"### AIスコア: {get_section('評価スコア', res_text)} / 10")
                st.info(f"**アドバイス:** {get_section('エージェントへのアドバイス', res_text)}")
                
                st.divider()
                st.subheader("📄 生成書類")
                st.caption("職務経歴書")
                st.code(get_section('職務経歴書', res_text), language="text")
                st.caption("志望動機")
                st.code(get_section('志望動機', res_text), language="text")
            except Exception as e:
                st.error(f"エラー: {e}")

# ==========================================
# Phase 3: 書類作成後 (マッチ度/推薦文)
# ==========================================
elif app_mode == "3. 書類作成後 (マッチ度/推薦文)":
    st.title("Phase 3: 書類作成後 (マッチ度/推薦文)")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🏢 企業側")
        comp_info = st.text_area("企業名・求人要件・社風", height=150)
        c_files = st.file_uploader("求人票など", accept_multiple_files=True, key="c3")
    with col2:
        st.subheader("👤 求職者側")
        cand_notes = st.text_area("補足事項 (例:退職理由の背景)", height=150)
        s_files = st.file_uploader("完成した職務経歴書など", accept_multiple_files=True, key="s3")

    if st.button("最終マッチ度審査を実行", type="primary"):
        if not my_name:
            st.error("サイドバーでアドバイザー氏名を入力してください。")
        else:
            with st.spinner("マッチング分析中..."):
                c_data = read_files(c_files)
                s_data = read_files(s_files)
                
                prompt = f"""
                凄腕ヘッドハンターとして、企業要件と求職者書類のマッチ度を審査し、最高の推薦文を作成してください。

                【情報】
                企業：{comp_info}\n{c_data}
                求職者：{cand_notes}\n{s_data}

                ---
                ▼出力フォーマット
                【マッチ度】
                (0〜100の数字のみ)

                【書類修正のアドバイス】
                (この企業向けにどこを直すべきか)

                【面接対策】
                (想定質問と回答方針)

                【推薦文】
                以下の構成を「必ず」守り、採用担当者が会いたくなるビジネスメールを作成してください。
                
                (企業名) 採用ご担当者様
                
                お世話になっております。キャリアアドバイザーの株式会社ライフアップの{my_name}です。
                この度、貴社の求人に非常にマッチする方をご紹介いたします。

                【推薦のポイント】
                ・(実績と要件の合致点を1文で)
                ・(スキルがどう貢献するかを1文で)
                ・(懸念点があれば払拭する内容を1文で。なければ省略)

                (人柄・熱意・ポテンシャルなど、エージェントが面談で感じた魅力を150字程度で記載。AI特有の「」””・は絶対に使わない。誠実なビジネス文体。)

                お忙しいところ恐縮ですが、ぜひ一度ご面接の機会をいただけますと幸いです。
                何卒よろしくお願い申し上げます。
                """
                
                try:
                    resp = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
                    res_m = resp.text
                    
                    ms = int(re.search(r'\d+', get_section('マッチ度', res_m)).group()) if re.search(r'\d+', get_section('マッチ度', res_m)) else 0
                    
                    st.markdown(f"""
                    <div class="cyber-panel">
                        <h3 style="margin-top:0;">最終マッチ判定: <span style="color:#00E5FF;">{ms} / 100</span></h3>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown(f"#### ✍️ 修正アドバイス\n{get_section('書類修正のアドバイス', res_m)}")
                    
                    if ms >= 80:
                        st.success("🔥 マッチ度80%以上！推薦状をコピーして企業へ送りましょう。")
                        st.subheader("📧 推薦メール案")
                        st.code(get_section('推薦文', res_m), language="text")
                    else:
                        st.warning("⚠️ マッチ度が基準値(80%)未満です。書類を修正して再送するか、別の検討を推奨します。")
                    
                    st.divider()
                    st.subheader("🗣️ 面接対策")
                    st.write(get_section('面接対策', res_m))
                    
                except Exception as e:
                    st.error(f"エラー: {e}")

# ==========================================
# 💡 フッター
# ==========================================
st.sidebar.caption(f"© 2024 株式会社ライフアップ - {my_name if my_name else 'Advisor'}")





















