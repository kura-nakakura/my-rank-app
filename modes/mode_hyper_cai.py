import streamlit as st
import streamlit.components.v1 as components
import re
from google.genai import types as genai_types
from utils import safe_generate_content, read_files, create_google_doc


def show():
    st.markdown("""
        <style>
        /* 1. 背景をブラック＆ゴールドに */
        .stApp {
            background: radial-gradient(circle at top, #2b2200 0%, #0a0a0a 50%, #000000 100%) !important;
            background-color: #000000 !important;
            background-image: none !important;
        }
        header { background-color: transparent !important; }

        /* 2. チャット吹き出し */
        div[data-testid="stChatMessage"] {
            background: linear-gradient(145deg, rgba(30, 25, 5, 0.9) 0%, rgba(10, 10, 10, 0.95) 100%) !important;
            border: 1px solid rgba(255, 215, 0, 0.4) !important;
            box-shadow: 0 4px 15px rgba(255, 215, 0, 0.05) !important;
            border-radius: 12px !important;
            color: #f3f0df !important;
        }

        /* 3. エクスパンダー */
        [data-testid="stExpander"] {
            background-color: rgba(20, 20, 20, 0.8) !important;
            border: 1px solid rgba(255, 215, 0, 0.3) !important;
            border-radius: 10px !important;
        }
        [data-testid="stExpander"] p, [data-testid="stExpander"] span {
            color: #FFD700 !important;
        }

        /* 4. メインコンテンツのボタン → ゴールド */
        section.main .stButton>button {
            background: linear-gradient(135deg, #FFD700 0%, #DAA520 100%) !important;
            color: #000000 !important;
            border: none !important;
            box-shadow: 0 4px 15px rgba(255, 215, 0, 0.4) !important;
            font-weight: 900 !important;
            border-radius: 8px !important;
            transition: all 0.3s ease;
        }
        section.main .stButton>button:hover {
            box-shadow: 0 6px 25px rgba(255, 215, 0, 0.7) !important;
            transform: translateY(-2px);
        }

        /* 5. サイドバーのボタンは青いサイバースタイルを維持 */
        [data-testid="stSidebar"] .stButton>button {
            background: linear-gradient(135deg, #00E5FF 0%, #0077FF 100%) !important;
            color: white !important;
            border: none !important;
            box-shadow: 0 4px 10px rgba(0, 229, 255, 0.4) !important;
            font-weight: bold !important;
        }
        [data-testid="stSidebar"] .stButton>button:hover {
            box-shadow: 0 6px 15px rgba(0, 229, 255, 0.7) !important;
            transform: translateY(-2px);
        }

        /* 6. タイトル装飾 */
        .hyper-title {
            text-align: center; color: #FFD700; font-size: 48px; font-weight: 900;
            text-shadow: 0 0 30px rgba(255, 215, 0, 0.6); margin-bottom: 10px;
            font-family: 'Helvetica Neue', sans-serif; letter-spacing: 2px;
        }
        </style>
        <div class="hyper-title">✨ HYPER-CAI-pro ✨</div>
        <p style="text-align: center; color: #FFD700; margin-bottom: 20px;">世界最高峰のキャリアアドバイザーAI</p>
    """, unsafe_allow_html=True)

    # ── コンテキスト初期化 ─────────────────────────────────────
    if "hyper_context" not in st.session_state:
        st.session_state.hyper_context = {"seeker": "", "job": ""}
    if "hyper_images" not in st.session_state:
        st.session_state.hyper_images = []

    # ── コンテキスト入力 ───────────────────────────────────────
    with st.expander("📥 引き継ぎ情報・ファイル添付"):
        c1, c2 = st.columns(2)
        with c1:
            st.session_state.hyper_context["seeker"] = st.text_area(
                "求職者情報", value=st.session_state.hyper_context.get("seeker", ""), height=130
            )
        with c2:
            st.session_state.hyper_context["job"] = st.text_area(
                "求人企業情報", value=st.session_state.hyper_context.get("job", ""), height=130
            )

        st.markdown("##### 📎 ファイル添付（PDF・TXT・画像）")
        uploaded_files = st.file_uploader(
            "添付ファイル",
            accept_multiple_files=True,
            type=["pdf", "txt", "png", "jpg", "jpeg", "webp"],
            key="hyper_uploads",
            label_visibility="collapsed",
        )

        if uploaded_files:
            image_files = []
            text_files = []
            for f in uploaded_files:
                if f.type and f.type.startswith("image/"):
                    image_files.append(f)
                else:
                    text_files.append(f)

            # PDFテキスト抽出 → コンテキストに追記
            if text_files:
                extracted = read_files(text_files)
                st.session_state.hyper_context["seeker"] = (
                    st.session_state.hyper_context.get("seeker", "") + "\n\n" + extracted
                ).strip()
                st.success(f"📄 {len(text_files)}件のファイルからテキストを抽出してコンテキストに追加しました")

            # 画像はセッションに保持（チャット送信時に使用）
            if image_files:
                st.session_state.hyper_images = [
                    {"name": f.name, "bytes": f.getvalue(), "mime": f.type or "image/jpeg"}
                    for f in image_files
                ]
                cols = st.columns(min(len(image_files), 4))
                for idx, f in enumerate(image_files):
                    with cols[idx % 4]:
                        st.image(f, caption=f.name, use_container_width=True)
                st.info(f"🖼️ {len(image_files)}枚の画像を添付済み。次のメッセージ送信時にAIが画像を読み取ります。")

    # ── チャット履歴初期化 ─────────────────────────────────────
    if "hyper_messages" not in st.session_state:
        st.session_state.hyper_messages = [{
            "role": "assistant",
            "content": "私は世界最高峰のエージェント、HYPER-CAIです。引き継いだ情報・添付ファイルを元に、内定までの戦略立案、書類の最終調整、面接対策資料の作成まで、すべてをお手伝いします。何をしましょうか？"
        }]

    # ── サイドバー クイックアクション ─────────────────────────
    st.sidebar.subheader("⚡ クイック・プロ・アクション")
    if st.sidebar.button("🏆 内定獲得の戦略を立案", use_container_width=True):
        st.session_state.hyper_input = "この求職者と企業の情報を分析して、内定を勝ち取るための全体戦略を立てて。"
    if st.sidebar.button("📊 面接対策プレゼンを作成", use_container_width=True):
        st.session_state.hyper_input = "求職者向けの面接対策プレゼン資料（HTML形式）を作成して。"
    if st.sidebar.button("📧 企業への極上推薦文", use_container_width=True):
        st.session_state.hyper_input = "企業担当者が即決で会いたくなるような、プロ視点の推薦文を書いて。"

    # ── チャット表示 ──────────────────────────────────────────
    chat_area = st.container(height=480)
    for msg in st.session_state.hyper_messages:
        with chat_area.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # ── チャット入力処理 ───────────────────────────────────────
    if prompt := st.chat_input("HYPER-CAIに指示を出す..."):
        st.session_state.hyper_messages.append({"role": "user", "content": prompt})
        with chat_area.chat_message("user"):
            st.markdown(prompt)

        with chat_area.chat_message("assistant"):
            with st.spinner("思考中..."):
                context = (
                    f"求職者情報:\n{st.session_state.hyper_context['seeker']}\n\n"
                    f"求人情報:\n{st.session_state.hyper_context['job']}"
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

ユーザーの指示: {prompt}
"""
                try:
                    # 画像が添付されている場合はマルチモーダルで送信
                    pending_images = st.session_state.get("hyper_images", [])
                    if pending_images:
                        contents = []
                        for img in pending_images:
                            contents.append(
                                genai_types.Part.from_bytes(
                                    data=img["bytes"], mime_type=img["mime"]
                                )
                            )
                        contents.append(sys_prompt)
                        resp = safe_generate_content(contents)
                        st.session_state.hyper_images = []  # 送信後クリア
                    else:
                        resp = safe_generate_content(sys_prompt)

                    ai_msg = resp.text
                    st.markdown(ai_msg)
                    st.session_state.hyper_messages.append({"role": "assistant", "content": ai_msg})

                    # HTMLプレゼンが含まれていたらプレビュー表示
                    html_match = re.search(r'<!DOCTYPE html>.*?</html>', ai_msg, re.DOTALL | re.IGNORECASE)
                    if html_match:
                        st.divider()
                        st.subheader("📺 プレゼン資料プレビュー")
                        components.html(html_match.group(), height=520, scrolling=True)
                        st.download_button(
                            "📥 プレゼンHTMLをダウンロード",
                            html_match.group(),
                            file_name="strategy.html",
                            mime="text/html",
                        )

                except Exception as e:
                    st.error(f"エラー: {e}")

    if st.button("🔄 トークをリセット"):
        st.session_state.hyper_messages = []
        st.session_state.hyper_images = []
        st.rerun()
