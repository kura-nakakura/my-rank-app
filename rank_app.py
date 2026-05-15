import streamlit as st
import base64
import os

from utils import create_google_doc, ca_icon_img
# インデント（左端の空白）を完全に除去し、プレゼンモードも追加
from modes import mode1_rank, mode2_carte, mode3_docs, mode4_review, mode_auto, mode_hyper_cai


# ==========================================
# デザイン定義
# ==========================================
def get_base64_video(video_path):
    try:
        with open(video_path, "rb") as video_file:
            return base64.b64encode(video_file.read()).decode()
    except Exception:
        return ""


_page_icon_path = os.path.join(os.path.dirname(__file__), "assets", "ca_icon.svg")
st.set_page_config(
    page_title="AIエージェントシステム PRO",
    page_icon=_page_icon_path if os.path.exists(_page_icon_path) else "🤖",
    layout="wide",
)

video_base64 = get_base64_video("ScreenRecording_03-04-2026 13-38-53_1.mov")

if video_base64:
    video_html = f"""
    <video autoplay loop muted playsinline style="position: fixed; right: 0; bottom: 0; min-width: 100%; min-height: 100%; z-index: -1; object-fit: cover; opacity: 0.8;">
        <source src="data:video/mp4;base64,{video_base64}" type="video/mp4">
    </video>
    """
    st.markdown(video_html, unsafe_allow_html=True)

st.markdown("""
<style>
/* 1. 背景の設定 */
.stApp { background-color: transparent !important; background-image: none !important; }
header { background-color: transparent !important; }

/* 2. メイン画面の文字色 */
.main .block-container h1, .main .block-container h2, .main .block-container h3,
.main .block-container h4, .main .block-container p, .main .block-container span,
.main .block-container div {
    color: #FFFFFF !important; text-shadow: 0px 2px 4px rgba(0,0,0,0.8);
}

/* 3. サイドバー */
[data-testid="stSidebar"] {
    background-color: rgba(5, 15, 30, 0.85) !important; backdrop-filter: blur(10px);
}
[data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label {
    color: #00E5FF !important; text-shadow: none !important;
}
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
    color: #FFFFFF !important;
    text-shadow: 0 0 10px rgba(255, 255, 255, 0.3) !important;
}
.block-container { position: relative; z-index: 1; }

/* 5. ダークグラスモーフィズムパネル */
.cyber-panel, [data-testid="stVerticalBlockBorderWrapper"] {
    background: rgba(10, 20, 40, 0.6) !important; backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px); border: 1px solid rgba(0, 229, 255, 0.3) !important;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5) !important; border-radius: 12px !important;
    padding: 25px; margin-top: 20px; position: relative; overflow: hidden;
}

/* 6. HUD装飾 */
.cyber-panel::before, [data-testid="stVerticalBlockBorderWrapper"]::before {
    content: ""; position: absolute; top: 0; left: 0; width: 25px; height: 25px;
    border-top: 3px solid #00E5FF; border-left: 3px solid #00E5FF; border-top-left-radius: 12px;
}
.cyber-panel::after, [data-testid="stVerticalBlockBorderWrapper"]::after {
    content: ""; position: absolute; bottom: 0; right: 0; width: 25px; height: 25px;
    border-bottom: 3px solid #00E5FF; border-right: 3px solid #00E5FF; border-bottom-right-radius: 12px;
}

/* 7. フィードバックボックス */
.fb-box {
    background: rgba(0, 229, 255, 0.1) !important; border-left: 4px solid #00E5FF !important;
    padding: 15px; margin-top: 10px; border-radius: 6px;
}

/* 8. 入力フォーム */
.stTextInput input, .stTextArea textarea, .stNumberInput input {
    background-color: rgba(0, 0, 0, 0.5) !important; color: #FFFFFF !important;
    border: 1px solid rgba(0, 229, 255, 0.4) !important; border-radius: 6px !important;
}
::placeholder { color: #8899A6 !important; opacity: 1 !important; }

/* 9. メトリック */
[data-testid="stMetricValue"] {
    color: #00E5FF !important; font-weight: bold; font-size: 2.5rem !important; text-shadow: 0 0 10px rgba(0, 229, 255, 0.5);
}

/* 10. ボタン */
.stButton>button { border-radius: 8px !important; font-weight: bold !important; transition: all 0.3s ease; }
.stButton>button[kind="primary"] {
    background: linear-gradient(135deg, #00E5FF 0%, #0077FF 100%) !important; color: white !important;
    border: none !important; box-shadow: 0 4px 10px rgba(0, 229, 255, 0.4) !important;
}
.stButton>button[kind="primary"]:hover {
    box-shadow: 0 6px 15px rgba(0, 229, 255, 0.7) !important; transform: translateY(-2px);
}

/* 11. ラジオボタンをサイバーな横タブに */
div[role="radiogroup"] {
    display: flex; flex-direction: row; justify-content: space-between;
    background: rgba(10, 20, 40, 0.6) !important; padding: 8px; border-radius: 12px;
    border: 1px solid rgba(0, 229, 255, 0.3); box-shadow: 0 4px 15px rgba(0,0,0,0.5);
    margin-bottom: 20px; flex-wrap: wrap; gap: 10px;
}
div[role="radiogroup"] > label {
    flex: 1; text-align: center; background: rgba(255, 255, 255, 0.05) !important;
    border: 1px solid transparent !important; border-radius: 8px !important;
    padding: 12px 10px !important; cursor: pointer; transition: all 0.3s ease;
    display: flex; justify-content: center; align-items: center; min-width: 150px;
}
div[role="radiogroup"] > label:hover {
    background: rgba(0, 229, 255, 0.15) !important;
    border: 1px solid rgba(0, 229, 255, 0.5) !important; transform: translateY(-2px);
}
div[role="radiogroup"] > label > div:first-child { display: none !important; }
div[role="radiogroup"] > label[aria-checked="true"], div[role="radiogroup"] > label[data-checked="true"] {
    background: linear-gradient(135deg, rgba(0, 229, 255, 0.6) 0%, rgba(0, 119, 255, 0.6) 100%) !important;
    border: 1px solid #00E5FF !important; box-shadow: 0 0 20px rgba(0, 229, 255, 0.5);
}
div[role="radiogroup"] p, div[role="radiogroup"] span, div[role="radiogroup"] div {
    color: #FFFFFF !important; font-weight: bold !important; margin: 0 !important;
    font-size: 0.95rem !important; text-shadow: 0 1px 3px rgba(0,0,0,0.8);
}
</style>
""", unsafe_allow_html=True)

# ==========================================
# セッション記憶
# ==========================================
if "history_log" not in st.session_state:
    st.session_state.history_log = []
if "carte_log" not in st.session_state:
    st.session_state.carte_log = []
if "phase2_generated" not in st.session_state:
    st.session_state.phase2_generated = False
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []
if "p0_generated" not in st.session_state:
    st.session_state.p0_generated = False
if "p0_interview_date" not in st.session_state:
    st.session_state.p0_interview_date = ""
if "p0_change_count" not in st.session_state:
    st.session_state.p0_change_count = ""
if "p0_short_term" not in st.session_state:
    st.session_state.p0_short_term = ""
if "p0_company" not in st.session_state:
    st.session_state.p0_company = ""
if "current_key_idx" not in st.session_state:
    st.session_state.current_key_idx = 0
if "top_mode" not in st.session_state:
    st.session_state.top_mode = None

# ==========================================
# ログイン
# ==========================================
LOGIN_PASSWORD = "HR9237"
if "password_correct" not in st.session_state:
    st.session_state.password_correct = False
if not st.session_state.password_correct:
    st.title("🛡️ システムログイン")
    pwd = st.text_input("アクセスコード", type="password")
    if st.button("ログイン"):
        if pwd == LOGIN_PASSWORD:
            st.session_state.password_correct = True
            st.rerun()
        else:
            st.error("コードが違います")
    st.stop()

# ==========================================
# トップ画面：モード選択
# ==========================================
if st.session_state.top_mode is None:
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown(
        '<h1 style="text-align:center; color:#FFFFFF; text-shadow:0 0 20px rgba(0,229,255,0.6);">'
        f'{ca_icon_img(48)} AIエージェントシステム PRO</h1>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p style="text-align:center; color:#00E5FF; font-size:1.1rem;">モードを選択してください</p>',
        unsafe_allow_html=True,
    )
    st.markdown("<br>", unsafe_allow_html=True)
    
    # HYPER-CAI起動ボタン（黒・金縁・白文字／コンパクト）
    st.markdown("""
    <style>
    [data-testid="stElementContainer"]:has(.hyper-launch-anchor) + [data-testid="stElementContainer"] button {
        background: #000000 !important;
        color: #FFFFFF !important;
        border: 1px solid rgba(255, 215, 0, 0.6) !important;
        box-shadow: 0 0 14px rgba(255, 215, 0, 0.5) !important;
        font-weight: 600 !important;
        letter-spacing: 1px;
        border-radius: 6px !important;
        transition: all 0.25s ease;
    }
    [data-testid="stElementContainer"]:has(.hyper-launch-anchor) + [data-testid="stElementContainer"] button:hover {
        background: #0a0a0a !important;
        box-shadow: 0 0 22px rgba(255, 215, 0, 0.9) !important;
        transform: translateY(-1px);
    }
    </style>
    """, unsafe_allow_html=True)
    col_c1, col_c2, col_c3 = st.columns([3, 2, 3])
    with col_c2:
        st.markdown('<div class="hyper-launch-anchor"></div>', unsafe_allow_html=True)
        if st.button("HYPER-CAIくん-pro を起動する", use_container_width=True, key="launch_hyper"):
            st.session_state.top_mode = "hyper"
            st.rerun()
    
    st.markdown("<br>", unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""
        <div style="background:rgba(10,20,40,0.7); border:1px solid rgba(0,229,255,0.4);
                    border-radius:16px; padding:30px; text-align:center; min-height:220px;">
            <div style="font-size:3rem;">🚀</div>
            <h2 style="color:#00E5FF;">自動化モード</h2>
            <p style="color:#FFFFFF; font-size:0.95rem;">
                面談メモ・履歴書・求人票を入力するだけで<br>
                <b>ランク判定 → カルテ → 書類作成 → 書類審査</b><br>
                を全自動で一括実行します
            </p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🚀 自動化モードへ", type="primary", use_container_width=True, key="btn_auto"):
            st.session_state.top_mode = "auto"
            st.rerun()

    with c2:
        st.markdown("""
        <div style="background:rgba(10,20,40,0.7); border:1px solid rgba(0,229,255,0.4);
                    border-radius:16px; padding:30px; text-align:center; min-height:220px;">
            <div style="font-size:3rem;">⚙️</div>
            <h2 style="color:#00E5FF;">手動モード</h2>
            <p style="color:#FFFFFF; font-size:0.95rem;">
                4つの工程（ランク判定・カルテ作成・<br>
                書類作成・書類審査）を<br>
                それぞれ個別に細かく操作できます
            </p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("⚙️ 手動モードへ", type="primary", use_container_width=True, key="btn_manual"):
            st.session_state.top_mode = "manual"
            st.rerun()

    st.stop()

# ==========================================
# サイドバー
# ==========================================
st.sidebar.title("AI AGENT MENU")

if st.sidebar.button("← モード選択に戻る", use_container_width=True):
    st.session_state.top_mode = None
    st.rerun()

st.sidebar.divider()

agent_name = st.sidebar.text_input("アドバイザー名", placeholder="山田 太郎")

if st.session_state.top_mode != "hyper":
  st.sidebar.divider()
  st.sidebar.subheader("📋 面談カルテ履歴 (最新20件)")
  if not st.session_state.carte_log:
    st.sidebar.caption("カルテの履歴はありません")
  else:
    for i, log in enumerate(st.session_state.carte_log):
        with st.sidebar.expander(f"👤 {log['time']} ({log['name']}様)"):
            if st.button("🔄 復元", key=f"c_res_{i}"):
                st.session_state.p0_interview_date = log["data"].get("面談日", "不明")
                st.session_state.p0_agent = log["data"].get("エージェント名", "")
                st.session_state.p0_seeker = log["data"].get("求職者名", "")
                st.session_state.p0_recog = log["data"].get("エージェント面談の認識", "")
                st.session_state.p0_exp = log["data"].get("エージェントの利用経験", "")
                st.session_state.p0_age = log["data"].get("生年月日・年齢", "")
                st.session_state.p0_cert = log["data"].get("保有資格", "")
                st.session_state.p0_status = log["data"].get("現在の勤務状況", "")
                st.session_state.p0_history = log["data"].get("職務経歴", "")
                st.session_state.p0_reason1 = log["data"].get("転職を考えたきっかけ", "")
                st.session_state.p0_reason2 = log["data"].get("今回の転職で叶えたいこと", "")
                st.session_state.p0_reason3 = log["data"].get("今後のビジョン", "")
                st.session_state.p0_str = log["data"].get("自分の強み", "")
                st.session_state.p0_str_ep = log["data"].get("強みエピソード", "")
                st.session_state.p0_weak = log["data"].get("弱み", "")
                st.session_state.p0_weak_ep = log["data"].get("弱みエピソード", "")
                st.session_state.p0_c_job = log["data"].get("希望職種・業務", "")
                st.session_state.p0_c_loc = log["data"].get("希望勤務地", "")
                st.session_state.p0_c_cur_sal = log["data"].get("現在年収・給与", "")
                st.session_state.p0_c_req_sal = log["data"].get("希望年収・給与", "")
                st.session_state.p0_c_time = log["data"].get("勤務時間・休日", "")
                st.session_state.p0_c_vibes = log["data"].get("社風・雰囲気", "")
                st.session_state.p0_c_date = log["data"].get("入社希望日", "")
                st.session_state.p0_o_ans = log["data"].get("確認事項や不安ごと", "")
                st.session_state.p0_o_ndate = log["data"].get("次回面談日", "")
                st.session_state.p0_o_ntime = log["data"].get("次回面談時間", "")
                st.session_state.p0_generated = True
                st.rerun()

            if st.button("📄 Docs生成", key=f"hist_dl_c_{i}"):
                with st.spinner("Google Docsを作成中..."):
                    content_str = "【初回面談カルテ】\n\n"
                    for k, v in log["data"].items():
                        content_str += f"■ {k}\n{v}\n\n"
                    success, doc_url = create_google_doc(f"履歴_面談カルテ_{log['name']}", content_str)
                    if success:
                        st.markdown(f"✅ **[生成完了！ここをクリックしてDocsを開く]({doc_url})**")
                    else:
                        st.error(doc_url)

  st.sidebar.divider()
  st.sidebar.subheader("📄 書類生成履歴 (最新20件)")
  if not st.session_state.history_log:
    st.sidebar.caption("書類履歴はありません")
  else:
    for i, log in enumerate(st.session_state.history_log):
        with st.sidebar.expander(f"📁 {log['time']} ({log['job']})"):
            if st.button("🔄 この画面を復元する", key=f"restore_btn_{i}"):
                st.session_state.phase2_score = log["score"]
                st.session_state.phase2_advice = log["advice"]
                st.session_state.phase2_combined = log["combined"]
                st.session_state.phase2_motive = log.get("motive", "")
                st.session_state.chat_messages = log["chat"]
                st.session_state.phase2_generated = True
                st.rerun()

            if st.button("📄 Docs生成", key=f"hist_dl_{i}"):
                with st.spinner("Google Docsを作成中..."):
                    doc_content_str = f"{log['combined']}\n\n■志望動機\n{log.get('motive', '')}"
                    success, doc_url = create_google_doc(f"履歴_職務経歴書_{i}", doc_content_str)
                    if success:
                        st.markdown(f"✅ **[生成完了！ここをクリックしてDocsを開く]({doc_url})**")
                    else:
                        st.error(doc_url)

# ==========================================
# モードルーティング
# ==========================================
if st.session_state.top_mode == "auto":
    mode_auto.show()
elif st.session_state.top_mode == "hyper":
    mode_hyper_cai.show()
else:
    app_mode = st.radio(
        "フェーズ選択",
        ["1. ランク判定", "2. カルテ作成", "3. 書類作成", "4. 書類審査"],
        horizontal=True,
        label_visibility="collapsed",
    )
    st.markdown("<br>", unsafe_allow_html=True)

    if app_mode == "1. ランク判定":
        mode1_rank.show()
    elif app_mode == "2. カルテ作成":
        mode2_carte.show()
    elif app_mode == "3. 書類作成":
        mode3_docs.show()
    elif app_mode == "4. 書類審査":
        mode4_review.show(agent_name)