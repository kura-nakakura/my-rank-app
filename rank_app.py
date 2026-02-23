import streamlit as st
from google import genai
import re
from pypdf import PdfReader
import time
from docx import Document
from io import BytesIO

# ==========================================
# 🎨 デザイン定義（ラベルを白に、パネル崩れを修正）
# ==========================================
st.set_page_config(page_title="AIエージェントシステム PRO", page_icon="🤖", layout="wide")

st.markdown("""
<style>
.stApp {
    background-color: #0A192F;
    background-image: linear-gradient(rgba(10, 25, 47, 0.9), rgba(10, 25, 47, 0.9)),
    url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%2300e5ff' fill-opacity='0.05'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
}

/* 評価パネル全体のスタイル */
.cyber-panel {
    background: rgba(23, 42, 70, 0.7);
    border: 1px solid #00E5FF;
    box-shadow: 0 0 20px rgba(0, 229, 255, 0.4);
    border-radius: 10px; padding: 25px; margin-top: 20px;
    position: relative; overflow: hidden;
}

/* スキャンアニメーション */
.scan-line {
    position: absolute; top: -100%; left: -100%; width: 300%; height: 300%;
    background: linear-gradient(to bottom, transparent, rgba(0, 229, 255, 0.4) 50%, transparent);
    transform: rotate(45deg); animation: scan 2.5s ease-in-out forwards; pointer-events: none;
}
@keyframes scan { 0% { top: -150%; } 100% { top: 150%; } }
@keyframes flash-fade { 0% { opacity: 1; } 100% { opacity: 0; } }

.fb-box {
    background: rgba(255, 255, 255, 0.05);
    border-left: 4px solid #00E5FF;
    padding: 15px; margin-top: 10px;
}

/* 入力ラベルの文字色を白に変更 */
label p { color: #FFFFFF !important; font-weight: bold !important; font-size: 1rem !important;}
[data-testid="stMetricValue"] { color: #00E5FF !important; }
</style>
""", unsafe_allow_html=True)

# --- セキュリティ ---
LOGIN_PASSWORD = "HR9237"
if "password_correct" not in st.session_state: st.session_state.password_correct = False
if not st.session_state.password_correct:
    st.title("🛡️ システムログイン")
    pwd = st.text_input("アクセスコード", type="password")
    if st.button("ログイン"):
        if pwd == LOGIN_PASSWORD:
            st.session_state.password_correct = True
            st.rerun()
        else: st.error("コードが違います")
    st.stop()

# --- 関数群 ---
def read_files(files):
    content = ""
    for f in files:
        if f.name.endswith('.txt'): content += f.getvalue().decode("utf-8") + "\n"
        elif f.name.endswith('.pdf'):
            try:
                pdf = PdfReader(f)
                for page in pdf.pages: content += (page.extract_text() or "") + "\n"
            except: content += f"[Error: {f.name}]\n"
    return content

def get_section(name, text):
    pattern = f"【{name}】(.*?)(?=【|$)"
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else f"{name}の情報が生成されませんでした。プロンプトを再確認してください。"

def create_docx(history_text):
    doc = Document()
    doc.add_heading('職務経歴書', 0)
    for line in history_text.split('\n'):
        doc.add_paragraph(line)
    bio = BytesIO()
    doc.save(bio)
    return bio.getvalue()

client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

# ==========================================
# 🎛️ サイドバー
# ==========================================
with st.sidebar:
    st.title("AI AGENT MENU")
    app_mode = st.radio("フェーズ選択", [
        "1. 応募時 (ランク判定)", 
        "2. 初回面談後 (詳細分析/書類作成)", 
        "3. 書類作成後 (マッチ審査/推薦文)"
    ])
    st.divider()
    my_name = st.text_input("アドバイザー名", placeholder="山田 太郎")

# ==========================================
# Phase 1: 応募時 (ランク判定)
# ==========================================
if app_mode == "1. 応募時 (ランク判定)":
    st.title("Phase 1: 応募時簡易分析")
    col1, col2, col3 = st.columns(3)
    with col1: age = st.number_input("年齢", 18, 85, 25)
    with col2: job_changes = st.number_input("転職回数", 0, 15, 1)
    with col3: short_term = st.number_input("短期離職数", 0, 10, 0)
    
    if st.button("ランクを判定する", type="primary"):
        if age < 20: age_s = -8
        elif 20 <= age <= 21: age_s = 8
        elif 22 <= age <= 25: age_s = 10
        elif 26 <= age <= 29: age_s = 8
        elif 30 <= age <= 35: age_s = 7
        else: age_s = 5

        job_bonus = 0
        if age <= 24 and job_changes == 0: job_bonus = 10
        elif 25 <= age <= 29 and job_changes <= 1: job_bonus = 10
        elif 25 <= age <= 29 and job_changes <= 2: job_bonus = 7
        elif 30 <= age <= 35 and job_changes <= 2: job_bonus = 10
        elif 30 <= age <= 35 and job_changes <= 3: job_bonus = 7
        elif 35 <= age <= 85 and job_changes <= 2: job_bonus = 10
        elif 35 <= age <= 85 and job_changes <= 3: job_bonus = 7
        elif 50 <= age <= 85 and job_changes <= 4: job_bonus = 5
        elif job_changes <= 1: job_bonus = 5

        job_penalty = 0
        if job_changes == 2: job_penalty = -5
        elif job_changes == 3: job_penalty = -10
        elif job_changes >= 5: job_penalty = -20
        
        st_penalty = short_term * 10
        total = age_s + job_bonus + job_penalty - st_penalty + 5 

        if total >= 23: cn, rc = "優秀 (Class-S)", "#00ff00"
        elif total >= 18: cn, rc = "良好 (Class-A)", "#00e5ff"
        elif total >= 13: cn, rc = "標準 (Class-B)", "#ffff00"
        elif total >= 8: cn, rc = "要努力 (Class-C)", "#ff9900"
        else: cn, rc = "測定不能 (Class-Z)", "#ff0000"

        st.markdown(f'<div class="cyber-panel"><h3>判定結果: <span style="color:{rc};">{cn}</span></h3></div>', unsafe_allow_html=True)
        
        if total >= 15:
            st.success("NICE❕ **【エージェント指示】** 優先度：高　市場価値が高い人材です。早期の内定獲得を狙いましょう。")
        elif 7 <= total < 15:
            st.info("safe **【エージェント指示】** 優先度：中　あなたの腕の見せ所です。紹介企業や書類作成によって内定の可能性はあります。")
        else:
            st.error("🚨 **【エージェント指示】** 優先度：低　キャリア形成に課題があります。長期戦を覚悟するか、ターゲットの再考が必要です。")

# ==========================================
# Phase 2: 初回面談後 (詳細分析/書類作成)
# ==========================================
elif app_mode == "2. 初回面談後 (詳細分析/書類作成)":
    st.title("Phase 2: 詳細分析 & 高品質書類一括作成")
    
    c_top1, c_top2 = st.columns(2)
    with c_top1: t_ind = st.text_input("志望業種", placeholder="未入力の場合は添付資料から判断します")
    with c_top2: t_job = st.text_input("志望職種", placeholder="未入力の場合は添付資料から判断します")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🏢 企業・募集情報")
        u_files_corp = st.file_uploader("企業資料 (求人票など)", accept_multiple_files=True, key="corp_up")
        achievement = st.text_area("補足事項・実績", height=200, placeholder="ここに入力するか、資料を右側に添付してください")
        
    with col2:
        st.subheader("📂 求職者資料・文字起こし")
        u_files_seeker = st.file_uploader("履歴書・文字起こし", accept_multiple_files=True, key="seeker_up")
        st.info("💡 複数の資料からAIが深く分析します。")

    if st.button("AI書類生成を開始", type="primary"):
        corp_content = read_files(u_files_corp)
        seeker_content = read_files(u_files_seeker)
        
        if not (t_ind or corp_content):
            st.warning("志望業種を入力するか、企業資料を添付してください。")
        elif not (achievement or seeker_content):
            st.warning("実績を入力するか、求職者資料を添付してください。")
        else:
            with st.spinner("プロキャリアライターが詳細に執筆中..."):
                all_file_data = corp_content + "\n" + seeker_content
                
                # あなたの作成したプロンプトを完全に維持
                prompt = f"""
あなたは人材紹介会社の**プロキャリアライター兼採用目線の職務経歴書編集者**です。
求職者の職歴情報と応募企業情報をもとに、企業が「ぜひ会ってみたい」と思える具体的・誠実・読みやすい書類を作成してください。

【入力情報】
志望業種：{t_ind if t_ind else "未入力（資料から判断せよ）"} / 職種：{t_job if t_job else "未入力（資料から判断せよ）"}
実績・メモ：{achievement}
添付資料：{all_file_data}

---
以下の【】で囲まれた各セクションを、指示に従って「一切省略せずに」出力してください。

【評価】
(S最高/A良き！/Bいい感じ/C要努力/Z測定不能のみ)

【理由とアドバイス】
(評価の理由と、エージェントへの書類作成等で見抜くべき視点のアドバイスを記載)

【職務経歴】
**下記職務経歴書自動生成プロンプト出力ルール**に従って作成してください。
1. 作成日・氏名
2. 職務経歴（各社ごとに以下の構成を維持）
   【会社名】
   雇用形態：◯◯
   事業内容：◯◯
   役職：◯◯
   ▼業務内容
   ・主要業務を5〜7行で簡潔に。例：「売上管理」「顧客対応」「教育・運営」「営業活動」など動作中心で記載。
   ▼成果
   ・数値・改善・貢献を具体的に。
   ・抽象語を避け、「何を→どう行い→どうなったか」で構成。

【自己PR】
-応募企業に最適化された自己PR
- 応募企業の理念・社風・仕事内容に合わせ、これまでの経験をどう活かせるか。
- 「なぜこの会社に惹かれたのか」も含める。
- 400字で構成。事実を元にし、嘘や推測は含めない。
- 「」や””や・などAI文章だとわかる記号は控える。
- 文体は敬体（です・ます）。
- 一文は60文字以内で簡潔。
- 丁寧・誠実・安定感のある文体で統一。

🔹【出力フォーマット（例）】↓
職務経歴書
（作成日：◯年◯月◯日）
（氏名：◯◯ ◯◯）

---
■職務経歴
【会社名】
雇用形態：正社員
事業内容：〇〇
役職：〇〇

▼業務内容
・〇〇業務を担当し、〇〇を実施。
・〇〇を通じて〇〇に貢献。

▼成果
・〇〇を実現し、〇〇％改善。
・〇〇件の契約・販売を継続的に達成。
等、実際の情報を基に記載する
（以下同様に記載）
---
■自己PR

これまで〇〇業界で培った〇〇力・〇〇力を活かし、〇〇様が大切にされている〇〇の理念に共感しております。
特に〇〇経験では〇〇という成果を上げ、〇〇力を身につけました。
今後は〇〇として、〇〇の実現に貢献したいと考えています。
---

【志望動機】
- 企業にマイナスにならないのを前提に、年齢に合わせた文章・言葉使いにする。
- 約450字で作成。業務や実績は推測や嘘を避ける。
- 「」や””や・などは控える。
"""
                try:
                    resp = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
                    res = resp.text
                    
                    st.markdown(f'<div class="cyber-panel"><div class="scan-line"></div><h3>AI評価: {get_section("評価", res)}</h3><div class="fb-box">{get_section("理由とアドバイス", res)}</div></div>', unsafe_allow_html=True)
                    
                    hist = get_section('職務経歴', res)
                    st.divider()
                    st.subheader("📄 職務経歴（高品質版）")
                    st.code(hist, language="text")
                    
                    docx_file = create_docx(hist)
                    st.download_button(label="📥 職務経歴書をWordで保存", data=docx_file, file_name=f"職務経歴書_{time.strftime('%Y%m%d')}.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
                    
                    st.subheader("📄 自己PR（応募企業最適化）")
                    st.code(get_section('自己PR', res), language="text")
                    st.subheader("📄 志望動機")
                    st.code(get_section('志望動機', res), language="text")
                except Exception as e: st.error(f"解析エラー: {e}")

# ==========================================
# Phase 3: 書類作成後 (マッチ審査/推薦文)
# ==========================================
elif app_mode == "3. 書類作成後 (マッチ審査/推薦文)":
    st.title("Phase 3: 書類審査・マッチ度・推薦文")
    m_mode = st.radio("分析モード", ["1. 簡易マッチング", "2. 詳細マッチング（推薦文あり）"], horizontal=True)
    
    if m_mode == "1. 簡易マッチング":
        c1, c2 = st.columns(2)
        with c1: 
            m_age = st.number_input("年齢", 18, 85, 25, key="m_age_3")
            m_ind = st.text_input("応募業種", placeholder="例：IT・SaaS", key="m_ind_3")
            m_ind_exp = st.radio("業種経験", ["あり", "なし"], horizontal=True, key="m_ind_exp_3")
        with c2: 
            m_job = st.text_input("応募職種", placeholder="例：法人営業", key="m_job_3")
            m_job_exp = st.radio("職種経験", ["あり", "なし"], horizontal=True, key="m_job_exp_3")
        
        if st.button("簡易マッチ分析を実行"):
            prompt = f"年齢{m_age}歳、応募業種：{m_ind}(経験{m_ind_exp})、応募職種：{m_job}(経験{m_job_exp})。この条件での採用マッチ度(0-100%)と、その理由を簡潔に出力してください。フォーマット：【マッチ度】【理由】"
            with st.spinner("計算中..."):
                resp = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
                st.markdown(f"<div class='fb-box'>{resp.text}</div>", unsafe_allow_html=True)
            
    else:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("🏢 企業要件")
            c_info = st.text_area("求人票の内容・求める人物像など", height=200)
            c_files = st.file_uploader("企業資料・求人票PDF", accept_multiple_files=True, key="c_up_3")
        with col2:
            st.subheader("📄 完成書類")
            s_info = st.text_area("求職者の追加補足", height=200)
            s_files = st.file_uploader("作成済みの書類", accept_multiple_files=True, key="s_up_3")

        if st.button("詳細審査 & 推薦文作成"):
            if not my_name:
                st.error("アドバイザー名を入力してください。")
            else:
                with st.spinner("マッチ度を厳密に審査中..."):
                    c_data = read_files(c_files)
                    s_data = read_files(s_files)
                    prompt = f"""
あなたは凄腕ヘッドハンター兼採用担当者です。
企業要件と求職者の書類を照らし合わせ、マッチ度を％で算出し、推薦メールを作成してください。

企業情報：{c_info}\n{c_data}
求職者書類：{s_info}\n{s_data}

---
【マッチ度】
(0〜100の数字のみ)
【書類修正アドバイス】
(さらに通過率を上げるための具体的な修正点)
【面接対策】
(想定質問と回答の方向性)
【推薦文】
(企業名) 採用ご担当者様

お世話になっております。キャリアアドバイザーの株式会社ライフアップの{my_name}です。
この度、○○様を推薦させていただきたく、ご連絡申し上げました。

【推薦理由】
・(応募企業に活かせる強み)
・(貢献できる理由)
・(懸念点払拭があれば)
・人柄や熱意も含めて200-300字程度
・AI記号「」などは禁止)
ぜひ一度、面接にてご本人とお話しいただけますと幸いです。
何卒ご検討のほど、よろしくお願い申し上げます。
"""
                    try:
                        resp = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
                        res_m = resp.text
                        match_score_raw = get_section('マッチ度', res_m)
                        ms = int(re.search(r'\d+', match_score_raw).group()) if re.search(r'\d+', match_score_raw) else 0
                        
                        st.markdown(f"""
                        <div class="cyber-panel">
                            <div class="scan-line"></div>
                            <h3>最終マッチ度: {ms} %</h3>
                            <div class='fb-box'>{get_section('書類修正アドバイス', res_m)}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        if ms >= 80:
                            st.success("🔥 合格ライン突破！推薦状が利用可能です。")
                            st.subheader("📧 推薦メール案")
                            st.code(get_section('推薦文', res_m), language="text")
                        else:
                            st.warning("⚠️ マッチ度が基準(80%)を下回っています。修正が必要です。")
                        
                        st.subheader("🗣️ 面接対策")
                        st.write(get_section('面接対策', res_m))
                    except Exception as e:
                        st.error(f"エラー: {e}")


















































