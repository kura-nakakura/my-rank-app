import streamlit as st
from google import genai
import re

# --- 1. セキュリティ設定 ---
# ログインパスワード
LOGIN_PASSWORD = "HR9237" 

def check_password():
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False
    if st.session_state.password_correct:
        return True

    st.title(":lock: ログインが必要です")
    pwd = st.text_input("パスワードを入力してください", type="password")
    if st.button("ログイン"):
        if pwd == LOGIN_PASSWORD:
            st.session_state.password_correct = True
            st.rerun()
        else:
            st.error("パスワードが正しくありません")
    return False

if not check_password():
    st.stop()

# --- 2. AIの設定 ---
# st.secrets を使って、隠された場所からキーを呼び出します（安全な状態です！）
client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

st.set_page_config(page_title="プロ仕様・求職者ランク判定", page_icon=":chart_with_upwards_trend:")
st.title(":chart_with_upwards_trend: 求職者ランク判定プロ")

# --- 3. 分析モード選択 ---
mode = st.radio(
    "分析モードを選択してください",
    ["1. 簡易分析（基本情報のみ）", "2. 通常分析（実績AI判定あり）", "3. 詳細分析（資料添付あり）"],
    horizontal=True
)

# --- 4. 入力エリア ---
with st.sidebar:
    st.header(":bust_in_silhouette: 基本情報入力")
    age = st.number_input("年齢", 18, 65, 25)
    job_changes = st.number_input("転職回数", 0, 15, 1)
    short_term = st.number_input("短期離職数", 0, 10, 0)

achievement_text = ""
uploaded_files = []

if mode == "2. 通常分析（実績AI判定あり）":
    achievement_text = st.text_area("職務経歴・実績", placeholder="例：営業でMVP獲得...", height=150)

elif mode == "3. 詳細分析（資料添付あり）":
    achievement_text = st.text_area("追加の実績・補足事項（任意）", height=100)
    uploaded_files = st.file_uploader("履歴書・職務経歴書・企業資料を添付", accept_multiple_files=True, type=['pdf', 'txt'])

# --- 5. 判定ロジック ---
if st.button("分析を開始する"):
    with st.spinner("プロの視点で分析中..."):
        try:
            ai_score = 5  # デフォルト値
            
            # モードに応じたAIプロンプト
            if mode != "1. 簡易分析（基本情報のみ）":
                
                file_contents = ""
                if mode == "3. 詳細分析（資料添付あり）" and uploaded_files:
                    for file in uploaded_files:
                        if file.name.endswith('.txt'):
                            file_contents += file.getvalue().decode("utf-8") + "\n"

                if mode == "2. 通常分析（実績AI判定あり）":
                    prompt = f"キャリアアドバイザーとして以下の実績を厳しく10点満点で採点し、『点数：〇点』とだけ答えて。実績：{achievement_text}"
                else:
                    prompt = f"資料と実績に基づき、求職者の市場価値を10点満点で採点し『点数：〇点』とだけ答えて。実績：{achievement_text}\n資料内容：\n{file_contents}"
                
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt
                )
                
                score_match = re.search(r'\d+', response.text)
                if score_match:
                    ai_score = int(score_match.group())

            # 総合スコア計算
            base_score = 0
            if 22 <= age <= 35: base_score += 5
            if job_changes <= 2: base_score += 5
            
            total_score = base_score + ai_score - (short_term * 4)

            # --- 修正後のランク判定ロジック ---
            if total_score >= 18: 
                rank, color_name = "S", "🟢 優秀 (S)"
            elif total_score >= 15: 
                rank, color_name = "A", "🔵 良好 (A)"
            elif total_score >= 12: 
                rank, color_name = "B", "🟡 標準 (B)"
            elif total_score >= 9: 
                rank, color_name = "C", "🟠 要努力 (C)"
            elif total_score >= 5: 
                rank, color_name = "D", "🔴 厳しい (D)"
            else: 
                rank, color_name = "Z", "⚫ 測定不能 (Z)"

            # ==========================================
            # 🎨 ここから下が見た目をかっこよくした表示UI
            # ==========================================
            st.balloons()
            st.divider() # かっこいい区切り線
            
            # AI感のある成功メッセージ
            st.success("✨ AIによる高精度分析が完了しました。")
            
            # 枠線付きのコンテナで結果を囲む（ダッシュボード感）
            with st.container(border=True):
                st.markdown("## 📊 AI キャリア分析レポート")
                
                # ランクを大きく色付きで表示
                st.markdown(f"### 総合評価: **{color_name}**")
                st.progress(total_score / 20) # スコアのゲージ（プログレスバー）を表示
                st.caption(f"獲得スコア: {total_score}点 / 満点: 20点")
                
                st.divider()
                
                # スコアの内訳を3列でスタイリッシュに表示
                col1, col2, col3 = st.columns(3)
                col1.metric("👤 基本情報スコア", f"{base_score} pt")
                col2.metric("🤖 AI 実績評価", f"{ai_score} pt")
                col3.metric("⚠️ リスク減点", f"-{short_term * 4} pt", delta_color="inverse")
            
            # AIからのメッセージ風ブロック
            st.info("💡 **システム通知:** 上記のスコアは、入力されたデータに基づき最新のAIモデルが算出した市場価値の目安です。")

        except Exception as e:
            st.error(f"❌ 分析中にエラーが発生しました: {e}")













