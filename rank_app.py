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
# Gemini 2.5 Flashは価格とパフォーマンスのバランスが最適化されたモデルです
client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
st.set_page_config(page_title="AIエージェントシステム", page_icon="🤖", layout="wide")

# --- セクション抽出ヘルパー ---
def get_section(name, text):
    if not text: return ""
    pattern = f"【{name}】(.*?)(?=【|$)"
    match = re.search(pattern, text, re.DOTALL)
    return match.group(1).strip() if match else ""

# ==========================================
# 🎛️ メインメニュー
# ==========================================
with st.sidebar:
    st.markdown("### 🎛️ メインメニュー")
    app_mode = st.radio("使用するツールを選択してください", ["1. 求職者ランク判定", "2. 企業×求職者 マッチング分析"])
    st.divider()
    st.header("アドバイザー情報")
    my_name = st.text_input("あなたの氏名", placeholder="山田太郎")

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
        target_industry = st.text_input("志望業種", placeholder="例：IT・Web業界")
        target_job = st.text_input("志望職種", placeholder="例：エンジニア")

    achievement_text, uploaded_files = "", []
    if mode == "2. 通常分析":
        achievement_text = st.text_area("職務経歴・実績", height=150)
    elif mode == "3. 詳細分析（書類作成あり）":
        achievement_text = st.text_area("追加の実績・面談メモ", height=100)
        uploaded_files = st.file_uploader("資料を添付 (PDF/TXT)", accept_multiple_files=True, type=['txt', 'pdf'])

    if st.button("分析を開始する", type="primary"):
        with st.spinner("AI Engine スキャン中..."):
            try:
                safe_ind = target_industry if target_industry else "全業種"
                safe_job = target_job if target_job else "職種全般"
                ai_score, pr_text, motive_text, letter_text = 5, "", "", ""
                reason_disp = "簡易分析モードのため、AI評価は省略されています。"
                advice_disp = "詳細は「通常分析」以上をご利用ください。"

                if mode != "1. 簡易分析":
                    file_contents = read_files(uploaded_files)
                    prompt = f"""あなたはプロのキャリアアドバイザーです。
【{safe_ind}】の【{safe_job}】志望者を事実に基づき評価と企業様がお会いしたくなるような書類作成してください。ただし自己PR、志望動機、推薦文は「」や・””などAIのような文章はさけてください。

【点数】(0〜10の数字のみ)
【評価理由】
【改善アドバイス】
【自己PR例】(事実ベース400字程度)
【志望動機例】(事実ベース450字程度)
【推薦文】(メール形式。署名：株式会社ライフアップ {my_name})

---
実績：{achievement_text}\n資料：{file_contents}"""
                    response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
                    full = response.text
                    ai_score = int(re.search(r'【点数】\s*(\d+)', full).group(1)) if re.search(r'【点数】\s*(\d+)', full) else 5
                    reason_disp, advice_disp = get_section('評価理由', full), get_section('改善アドバイス', full)
                    pr_text, motive_text, letter_text = get_section('自己PR例', full), get_section('志望動機例', full), get_section('推薦文', full)

                # --- ライフアップ流・厳格スコアリング ---
                # 1. 年齢スコア
                if age < 20: age_s = -8
                elif 20 <= age <= 21: age_s = 8
                elif 22 <= age <= 25: age_s = 10
                elif 26 <= age <= 29: age_s = 8
                elif 30 <= age <= 35: age_s = 7
                else: age_s = 5

                # 2. 転職回数/短期離職ペナルティ
                job_bonus = 0
                if age <= 24 and job_changes == 0: job_bonus = 10
                elif 25 <= age <= 29 and job_changes <= 1: job_bonus = 10
                elif 25 <= age <= 29 and job_changes <= 2: job_bonus = 8
                elif 25 <= age <= 29 and job_changes <= 3: job_bonus = 5
                elif 30 <= age <= 35 and job_changes <= 2: job_bonus = 10
                elif 35 <= age <= 45 and job_changes <= 3: job_bonus = 10
                elif 45 <= age <= 60 and job_changes <= 5: job_bonus = 7
                elif job_changes <= 1: job_bonus = 5

                # ペナルティ合算
                job_penalty = 0
                if job_changes == 2: job_penalty = -5
                elif job_changes == 3: job_penalty = -10
                elif job_changes == 4: job_penalty = -12
                elif job_changes >= 5: job_penalty = -20
                
                # ★短期離職ペナルティ (1回につき-10点の重い判定)
                st_penalty = short_term * 10

                total_score = age_s + job_bonus + job_penalty - st_penalty + ai_score
                
                if total_score >= 23: cn, rc = "優秀 (Class-S)", "#00ff00"
                elif total_score >= 18: cn, rc = "良好 (Class-A)", "#00e5ff"
                elif total_score >= 13: cn, rc = "標準 (Class-B)", "#ffff00"
                elif total_score >= 8: cn, rc = "要努力 (Class-C)", "#ff9900"
                elif total_score >= 5: cn, rc = "厳しい (Class-D)", "#ff0000"
                else: cn, rc = "測定不能 (Class-Z)", "#ff0000"

                st.toast("スキャン完了：成功しました")
                flash_id = str(time.time())
                st.markdown(f'<div id="f-{flash_id}" style="position:fixed;top:0;left:0;width:100vw;height:100vh;background:rgba(0,229,255,0.4);z-index:9999;pointer-events:none;animation:flash-fade 0.7s forwards;"></div>', unsafe_allow_html=True)
                
                st.markdown(f"""
                <div class="cyber-panel scan-effect">
                    <h3 style="margin-top:0;">分析結果: <span style="color:{rc};">{cn}</span></h3>
                    <div style="background: rgba(255,255,255,0.1); border-radius: 5px; height: 10px; margin-bottom: 20px;">
                        <div style="background: {rc}; width: {min(100, total_score*5)}%; height: 100%; border-radius: 5px;"></div>
                    </div>
                    <div style="display: flex; justify-content: space-around; flex-wrap: wrap;">
                        <div style="text-align: center; min-width: 80px;"><small>年齢評価</small><br><b style="color:#00E5FF; font-size:1.5rem;">{age_s}pt</b></div>
                        <div style="text-align: center; min-width: 80px;"><small>経歴評価</small><br><b style="color:#00E5FF; font-size:1.5rem;">{job_bonus}pt</b></div>
                        <div style="text-align: center; min-width: 80px;"><small>回数/短期</small><br><b style="color:#FF4B4B; font-size:1.5rem;">{job_penalty - st_penalty}pt</b></div>
                        <div style="text-align: center; min-width: 80px;"><small>AI評価</small><br><b style="color:#00E5FF; font-size:1.5rem;">{ai_score}pt</b></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # ★追加：エージェント向け指示（ランク判定版）
                if total_score >= 15:
                    st.success("NICE **【エージェント指示】** 優先度：高　市場価値が高い人材です。早期の内定獲得を狙いましょう。")
                elif total_score < 14:
                    st.error("safe **【エージェント指示】** 優先度：中　あなたの腕の見せ所です。紹介企業や書類作成によって内定の可能性はあります。")
                elif total_score < 7:
                    st.error("🚨 **【エージェント指示】** 優先度：低　キャリア形成に課題があります。長期戦を覚悟するか、ターゲットの再考が必要です。")
                    
                st.divider()
                st.markdown(f"#### 📝 評価理由\n<div class='fb-box'>{reason_disp}</div>", unsafe_allow_html=True)
                st.markdown(f"#### 💡 アドバイス\n<div class='fb-box' style='border-left-color:#00ff00;'>{advice_disp}</div>", unsafe_allow_html=True)
                if mode == "3. 詳細分析（書類作成あり）":
                    st.subheader("📄 応募書類案 (コピー可)")
                    st.caption("自己PR (約400字)"); st.code(pr_text, language="text")
                    st.caption("志望動機 (約450字)"); st.code(motive_text, language="text")
                    st.caption("推薦メール"); st.code(letter_text, language="text")
                st.markdown("</div>", unsafe_allow_html=True)
            except Exception as e:
                # ★エラーガード：429エラーを日本語で表示
                if "429" in str(e): st.error("⚠️ 【利用制限】無料枠の上限に達しました（1日20回）。30秒ほど待つか、明日再度お試しください。")
                else: st.error(f"❌ 解析エラー: {e}")

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
            c_txt = st.text_area("企業要件", height=150)
            c_files = st.file_uploader("企業資料", accept_multiple_files=True, type=['txt', 'pdf'], key="cf")
        with col2:
            s_txt = st.text_area("求職者情報", height=150)
            s_files = st.file_uploader("求職者資料", accept_multiple_files=True, type=['txt', 'pdf'], key="sf")

    if st.button("マッチング分析を実行", type="primary"):
        with st.spinner("Analyzing..."):
            try:
                cfc, sfc = read_files(c_files), read_files(s_files)
                prompt = f"""凄腕ヘッドハンターとして相性を判定し、応募先企業が面接をしたくなるような推薦メールを作成してください。その際転職回数や短期離職など書類選考にマイナスな内容があれば払拭も事実を元にしてください署名：株式会社ライフアップ {my_name}
【マッチ度】(数字)\n【評価理由】\n【面接突破戦略】\n【推薦文】
---
{m_age if m_mode=="1. 簡易マッチング" else ""}\n企業：{c_txt}{cfc}\n求職者：{s_txt}{sfc}"""
                response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
                full_m = response.text
                ms = int(re.search(r'【マッチ度】\s*(\d+)', full_m).group(1)) if re.search(r'【マッチ度】\s*(\d+)', full_m) else 50
                st.toast("解析完了：成功しました")
                flash_id = str(time.time())
                st.markdown(f'<div id="f-{flash_id}" style="position:fixed;top:0;left:0;width:100vw;height:100vh;background:rgba(0,229,255,0.4);z-index:9999;pointer-events:none;animation:flash-fade 0.7s forwards;"></div>', unsafe_allow_html=True)
                st.markdown(f"""
                <div class="cyber-panel scan-effect">
                    <h3 style="margin-top:0;">マッチ判定: <span style="color:#00E5FF;">{ms}/100</span></h3>
                    <div style="background: rgba(255,255,255,0.1); border-radius: 5px; height: 10px; margin-bottom: 20px;">
                        <div style="background: #00E5FF; width: {ms}%; height: 100%; border-radius: 5px;"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                if ms >= 75:
                    st.success("🔥 **【エージェント指示】** 非常に高いマッチ度です！すぐに推薦状を作成し、面接対策のスケジュールを組んでください。")
                elif ms < 50:
                    st.error("🚨 **【エージェント指示】** 優先度：低（ミスマッチの可能性）。慎重なフォローが必要です。")

                st.markdown(f"**理由:** {get_section('評価理由', full_m)}")
                st.markdown(f"**戦略:** {get_section('面接突破戦略', full_m)}")
                if m_mode == "2. 詳細マッチング（推薦文あり）":
                    st.subheader("📧 推薦メール案"); st.code(get_section("推薦文", full_m), language="text")
                st.markdown("</div>", unsafe_allow_html=True)
            except Exception as e:
                # ★ここにもエラーガードを追加
                if "429" in str(e): st.error("⚠️ 【利用制限】上限に達しました。30秒ほど待ってから再試行してください。")
                else: st.error(f"❌ 解析エラー: {e}")

















