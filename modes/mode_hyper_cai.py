import streamlit as st
import streamlit.components.v1 as components
import json
import re
from utils import safe_generate_content, read_files, create_google_doc

def show():
    # ==========================================
    # ✨ HYPER-CAI-pro 専用のVIPデザイン（ブラック＆ゴールド）
    # ==========================================
    st.markdown("""
        <style>
        /* 1. 背景を通常の動画から「漆黒と黄金のグラデーション」で完全に上書き */
        .stApp {
            background: radial-gradient(circle at top, #2b2200 0%, #0a0a0a 50%, #000000 100%) !important;
            background-color: #000000 !important;
            background-image: none !important; /* 通常の背景画像を消す */
        }
        
        /* 2. ヘッダーも馴染ませる */
        header { background-color: transparent !important; }

        /* 3. チャットの吹き出しを高級感のあるダークゴールドに */
        div[data-testid="stChatMessage"] {
            background: linear-gradient(145deg, rgba(30, 25, 5, 0.9) 0%, rgba(10, 10, 10, 0.95) 100%) !important;
            border: 1px solid rgba(255, 215, 0, 0.4) !important;
            box-shadow: 0 4px 15px rgba(255, 215, 0, 0.05) !important;
            border-radius: 12px !important;
            color: #f3f0df !important;
        }

        /* 4. アコーディオン（エクスパンダー）の枠もプロ仕様に */
        [data-testid="stExpander"] {
            background-color: rgba(20, 20, 20, 0.8) !important;
            border: 1px solid rgba(255, 215, 0, 0.3) !important;
            border-radius: 10px !important;
        }
        [data-testid="stExpander"] p, [data-testid="stExpander"] span {
            color: #FFD700 !important; /* 文字をゴールドに */
        }
        
        /* 5. ボタンを圧倒的なゴールドグラデーションに！ */
        .stButton>button {
            background: linear-gradient(135deg, #FFD700 0%, #DAA520 100%) !important;
            color: #000000 !important;
            border: none !important;
            box-shadow: 0 4px 15px rgba(255, 215, 0, 0.4) !important;
            font-weight: 900 !important;
            border-radius: 8px !important;
            transition: all 0.3s ease;
        }
        .stButton>button:hover {
            box-shadow: 0 6px 25px rgba(255, 215, 0, 0.7) !important;
            transform: translateY(-2px);
        }

        /* 6. タイトルの装飾 */
        .hyper-title {
            text-align: center; color: #FFD700; font-size: 48px; font-weight: 900;
            text-shadow: 0 0 30px rgba(255, 215, 0, 0.6); margin-bottom: 10px;
            font-family: 'Helvetica Neue', sans-serif; letter-spacing: 2px;
        }
        </style>
        <div class="hyper-title">✨ HYPER-CAI-pro ✨</div>
        <p style="text-align: center; color: #FFD700;">世界最高峰のキャリアアドバイザーAI</p>
    """, unsafe_allow_html=True)

    # 1. コンテキスト（引き継ぎ情報）の確認
    if "hyper_context" not in st.session_state:
        st.session_state.hyper_context = {"seeker": "", "job": "", "history": ""}

    with st.expander("📥 現在引き継がれている情報（コンテキスト）"):
        c1, c2 = st.columns(2)
        with c1:
            st.session_state.hyper_context["seeker"] = st.text_area("求職者情報", value=st.session_state.hyper_context.get("seeker", ""), height=150)
        with c2:
            st.session_state.hyper_context["job"] = st.text_area("求人企業情報", value=st.session_state.hyper_context.get("job", ""), height=150)

    # 2. チャット履歴の初期化
    if "hyper_messages" not in st.session_state:
        st.session_state.hyper_messages = [{"role": "assistant", "content": "私は世界最高峰のエージェント、HYPER-CAIです。引き継いだ情報を元に、内定までの戦略立案、書類の最終調整、面接対策資料の作成まで、すべてをお手伝いします。何をしましょうか？"}]

    # 3. チャット表示（背景グレー仕様）
    st.markdown("<style>div[data-testid='stChatMessage'] { background-color: rgba(30, 35, 45, 0.98) !important; }</style>", unsafe_allow_html=True)
    
    chat_area = st.container(height=500)
    for msg in st.session_state.hyper_messages:
        with chat_area.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # 4. 操作パネル
    st.sidebar.subheader("⚡ クイック・プロ・アクション")
    if st.sidebar.button("🏆 内定獲得の戦略を立案"):
        st.session_state.hyper_input = "この求職者と企業の情報を分析して、内定を勝ち取るための全体戦略を立てて。"
    if st.sidebar.button("📊 面接対策プレゼンを作成"):
        st.session_state.hyper_input = "求職者向けの面接対策プレゼン資料（HTML形式）を作成して。"
    if st.sidebar.button("📧 企業への極上推薦文"):
        st.session_state.hyper_input = "企業担当者が即決で会いたくなるような、プロ視点の推薦文を書いて。"

    # 5. チャット入力処理
    if prompt := st.chat_input("HYPER-CAIに指示を出す..."):
        st.session_state.hyper_messages.append({"role": "user", "content": prompt})
        with chat_area.chat_message("user"):
            st.markdown(prompt)

        with chat_area.chat_message("assistant"):
            with st.spinner("思考中..."):
                context = f"求職者情報: {st.session_state.hyper_context['seeker']}\n求人情報: {st.session_state.hyper_context['job']}"
                history = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.hyper_messages[-5:]])
                
                sys_prompt = f"""
あなたは世界最高峰のキャリアアドバイザーAI「HYPER-CAI-pro」です。
【コンテキスト】
{context}
【会話履歴】
{history}

【あなたの任務】
1. 圧倒的な分析力で求職者を内定に導く。
2. プレゼン作成を依頼されたら、必ず Mckinsey/BCGスタイルの洗練された「1枚の完結したHTML」を出力する。
3. 文体は極めてプロフェッショナルで、かつエージェントの熱意が伝わるものにする。
4. 最後に必ず「次の推奨アクション」を3つ提示する。

【プレゼン資料作成の絶対ルール】
プレゼン資料を要求された場合、必ず以下のHTML/CSS/JSテンプレート構造を使用し、ボタンで切り替わる「複数ページ（スライド型）」のプレゼンを出力してください。
デザインはMckinsey/BCGのような高級感ある色合いを基調とすること。
スライドは必ず5枚以上（例：1.タイトル 2.現状分析 3.強み 4.面接対策 5.まとめ）作成し、それぞれの `<div class="slide">` の中にコンテンツを入れてください。

```html
<!DOCTYPE html>
<html lang="ja">
<head>
<style>
  body {{ margin:0; font-family:'Helvetica Neue', sans-serif; background:#e2e8f0; overflow:hidden; }}
  .slide {{ display:none; flex-direction:column; justify-content:flex-start; height:100vh; padding:60px 80px; background:#f8fafc; box-sizing:border-box; position:relative; }}
  .slide.active {{ display:flex; animation: fadeIn 0.5s ease-in-out; }}
  @keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(10px); }} to {{ opacity: 1; transform: translateY(0); }} }}
  
  /* 装飾デザイン */
  .slide::before {{ content: ''; position: absolute; top: 0; right: 0; width: 300px; height: 100%; background: linear-gradient(135deg, rgba(0, 80, 136, 0.05) 0%, rgba(17, 202, 160, 0.05) 100%); clip-path: polygon(100% 0, 0 0, 100% 100%); z-index: 0; }}
  .slide > * {{ position: relative; z-index: 1; }}

  h1 {{ color:#005088; font-size:60px; margin-bottom:20px; margin-top:20vh; text-align:center; }}
  h2 {{ color:#005088; font-size:45px; border-left:8px solid #11caa0; padding-left:20px; width:100%; margin-top:0; }}
  h3 {{ color:#005088; font-size:30px; margin-top:30px; }}
  .content {{ flex-grow:1; width:100%; font-size:24px; color:#333; line-height:1.6; display:flex; flex-direction:column; }}
  
  .controls {{ position:fixed; bottom:30px; left:50%; transform:translateX(-50%); display:flex; gap:20px; z-index:1000; }}
  button {{ padding:12px 30px; font-size:18px; font-weight:bold; cursor:pointer; background:#005088; color:white; border:none; border-radius:30px; box-shadow:0 4px 10px rgba(0,0,0,0.3); transition:all 0.2s; }}
  button:hover {{ background:#11caa0; transform:translateY(-2px); }}
  .slide-number {{ position:absolute; bottom:30px; right:40px; font-size:20px; color:#005088; font-weight:bold; }}
</style>
</head>
<body>
  <div id="slides-container">
    <div class="slide active">
      <h1>[タイトル]</h1>
      <p style="text-align:center; font-size:28px; color:#11caa0;">[サブタイトル / 対象者名]</p>
      <div class="slide-number">1</div>
    </div>
    
    <div class="slide">
      <h2>[スライド見出し]</h2>
      <div class="content">
        [具体的な分析内容や箇条書き]
      </div>
      <div class="slide-number">2</div>
    </div>
    </div>
  
  <div class="controls">
    <button onclick="prevSlide()">◀ 前へ</button>
    <button onclick="nextSlide()">次へ ▶</button>
  </div>

  <script>
    let current = 0;
    const slides = document.querySelectorAll('.slide');
    function showSlide(n) {{
       slides.forEach(s => s.classList.remove('active'));
       current = (n + slides.length) % slides.length;
       slides[current].classList.add('active');
    }}
    function nextSlide() {{ showSlide(current + 1); }}
    function prevSlide() {{ showSlide(current - 1); }}
  </script>
</body>
</html>
"""
                resp = safe_generate_content(sys_prompt)
                ai_msg = resp.text
                st.markdown(ai_msg)
                st.session_state.hyper_messages.append({"role": "assistant", "content": ai_msg})

                # HTMLプレゼンが含まれていればプレビューを表示
                html_match = re.search(r'<!DOCTYPE html>.*?</html>', ai_msg, re.DOTALL | re.IGNORECASE)
                if html_match:
                    st.divider()
                    st.subheader("📺 プレゼン資料プレビュー")
                    components.html(html_match.group(), height=500, scrolling=True)
                    st.download_button("📥 プレゼンHTMLをダウンロード", html_match.group(), file_name="strategy.html", mime="text/html")

    if st.button("🔄 トークをリセット"):
        st.session_state.hyper_messages = []
        st.rerun()