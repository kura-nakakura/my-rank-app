import streamlit as st
import google.generativeai as genai
import re

# --- 1. セキュリティ設定 ---
# ログインパスワード（好きなものに変えてください）
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
# エラー回避のため、モデル名は 'gemini-1.5-flash' を使用
genai.configure(api_key="AIzaSyDb1MX4vLFgPvcUlsalcE59VnSvrRULjC8")
model = genai.GenerativeModel('gemini-1.5-flash')

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
                if mode == "2. 通常分析（実績AI判定あり）":
                    prompt = f"キャリアアドバイザーとして以下の実績を厳しく10点満点で採点し、『点数：〇点』とだけ答えて。実績：{achievement_text}"
                else:
                    prompt = f"資料と実績に基づき、求職者の市場価値を10点満点で採点し『点数：〇点』とだけ答えて。実績：{achievement_text}"
                
                response = model.generate_content(prompt)
                score_match = re.search(r'\d+', response.text)
                if score_match:
                    ai_score = int(score_match.group())

            # 総合スコア計算（ロジックの調整）
            base_score = 0
            if 22 <= age <= 35: base_score += 5
            if job_changes <= 2: base_score += 5
            
            total_score = base_score + ai_score - (short_term * 4)

            # S〜Zランク判定（20点満点想定）
            if total_score >= 18: rank, color = "S", "red"
            elif total_score >= 15: rank, color = "orange" # A
            elif total_score >= 12: rank, color = "yellow" # B
            elif total_score >= 9: rank, color = "green"  # C
            elif total_score >= 5: rank, color = "blue"   # D
            else: rank, color = "gray" # Z

            # 表示
            st.balloons()
            st.subheader("分析結果")
            st.markdown(f"### 総合評価: :{color}[ランク {rank}] （{total_score}点 / 20点）")
            
            col1, col2, col3 = st.columns(3)
            col1.metric("基本スコア", f"{base_score}点")
            col2.metric("AI実績スコア", f"{ai_score}点")
            col3.metric("マイナス評価", f"-{short_term * 4}点")

        except Exception as e:
            st.error(f"エラーが発生しました。設定を確認してください：{e}")


