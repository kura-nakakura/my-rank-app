import streamlit as st
from google import genai
import re
from pypdf import PdfReader
import time

# ==========================================
# 🎨 デザイン定義
# ==========================================
st.set_page_config(page_title="AIエージェントシステム PRO", page_icon="🤖", layout="wide")

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
    box-shadow: 0 0 20px rgba(0, 229, 255, 0.4);
    border-radius: 10px; padding: 25px; margin-top: 20px;
}
.fb-box {
    background: rgba(255, 255, 255, 0.05);
    border-left: 4px solid #00E5FF;
    padding: 15px; margin-bottom: 15px;
}
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
    pattern = f"【{name}】\n?(.*?)(?=【|$)"
    match = re.search(pattern, text, re.DOTALL)
    return match.group(1).strip() if match else f"{name}の情報が見つかりませんでした。"

client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

# ==========================================
# 🎛️ サイドバー
# ==========================================
with st.sidebar:
    st.title("AI AGENT MENU")
    app_mode = st.radio("フェーズ選択", [
        "1. 応募時 (ランク判定)", 
        "2. 初回面談後 (詳細分析/高品質書類作成)", 
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
    with col1: age = st.number_input("年齢", 18, 85, 25) # 85歳まで対応
    with col2: job_changes = st.number_input("転職回数", 0, 15, 1)
    with col3: short_term = st.number_input("短期離職数", 0, 10, 0)
    
    if st.button("判定開始"):
        # スコアリングロジック
        age_s = 10 if 22 <= age <= 25 else (8 if 20 <= age <= 29 else 5)
        job_bonus = 10 if (age <= 29 and job_changes <= 1) or (age >= 30 and job_changes <= 2) else 5
        job_penalty = 0 if job_changes <= 1 else (-5 if job_changes == 2 else -15)
        st_penalty = short_term * 10
        total = age_s + job_bonus + job_penalty - st_penalty + 5

        if total >= 23: cn, rc = "優秀 (Class-S)", "#00ff00"
        elif total >= 18: cn, rc = "良好 (Class-A)", "#00e5ff"
        elif total >= 13: cn, rc = "標準 (Class-B)", "#ffff00"
        elif total >= 8: cn, rc = "要努力 (Class-C)", "#ff9900"
        else: cn, rc = "測定不能 (Class-Z)", "#ff0000"

        st.markdown(f'<div class="cyber-panel"><h3>判定結果: <span style="color:{rc};">{cn}</span></h3></div>', unsafe_allow_html=True)
        
        # 優先度通知の分離
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
    st.title("Phase 2: 詳細分析 & 高品質書類作成")
    col1, col2 = st.columns(2)
    with col1:
        t_ind = st.text_input("志望業種")
        t_job = st.text_input("志望職種")
        achievement = st.text_area("面談メモ・実績追加", height=150)
    with col2:
        u_files = st.file_uploader("履歴書等の資料添付", accept_multiple_files=True)

    if st.button("分析・書類生成開始"):
        with st.spinner("プロフェッショナルライターが執筆中..."):
            file_data = read_files(u_files)
            # あなたの高品質プロンプトをそのまま統合
            prompt = f"""
あなたは人材紹介会社のプロキャリアライター兼採用目線の職務経歴書編集者です。
以下の情報をもとに、最高の書類一式を作成してください。

【入力情報】
志望業種：{t_ind} / 職種：{t_job}
実績・メモ：{achievement}
添付資料：{file_data}

---
【評価】
(0〜10の数字のみ)
【理由】
(評価の理由)
【アドバイス】
(エージェントへの書類作成等で見抜くべき視点)

【職務経歴書】
**職務経歴書自動生成プロンプト（企業提出用・高品質版）**に従い作成。
■出力構成
1. 作成日・氏名
2. 職務経歴（各社ごとに「業務内容」と「成果」を分けて記載）
3. 応募企業に最適化された自己PR

■各職歴ブロック構成
【会社名】
雇用形態：◯◯
事業内容：◯◯
役職：◯◯
▼業務内容
・主要業務を5〜7行で簡潔に記載
▼成果
・数値・改善・貢献を具体的に。定量実績を優先。
・「何を→どう行い→どうなったか」で構成。

【自己PR】
- 応募企業の理念・社風・仕事内容に合わせ、これまでの経験をどう活かせるか記載。
- 400字でテンポよく読める構成に。事実を元にし、嘘や推測は含めない。
- 「」や””や・などAI文章だとわかる記号は控える。文章トーンは敬体。

【志望動機】
- 企業にマイナスにならないのを前提に年齢に合わせた文章、言葉使いにすること。
- 450字ほどで作成。企業情報に合わせた内容にする。
- 業務や実績などは推測や嘘はさけ、「」や””や・などは控えること。
"""
            resp = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
            res = resp.text
            
            st.metric("AI分析評価", f"{get_section('評価', res)} / 10")
            st.markdown(f"#### 💡 アドバイス\n<div class='fb-box'>{get_section('アドバイス', res)}</div>", unsafe_allow_html=True)
            st.divider()
            st.subheader("📄 作成された職務経歴書（自己PR含む）")
            st.code(get_section('職務経歴書', res), language="text")
            st.subheader("📄 作成された志望動機")
            st.code(get_section('志望動機', res), language="text")

# ==========================================
# Phase 3: 書類作成後 (マッチ審査/推薦文)
# ==========================================
elif app_mode == "3. 書類作成後 (マッチ審査/推薦文)":
    st.title("Phase 3: マッチ度審査 & 推薦文")
    m_mode = st.radio("分析モード", ["1. 簡易マッチング", "2. 詳細マッチング（推薦文あり）"], horizontal=True)
    
    if m_mode == "1. 簡易マッチング":
        col1, col2 = st.columns(2)
        with col1:
            m_age = st.number_input("年齢", 18, 85, 25, key="m_age")
            m_ind = st.text_input("応募業種")
            m_ind_exp = st.radio("業種経験", ["あり", "なし"], horizontal=True)
        with col2:
            m_job = st.text_input("応募職種")
            m_job_exp = st.radio("職種経験", ["あり", "なし"], horizontal=True)
        
        if st.button("簡易マッチ分析"):
            prompt = f"年齢{m_age}歳、業種：{m_ind}(経験{m_ind_exp})、職種：{m_job}(経験{m_job_exp})。この条件でのマッチ度を0-100で出し、理由を簡潔に述べてください。フォーマット：【マッチ度】【理由】"
            resp = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
            st.write(resp.text)
            
    else:
        col1, col2 = st.columns(2)
        with col1:
            c_info = st.text_area("企業要件・詳細", height=150)
            c_files = st.file_uploader("企業資料", accept_multiple_files=True, key="c_up")
        with col2:
            s_info = st.text_area("求職者補足", height=150)
            s_files = st.file_uploader("最終書類", accept_multiple_files=True, key="s_up")

        if st.button("詳細マッチ審査実行"):
            with st.spinner("最終審査中..."):
                c_data, s_data = read_files(c_files), read_files(s_files)
                prompt = f"""
凄腕ヘッドハンターとして、企業と求職者のマッチ度を審査してください。
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
以下の構成を守り、株式会社ライフアップ {my_name}として作成してください。
・(企業名) 採用ご担当者様
・お世話になっております。キャリアアドバイザーの株式会社ライフアップの{my_name}です。
・この度～(ここから魅力を伝える文章を作成。箇条書きの推薦ポイント、懸念払拭、人柄を含める。150字程度の自由文は「」等AI記号禁止)
"""
                resp = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
                res_m = resp.text
                ms = int(re.search(r'\d+', get_section('マッチ度', res_m)).group() or 0)
                
                st.metric("最終マッチ度", f"{ms} %")
                st.markdown(f"#### ✍️ 修正アドバイス\n{get_section('書類修正アドバイス', res_m)}")
                
                if ms >= 80:
                    st.success("🎉 マッチ度80%超え！推薦状を作成しました。")
                    st.subheader("📧 推薦メール案")
                    st.code(get_section('推薦文', res_m), language="text")
                else:
                    st.warning("⚠️ マッチ度が80%に達していません。アドバイスを元に修正してください。")
                
                st.subheader("🗣️ 面接対策")
                st.write(get_section('面接対策', res_m))






















