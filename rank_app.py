import streamlit as st
from google import genai
import re

# ==========================================
# 🎨 カスタムCSSによるデザイン定義（3Dパネル＆エフェクト）
# ==========================================
st.markdown("""
<style>
    /* 全体の背景にデジタルなグリッド線を追加（任意） */
    .stApp {
        background-image: linear-gradient(rgba(10, 25, 47, 0.9), rgba(10, 25, 47, 0.9)),
                          url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%2300e5ff' fill-opacity='0.05'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
    }

    /* 3Dサイバーパネルのスタイル定義 */
    .cyber-panel {
        background: rgba(23, 42, 70, 0.7); /* 半透明の背景 */
        border: 1px solid #00E5FF;       /* 発光する青い枠線 */
        box-shadow: 0 0 20px rgba(0, 229, 255, 0.4), /* 青い光の影（グロー効果） */
                    inset 0 0 10px rgba(0, 229, 255, 0.2); /* 内側の光 */
        border-radius: 10px;
        padding: 20px;
        margin-top: 20px;
        backdrop-filter: blur(5px); /* すりガラス効果 */
        position: relative;
        overflow: hidden; /* スキャンエフェクトがはみ出さないように */
    }

    /* 分析完了時のスキャン光線エフェクト */
    .scan-effect::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: linear-gradient(
            to bottom,
            transparent,
            rgba(0, 229, 255, 0.4) 50%,
            transparent
        );
        transform: rotate(45deg);
        animation: scan 2s ease-in-out forwards; /* 2秒かけてスキャン */
        pointer-events: none; /* 操作の邪魔にならないように */
    }

    @keyframes scan {
        0% { top: -150%; }
        100% { top: 150%; }
    }

    /* メトリック（スコア表示）のスタイル */
    [data-testid="stMetricValue"] {
        font-size: 2rem !important;
        color: #00E5FF !important; /* 数字を青く発光させる */
        text-shadow: 0 0 10px rgba(0, 229, 255, 0.6);
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# ここからメインのPythonコード
# ==========================================

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
# st.secrets を使って、隠された場所からキーを呼び出します
client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

st.set_page_config(page_title="プロ仕様・求職者ランク判定", page_icon=":chart_with_upwards_trend:", layout="wide") # layout="wide"で画面を広く使う
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
if st.button("分析を開始する", type="primary"): # ボタンも目立たせる
    with st.spinner("AIがデータをスキャン中..."): # メッセージもそれっぽく変更
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
                    model='gemini-1.5-flash',
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

            # --- ランク判定ロジック ---
            if total_score >= 18: 
                rank, color_name, rank_color = "S", "🟢 優秀 (S)", "#00ff00"
            elif total_score >= 15: 
                rank, color_name, rank_color = "A", "🔵 良好 (A)", "#00e5ff"
            elif total_score >= 12: 
                rank, color_name, rank_color = "B", "🟡 標準 (B)", "#ffff00"
            elif total_score >= 9: 
                rank, color_name, rank_color = "C", "🟠 要努力 (C)", "#ff9900"
            elif total_score >= 5: 
                rank, color_name, rank_color = "D", "🔴 厳しい (D)", "#ff0000"
            else: 
                rank, color_name, rank_color = "Z", "⚫ 測定不能 (Z)", "#888888"

            # ==========================================
            # 🎨 3Dサイバーパネルでの結果表示
            # ==========================================
            
            # 風船(balloons)は廃止！代わりにCSSスキャンエフェクトを発動
            
            # AI感のある成功メッセージ
            st.markdown(f"""
            <div style="background-color: rgba(0, 229, 255, 0.2); padding: 10px; border-radius: 5px; border-left: 5px solid #00E5FF;">
                ✨ <b>Analysis Complete:</b> AIによる高精度スキャンが完了しました。
            </div>
            """, unsafe_allow_html=True)
            
            # 3Dサイバーパネルのコンテナを作成（ここに scan-effect クラスを付与して光らせる）
            st.markdown("""
            <div class="cyber-panel scan-effect">
            """, unsafe_allow_html=True)

            # --- ここからパネルの中身 ---
            st.markdown("## 📊 AI キャリア分析レポート")
            
            # ランクを大きく表示（文字色もランクに合わせて発光させる）
            st.markdown(f"<h3 style='color: {rank_color}; text-shadow: 0 0 15px {rank_color};'>総合評価: {color_name}</h3>", unsafe_allow_html=True)
            
            st.progress(total_score / 20)
            st.caption(f"獲得スコア: {total_score}点 / 満点: 20点")
            
            st.divider()
            
            # スコアの内訳（数字が青く光るようにCSSで調整済み）
            col1, col2, col3 = st.columns(3)
            col1.metric("👤 基本情報スコア", f"{base_score} pt")
            col2.metric("🤖 AI 実績評価", f"{ai_score} pt")
            col3.metric("⚠️ リスク減点", f"-{short_term * 4} pt", delta_color="inverse")
            
            # --- パネルの終わり ---
            st.markdown("</div>", unsafe_allow_html=True)

            
            # AIからのメッセージ風ブロック
            st.markdown("""
            <div style="margin-top: 20px; padding: 15px; background: rgba(255, 255, 255, 0.05); border-radius: 10px;">
                💡 <b>システム通知:</b> 上記のスコアは、入力されたデータに基づき最新のAIモデルが算出した市場価値の目安です。
            </div>
            """, unsafe_allow_html=True)

        except Exception as e:
            st.error(f"❌ 分析中にエラーが発生しました: {e}")















