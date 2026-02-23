import streamlit as st
import streamlit.components.v1 as components
from google import genai
import re
from pypdf import PdfReader
import time
from docx import Document
from io import BytesIO
import requests
from bs4 import BeautifulSoup

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

@keyframes move-bg {
    0% { background_position: 0 0; }
    100% { background-position: 1000px 1000px; }
}
.stApp::before {
    content: "";
    position: fixed;
    top: 0; left: 0; width: 100vw; height: 100vh;
    background-image: radial-gradient(#00E5FF 1.5px, transparent 1.5px);
    background-size: 50px 50px;
    opacity: 0.15;
    animation: move-bg 30s linear infinite;
    pointer-events: none;
    z-index: 0;
}
.block-container {
    position: relative;
    z-index: 1;
}

.cyber-panel {
    background: rgba(23, 42, 70, 0.7);
    border: 1px solid #00E5FF;
    box-shadow: 0 0 20px rgba(0, 229, 255, 0.4);
    border-radius: 10px; padding: 25px; margin-top: 20px;
    position: relative; overflow: hidden;
}

.scan-line {
    position: absolute; top: -100%; left: -100%; width: 300%; height: 300%;
    background: linear-gradient(to bottom, transparent, rgba(0, 229, 255, 0.4) 50%, transparent);
    transform: rotate(45deg); animation: scan 2.5s ease-in-out forwards; pointer-events: none;
}
@keyframes scan { 0% { top: -150%; } 100% { top: 150%; } }

.fb-box {
    background: rgba(255, 255, 255, 0.05);
    border-left: 4px solid #00E5FF;
    padding: 15px; margin-top: 10px;
}

label p, .stTextInput label, .stNumberInput label, .stTextArea label, .stRadio label, .stSelectbox label { 
    color: #FFFFFF !important; 
    font-weight: bold !important; 
    font-size: 1rem !important;
}
[data-testid="stMetricValue"] { color: #00E5FF !important; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 💾 セッション記憶
# ==========================================
if "history_log" not in st.session_state:
    st.session_state.history_log = [] 
if "phase2_generated" not in st.session_state:
    st.session_state.phase2_generated = False 
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

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

def get_url_text(url):
    try:
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.content, 'html.parser')
        for script in soup(["script", "style"]):
            script.extract()
        text = soup.get_text(separator='\n')
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        return text[:3000] 
    except Exception as e:
        return f"[URL読み取りエラー: {e}]"

def get_section(name, text):
    pattern = f"【{name}】(.*?)(?=【|$)"
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else f"{name}の情報が生成されませんでした。プロンプトを再確認してください。"

def create_docx(history_text):
    doc = Document()
    doc.add_heading('職務経歴書（自己PR含む）', 0)
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
    
    st.divider()
    st.subheader("🕒 生成履歴 (最新5件)")
    if not st.session_state.history_log:
        st.caption("履歴はありません")
    else:
        for i, log in enumerate(st.session_state.history_log):
            with st.expander(f"📁 {log['time']} ({log['job']})"):
                # ★追加：履歴を復元するボタン
                if st.button("🔄 この画面を復元する", key=f"restore_btn_{i}"):
                    st.session_state.phase2_score = log["score"]
                    st.session_state.phase2_advice = log["advice"]
                    st.session_state.phase2_combined = log["combined"]
                    st.session_state.phase2_motive = log["motive"]
                    st.session_state.chat_messages = log["chat"]
                    st.session_state.phase2_generated = True
                    st.rerun()
                
                dl_doc = create_docx(log["combined"])
                st.download_button(
                    label="📥 WordをDL",
                    data=dl_doc,
                    file_name=f"履歴_職務経歴書_{i}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    key=f"hist_dl_{i}"
                )

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
        if total >= 15: st.success("NICE❕ **【エージェント指示】** 優先度：高")
        elif 7 <= total < 15: st.info("safe **【エージェント指示】** 優先度：中")
        else: st.error("🚨 **【エージェント指示】** 優先度：低")

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
        u_url_corp = st.text_input("🔗 求人票URL (自動読み取り)", placeholder="https://...")
        u_files_corp = st.file_uploader("企業求人票など", accept_multiple_files=True, key="corp_up")
        
    with col2:
        st.subheader("📂 求職者情報")
        u_files_seeker = st.file_uploader("履歴書・面談文字起こし", accept_multiple_files=True, key="seeker_up")
        achievement = st.text_area("求職者の補足事項・メモ", height=100)
        
        components.html("""
        <div style="font-family: sans-serif; margin-top: -10px;">
            <p style="color: #00E5FF; font-size: 14px; font-weight: bold; margin-bottom: 5px;">🎤 音声入力</p>
            <button id="start-btn" style="background: transparent; color: #00E5FF; border: 1px solid #00E5FF; border-radius: 5px; padding: 5px 10px; cursor: pointer;">🔴 録音開始</button>
            <button id="stop-btn" style="background: transparent; color: #ff4b4b; border: 1px solid #ff4b4b; border-radius: 5px; padding: 5px 10px; cursor: pointer;" disabled>⏹ 停止</button>
            <textarea id="result" style="width: 100%; height: 70px; background: rgba(0,0,0,0.3); color: white; border: 1px solid #00E5FF; border-radius: 5px; padding: 5px; margin-top: 5px;"></textarea>
        </div>
        <script>
            const startBtn = document.getElementById('start-btn'); const stopBtn = document.getElementById('stop-btn');
            const resultArea = document.getElementById('result'); let recognition;
            if ('webkitSpeechRecognition' in window) {
                recognition = new webkitSpeechRecognition(); recognition.lang = 'ja-JP'; recognition.continuous = true;
                recognition.onresult = function(event) {
                    let finalTranscript = '';
                    for (let i = event.resultIndex; i < event.results.length; ++i) {
                        if (event.results[i].isFinal) finalTranscript += event.results[i][0].transcript;
                    }
                    if(finalTranscript) resultArea.value += finalTranscript + '\\n';
                };
                startBtn.onclick = () => { recognition.start(); startBtn.disabled = true; stopBtn.disabled = false; };
                stopBtn.onclick = () => { recognition.stop(); startBtn.disabled = false; stopBtn.disabled = true; };
            }
        </script>
        """, height=160)

    if st.button("AI書類生成を開始", type="primary"):
        corp_url_data = get_url_text(u_url_corp) if u_url_corp else ""
        corp_file_data = read_files(u_files_corp) if u_files_corp else ""
        corp_data = corp_file_data + "\n" + corp_url_data
        seeker_data = read_files(u_files_seeker) if u_files_seeker else ""
        
        if not (t_ind or t_job or corp_data.strip()): st.warning("企業情報を入力してください。")
        elif not (achievement or seeker_data.strip()): st.warning("求職者情報を入力してください。")
        else:
            with st.spinner("情報を深く分析中..."):
                prompt = f"""
あなたはプロキャリアライター兼採用目線の職務経歴書編集者です。
【企業情報】
業種：{t_ind} / 職種：{t_job}
資料：{corp_data}
【求職者情報】
メモ：{achievement}
資料：{seeker_data}

---
以下のセクションを省略せず出力してください。
【評価】(S/A/B/C/Z)
【理由とアドバイス】
【職務経歴】
※文末は「〜を実施。」「〜に貢献。」等で言い切ること。
【自己PR】
※文末は「〜です。〜ます。」の敬体。
【志望動機】
"""
                try:
                    resp = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
                    res = resp.text
                    st.session_state.phase2_score = get_section("評価", res)
                    st.session_state.phase2_advice = get_section("理由とアドバイス", res)
                    hist = get_section('職務経歴', res)
                    pr = get_section('自己PR', res)
                    st.session_state.phase2_combined = f"{hist}\n\n■自己PR\n{pr}"
                    st.session_state.phase2_motive = get_section('志望動機', res)
                    st.session_state.phase2_generated = True
                    st.session_state.chat_messages = [] 
                    
                    st.session_state.history_log.insert(0, {
                        "time": time.strftime('%Y/%m/%d %H:%M'),
                        "job": t_job if t_job else "未指定",
                        "score": st.session_state.phase2_score,
                        "advice": st.session_state.phase2_advice,
                        "combined": st.session_state.phase2_combined,
                        "motive": st.session_state.phase2_motive,
                        "chat": []
                    })
                    if len(st.session_state.history_log) > 5: st.session_state.history_log.pop()
                except Exception as e: st.error(f"解析エラー: {e}")

    if st.session_state.get("phase2_generated"):
        st.markdown(f'<div class="cyber-panel"><div class="scan-line"></div><h3>AI分析評価スコア: {st.session_state.phase2_score}</h3><div class="fb-box">{st.session_state.phase2_advice}</div></div>', unsafe_allow_html=True)
        st.divider()
        st.subheader("📄 職務経歴書（自己PR含む・高品質版）")
        st.code(st.session_state.phase2_combined, language="text")
        
        c_btn1, c_btn2, _ = st.columns([1.5, 1.2, 3])
        with c_btn1:
            docx_file = create_docx(st.session_state.phase2_combined)
            st.download_button(label="📥 WordでDL", data=docx_file, file_name=f"職務経歴書_{time.strftime('%Y%m%d')}.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        with c_btn2:
            components.html("""<button onclick="window.parent.print()" style="background:transparent; color:#00E5FF; border:1px solid #00E5FF; padding:8px 12px; border-radius:8px; font-size:13px; cursor:pointer; width:auto;">🖨️ PDF保存</button>""", height=50)
        
        st.subheader("📄 志望動機")
        st.code(st.session_state.phase2_motive, language="text")
        
        # --- AIチャット機能 ---
        st.divider()
        st.subheader("💬 AIアシスタントと内容を調整する")
        for msg in st.session_state.chat_messages:
            with st.chat_message(msg["role"]): st.markdown(msg["content"])
                
        if chat_input := st.chat_input("修正依頼を入力（例：志望動機の『』をなくして）"):
            st.session_state.chat_messages.append({"role": "user", "content": chat_input})
            with st.chat_message("user"): st.markdown(chat_input)
                
            with st.chat_message("assistant"):
                # ★強化ポイント：修正箇所を特定し、フォーマットを崩さないチャット用プロンプト
                chat_prompt = f"""
あなたはプロのキャリアコンサルタントです。ユーザーの【修正指示】に基づき、書類を改善してください。

【厳守ルール】
1. 指示されたセクション（職務経歴、自己PR、志望動機のいずれか）をピンポイントで修正。
2. 他のセクションは一切変更しない。
3. 元の改行、見出し(■,▼,・)、箇条書き、体言止めのフォーマットを絶対に崩さない。

【現在の書類データ】
{st.session_state.phase2_combined}
志望動機：{st.session_state.phase2_motive}

【ユーザーからの修正指示】
{chat_input}
"""
                try:
                    chat_resp = client.models.generate_content(model='gemini-2.5-flash', contents=chat_prompt)
                    st.markdown(chat_resp.text)
                    st.session_state.chat_messages.append({"role": "assistant", "content": chat_resp.text})
                    # 履歴のチャットログも更新
                    if st.session_state.history_log:
                        st.session_state.history_log[0]["chat"] = st.session_state.chat_messages
                except Exception as e: st.error(f"チャットエラー: {e}")

# ==========================================
# Phase 3: マッチ審査
# ==========================================
elif app_mode == "3. 書類作成後 (マッチ審査/推薦文)":
    st.title("Phase 3: 書類審査・マッチ度・推薦文")
    m_mode = st.radio("分析モード", ["1. 簡易マッチング", "2. 詳細マッチング"], horizontal=True)
    
    if m_mode == "1. 簡易マッチング":
        col1, col2 = st.columns(2)
        with col1:
            m_age = st.number_input("年齢", 18, 85, 25, key="m_age_3")
            m_ind = st.text_input("応募業種", key="m_ind_3")
        with col2:
            m_job = st.text_input("応募職種", key="m_job_3")
        
        if st.button("簡易マッチ分析を実行"):
            prompt = f"年齢{m_age}歳、応募業種：{m_ind}、応募職種：{m_job}のマッチ度と理由を出力。"
            resp = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
            st.markdown(f"<div class='cyber-panel'>{resp.text}</div>", unsafe_allow_html=True)
    else:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("🏢 企業要件")
            c_url_3 = st.text_input("🔗 求人URL", key="c_url_3")
            c_info = st.text_area("求人内容", height=130)
            c_files = st.file_uploader("資料", accept_multiple_files=True, key="c_up_3")
        with col2:
            st.subheader("📄 完成書類")
            s_info = st.text_area("追加補足", height=200)
            s_files = st.file_uploader("完成書類", accept_multiple_files=True, key="s_up_3")

        if st.button("詳細審査 & 推薦文作成", type="primary"):
            if not my_name: st.error("アドバイザー名を入力してください。")
            else:
                with st.spinner("審査中..."):
                    c_data = read_files(c_files) + "\n" + (get_url_text(c_url_3) if c_url_3 else "")
                    s_data = read_files(s_files)
                    prompt = f"""
凄腕ヘッドハンターとして、企業要件{c_info}{c_data}と、求職者書類{s_info}{s_data}を審査し、以下を出力せよ。
【マッチ度】(数字)
【書類修正アドバイス】
【面接対策】
【推薦文】(株式会社ライフアップ {my_name}名義)
"""
                    try:
                        resp = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
                        res_m = resp.text
                        match_score_raw = get_section('マッチ度', res_m)
                        ms = int(re.search(r'\d+', match_score_raw).group()) if re.search(r'\d+', match_score_raw) else 0
                        st.metric("最終マッチ度", f"{ms} %")
                        st.markdown(f"#### ✍️ アドバイス\n<div class='fb-box'>{get_section('書類修正アドバイス', res_m)}</div>", unsafe_allow_html=True)
                        if ms >= 80:
                            st.success("🔥 合格ライン突破！"); st.code(get_section('推薦文', res_m), language="text")
                        st.subheader("🗣️ 面接対策"); st.write(get_section('面接対策', res_m))
                    except Exception as e: st.error(f"エラー: {e}")
