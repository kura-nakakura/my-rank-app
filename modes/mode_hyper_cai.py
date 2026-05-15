import streamlit as st
import streamlit.components.v1 as components
import re
import time
from google.genai import types as genai_types
from utils import safe_generate_content, read_files, create_google_doc


def _run_chat(prompt_text):
    """ユーザー入力を受け取りAIから返答を得て履歴に追加する共通処理"""
    st.session_state.hyper_messages.append({"role": "user", "content": prompt_text})

    context = (
        f"求職者情報:\n{st.session_state.hyper_context.get('seeker','')}\n\n"
        f"求人情報:\n{st.session_state.hyper_context.get('job','')}"
    )
    history = "\n".join([
        f"{m['role']}: {m['content']}"
        for m in st.session_state.hyper_messages[-6:]
    ])

    sys_prompt = f"""あなたは世界最高峰のキャリアアドバイザーAI「HYPER-CAI-pro」です。
【コンテキスト】
{context}
【会話履歴】
{history}

【あなたの任務】
1. 圧倒的な分析力で求職者を内定に導く。
2. プレゼン作成を依頼されたらMckinsey/BCGスタイルのスライド型HTMLを出力する。
3. 文体は極めてプロフェッショナルで熱意が伝わるものにする。
4. 最後に必ず「次の推奨アクション」を3つ提示する。

【プレゼン資料の絶対ルール】
スライド型プレゼンはボタンで切り替わる複数ページ構成のHTMLで出力。5枚以上のスライドを含めること。

```html
<!DOCTYPE html><html lang="ja"><head><style>
  body{{margin:0;font-family:'Helvetica Neue',sans-serif;background:#e2e8f0;overflow:hidden;}}
  .slide{{display:none;flex-direction:column;justify-content:flex-start;height:100vh;padding:60px 80px;background:#f8fafc;box-sizing:border-box;position:relative;}}
  .slide.active{{display:flex;animation:fadeIn 0.5s ease-in-out;}}
  @keyframes fadeIn{{from{{opacity:0;transform:translateY(10px);}}to{{opacity:1;transform:translateY(0);}}}}
  h1{{color:#005088;font-size:60px;margin-bottom:20px;margin-top:20vh;text-align:center;}}
  h2{{color:#005088;font-size:45px;border-left:8px solid #11caa0;padding-left:20px;margin-top:0;}}
  .content{{flex-grow:1;width:100%;font-size:24px;color:#333;line-height:1.6;}}
  .controls{{position:fixed;bottom:30px;left:50%;transform:translateX(-50%);display:flex;gap:20px;z-index:1000;}}
  button{{padding:12px 30px;font-size:18px;font-weight:bold;cursor:pointer;background:#005088;color:white;border:none;border-radius:30px;}}
  .slide-number{{position:absolute;bottom:30px;right:40px;font-size:20px;color:#005088;font-weight:bold;}}
</style></head><body>
  <div id="slides-container">
    <div class="slide active"><h1>[タイトル]</h1><div class="slide-number">1</div></div>
    <div class="slide"><h2>[見出し]</h2><div class="content">[内容]</div><div class="slide-number">2</div></div>
  </div>
  <div class="controls">
    <button onclick="prevSlide()">◀ 前へ</button>
    <button onclick="nextSlide()">次へ ▶</button>
  </div>
  <script>
    let current=0;const slides=document.querySelectorAll('.slide');
    function showSlide(n){{slides.forEach(s=>s.classList.remove('active'));current=(n+slides.length)%slides.length;slides[current].classList.add('active');}}
    function nextSlide(){{showSlide(current+1);}}function prevSlide(){{showSlide(current-1);}}
  </script>
</body></html>
```

ユーザーの指示: {prompt_text}
"""
    try:
        pending_images = st.session_state.get("hyper_images", [])
        if pending_images:
            contents = []
            for img in pending_images:
                contents.append(
                    genai_types.Part.from_bytes(data=img["bytes"], mime_type=img["mime"])
                )
            contents.append(sys_prompt)
            resp = safe_generate_content(contents)
            st.session_state.hyper_images = []
        else:
            resp = safe_generate_content(sys_prompt)
        ai_msg = resp.text
        st.session_state.hyper_messages.append({"role": "assistant", "content": ai_msg})
    except Exception as e:
        st.session_state.hyper_messages.append({
            "role": "assistant",
            "content": f"⚠️ エラーが発生しました: {e}",
        })


def show():
    st.markdown("""
        <style>
        /* ── 背景：動画を非表示・完全黒 ── */
        video { display: none !important; }
        .stApp {
            background: #000000 !important;
            background-image: none !important;
        }
        header { background-color: transparent !important; }

        /* ── チャット吹き出し ── */
        div[data-testid="stChatMessage"] {
            background: linear-gradient(145deg, rgba(30,25,5,0.9) 0%, rgba(10,10,10,0.95) 100%) !important;
            border: 1px solid rgba(255,215,0,0.4) !important;
            box-shadow: 0 4px 15px rgba(255,215,0,0.05) !important;
            border-radius: 12px !important;
            color: #f3f0df !important;
        }

        /* ── エクスパンダー ── */
        [data-testid="stExpander"] {
            background-color: rgba(20,20,20,0.8) !important;
            border: 1px solid rgba(255,215,0,0.3) !important;
            border-radius: 10px !important;
        }
        [data-testid="stExpander"] p, [data-testid="stExpander"] span {
            color: #FFD700 !important;
        }

        /* ── メインのゴールドボタン ── */
        section.main .stButton>button {
            background: linear-gradient(135deg, #FFD700 0%, #DAA520 100%) !important;
            color: #000000 !important;
            border: none !important;
            box-shadow: 0 4px 15px rgba(255,215,0,0.4) !important;
            font-weight: 900 !important;
            border-radius: 8px !important;
            transition: all 0.3s ease;
        }
        section.main .stButton>button:hover {
            box-shadow: 0 6px 25px rgba(255,215,0,0.7) !important;
            transform: translateY(-2px);
        }

        /* ── ツールバーボタン（小サイズ・黒金白）── */
        .hyper-toolbar .stButton>button,
        .hyper-toolbar [data-testid="stDownloadButton"]>button {
            background: #000000 !important;
            color: #FFFFFF !important;
            border: 1px solid rgba(255,215,0,0.55) !important;
            box-shadow: 0 0 8px rgba(255,215,0,0.35) !important;
            font-size: 0.72rem !important;
            font-weight: 600 !important;
            padding: 4px 8px !important;
            border-radius: 5px !important;
            transition: all 0.2s ease;
            white-space: nowrap;
        }
        .hyper-toolbar .stButton>button:hover,
        .hyper-toolbar [data-testid="stDownloadButton"]>button:hover {
            box-shadow: 0 0 16px rgba(255,215,0,0.8) !important;
            transform: translateY(-1px);
        }

        /* ── サイドバー ── */
        [data-testid="stSidebar"] { background-color: #000000 !important; }
        [data-testid="stSidebar"] .stButton>button {
            background: #000000 !important;
            color: #FFFFFF !important;
            border: 1px solid rgba(255,215,0,0.5) !important;
            box-shadow: 0 0 12px rgba(255,215,0,0.45) !important;
            font-weight: 600 !important;
            letter-spacing: 1px;
            border-radius: 6px !important;
            transition: all 0.25s ease;
        }
        [data-testid="stSidebar"] .stButton>button:hover {
            background: #0a0a0a !important;
            box-shadow: 0 0 20px rgba(255,215,0,0.85) !important;
            transform: translateY(-1px);
        }
        [data-testid="stSidebar"] h1,[data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3,[data-testid="stSidebar"] label,
        [data-testid="stSidebar"] p { color: #FFFFFF !important; }

        /* ── タイトル ── */
        .hyper-title {
            text-align: center; color: #FFD700; font-size: 48px; font-weight: 900;
            text-shadow: 0 0 30px rgba(255,215,0,0.6); margin-bottom: 10px;
            font-family: 'Helvetica Neue', sans-serif; letter-spacing: 2px;
        }
        </style>
        <div class="hyper-title">HYPER-CAI-pro</div>
        <p style="text-align:center;color:#FFD700;margin-bottom:20px;letter-spacing:4px;">世界最高峰のキャリアアドバイザーAI</p>
    """, unsafe_allow_html=True)

    # ── コンテキスト初期化 ─────────────────────────────────────
    if "hyper_context" not in st.session_state:
        st.session_state.hyper_context = {"seeker": "", "job": ""}
    if "hyper_images" not in st.session_state:
        st.session_state.hyper_images = []

    # Phase 2/3引き継ぎ通知
    has_synced_seeker = bool(st.session_state.hyper_context.get("seeker", "").strip())
    has_synced_job = bool(st.session_state.hyper_context.get("job", "").strip())
    if has_synced_seeker or has_synced_job:
        st.success(
            "他モードからコンテキストを引き継ぎました："
            + ("【求職者情報】" if has_synced_seeker else "")
            + ("【求人企業情報】" if has_synced_job else "")
        )

    # ── コンテキスト入力 ───────────────────────────────────────
    with st.expander("引き継ぎ情報・ファイル添付", expanded=not (has_synced_seeker or has_synced_job)):
        c1, c2 = st.columns(2)
        with c1:
            st.session_state.hyper_context["seeker"] = st.text_area(
                "求職者情報", value=st.session_state.hyper_context.get("seeker", ""), height=130
            )
        with c2:
            st.session_state.hyper_context["job"] = st.text_area(
                "求人企業情報", value=st.session_state.hyper_context.get("job", ""), height=130
            )

        st.markdown("##### ファイル添付（PDF・TXT・画像）")
        uploaded_files = st.file_uploader(
            "添付ファイル",
            accept_multiple_files=True,
            type=["pdf", "txt", "png", "jpg", "jpeg", "webp"],
            key="hyper_uploads",
            label_visibility="collapsed",
        )
        if uploaded_files:
            image_files = [f for f in uploaded_files if f.type and f.type.startswith("image/")]
            text_files  = [f for f in uploaded_files if not (f.type and f.type.startswith("image/"))]
            if text_files:
                extracted = read_files(text_files)
                st.session_state.hyper_context["seeker"] = (
                    st.session_state.hyper_context.get("seeker", "") + "\n\n" + extracted
                ).strip()
                st.success(f"{len(text_files)}件のファイルからテキストを抽出してコンテキストに追加しました")
            if image_files:
                st.session_state.hyper_images = [
                    {"name": f.name, "bytes": f.getvalue(), "mime": f.type or "image/jpeg"}
                    for f in image_files
                ]
                cols = st.columns(min(len(image_files), 4))
                for idx, f in enumerate(image_files):
                    with cols[idx % 4]:
                        st.image(f, caption=f.name, use_container_width=True)
                st.info(f"{len(image_files)}枚の画像を添付済み。次のメッセージ送信時にAIが読み取ります。")

    # ── チャット履歴初期化 ─────────────────────────────────────
    if "hyper_messages" not in st.session_state:
        st.session_state.hyper_messages = [{
            "role": "assistant",
            "content": "私は世界最高峰のエージェント、HYPER-CAIです。引き継いだ情報・添付ファイルを元に、内定までの戦略立案、書類の最終調整、面接対策資料の作成まで、すべてをお手伝いします。何をしましょうか？"
        }]

    # ── サイドバー クイックアクション ─────────────────────────
    st.sidebar.subheader("クイック・プロ・アクション")
    quick_action = None
    if st.sidebar.button("内定獲得の戦略を立案", use_container_width=True, key="qa_strategy"):
        quick_action = "この求職者と企業の情報を分析して、内定を勝ち取るための全体戦略を立てて。"
    if st.sidebar.button("面接対策プレゼンを作成", use_container_width=True, key="qa_presen"):
        quick_action = "求職者向けの面接対策プレゼン資料（HTML形式・5枚以上のスライド型）を作成して。"
    if st.sidebar.button("企業への極上推薦文", use_container_width=True, key="qa_recom"):
        quick_action = "企業担当者が即決で会いたくなるような、プロ視点の推薦文を書いて。"
    if st.sidebar.button("想定面接質問と模範回答", use_container_width=True, key="qa_qa"):
        quick_action = "この求人に対して、想定される面接質問を10個と、求職者の強みを活かした模範回答を作成して。"
    if st.sidebar.button("強み・弱み・リスク分析", use_container_width=True, key="qa_swot"):
        quick_action = "この求職者の強み・弱み・採用リスクをSWOT分析の形式で洗い出して。"

    if quick_action:
        with st.spinner("思考中..."):
            _run_chat(quick_action)
        st.rerun()

    # ── チャット入力 ──────────────────────────────────────────
    if prompt := st.chat_input("HYPER-CAIに指示を出す..."):
        with st.spinner("思考中..."):
            _run_chat(prompt)
        st.rerun()

    # ── 最新AI回答
    last_assistant_msg = next(
        (m["content"] for m in reversed(st.session_state.hyper_messages) if m["role"] == "assistant"),
        "",
    )

    # 会話全文テキスト化
    transcript = "\n\n".join([
        f"【{('AI' if m['role']=='assistant' else 'ユーザー')}】\n{m['content']}"
        for m in st.session_state.hyper_messages
    ])

    # ── ツールバー（チャット上部）──────────────────────────────
    st.markdown('<div class="hyper-toolbar">', unsafe_allow_html=True)
    tb1, tb2, tb3, tb4 = st.columns([2, 2, 2, 1])
    with tb1:
        st.download_button(
            "テキスト保存",
            transcript,
            file_name=f"HYPER-CAI_{time.strftime('%Y%m%d_%H%M')}.txt",
            mime="text/plain",
            use_container_width=True,
            key="dl_transcript",
        )
    with tb2:
        if st.button("最新回答 → Docs", use_container_width=True, key="docs_last"):
            if not last_assistant_msg:
                st.warning("AI回答がまだありません。")
            else:
                with st.spinner("作成中..."):
                    ok, url = create_google_doc(f"HYPER-CAI_回答_{time.strftime('%Y%m%d_%H%M')}", last_assistant_msg)
                    if ok:
                        st.success(f"[Docsを開く]({url})")
                    else:
                        st.error(url)
    with tb3:
        if st.button("全文 → Docs", use_container_width=True, key="docs_all"):
            with st.spinner("作成中..."):
                ok, url = create_google_doc(f"HYPER-CAI_全文_{time.strftime('%Y%m%d_%H%M')}", transcript)
                if ok:
                    st.success(f"[Docsを開く]({url})")
                else:
                    st.error(url)
    with tb4:
        if st.button("リセット", use_container_width=True, key="reset_chat"):
            st.session_state.hyper_messages = []
            st.session_state.hyper_images = []
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # ── チャット表示（拡張）──────────────────────────────────
    chat_area = st.container(height=640)
    for msg in st.session_state.hyper_messages:
        with chat_area.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # ── HTMLプレゼンプレビュー ────────────────────────────────
    html_match = re.search(r'<!DOCTYPE html>.*?</html>', last_assistant_msg, re.DOTALL | re.IGNORECASE)
    if html_match:
        st.divider()
        st.subheader("プレゼン資料プレビュー")
        components.html(html_match.group(), height=520, scrolling=True)
        st.download_button(
            "プレゼンHTMLをダウンロード",
            html_match.group(),
            file_name=f"strategy_{time.strftime('%Y%m%d_%H%M')}.html",
            mime="text/html",
            key="dl_presen",
        )
