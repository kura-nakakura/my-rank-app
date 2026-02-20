import streamlit as st
from google import genai
import re

# ==========================================
# 🎨 カスタムCSSによるデザイン定義
# ==========================================
st.markdown("""
<style>
    .stApp {
        background-image: linear-gradient(rgba(10, 25, 47, 0.9), rgba(10, 25, 47, 0.9)),
                          url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%2300e5ff' fill-opacity='0.05'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
    }
    .cyber-panel {
        background: rgba(23, 42, 70, 0.7);
        border: 1px solid #00E5FF;
        box-shadow: 0 0 20px rgba(0, 229, 255, 0.4), inset 0 0 10px rgba(0, 229, 255, 0.2);
        border-radius: 10px;
        padding: 25px;
        margin-top: 20px;
        backdrop-filter: blur(5px);
        position: relative;
        overflow: hidden;
    }
    .scan-effect::before {
        content: '';
        position: absolute;
        top: -50%; left: -50%; width: 200%; height: 200%;
        background: linear-gradient(to bottom, transparent, rgba(0, 229, 255, 0.4) 50%, transparent);
        transform: rotate(45deg);
        animation: scan 2.5s ease-in-out forwards;
        pointer-events: none;
    }
    @keyframes scan {
        0% { top: -150%; }
        100% { top: 150%; }
    }
    [data-testid="stMetricValue"] {
        font-size: 2rem !important;
        color: #00E5FF !important;
        text-shadow: 0 0 10px rgba(0, 229, 255, 0.6);
    }
    .fb-box {
        background: rgba(255, 255, 255, 0.05);
        border-left: 4px solid #00E5FF;
        padding: 15px;
        margin-bottom: 15px;
        border-radius: 0 5px 5px 0;
    }
</style>
""", unsafe_allow_html=True)

# --- 1. セキュリティ設定 ---
LOGIN_PASSWORD = "HR9237" 

def check_password():
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False
    if st.session_state.password_correct: return True

    st.title(":lock: ログインが必要です")
    pwd = st.text_input("パスワードを入力してください", type="password")
    if st.button("ログイン"):
        if pwd == LOGIN_PASSWORD:
            st.session_state.password_correct = True
            st.rerun()
        else:
            st.error("パスワードが正しくありません")
    return False

if not check_password(): st.stop()

# --- 2. AIの設定 ---
client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

st.set_page_config(page_title="プロ仕様・求職者ランク判定", page_icon=":chart_with_upwards_trend:", layout="wide")
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
    
    # ★追加：志望業種・職種の入力エリア
    st.divider()
    st.header(":office: 志望企業情報")
    target_industry = st.text_input("志望業種", placeholder="例：IT、メーカー、商社など", value="IT/Web業界")
    target_job = st.text_input("志望職種", placeholder="例：エンジニア、営業、経理など", value="職種全般")

achievement_text = ""
uploaded_files = []

if mode == "2. 通常分析（実績AI判定あり）":
    achievement_text = st.text_area("職務経歴・実績", placeholder="例：営業でMVP獲得...", height=150)
elif mode == "3. 詳細分析（資料添付あり）":
    achievement_text = st.text_area("追加の実績・補足事項（任意）", height=100)
    uploaded_files = st.file_uploader("履歴書・職務経歴書・企業資料を添付", accept_multiple_files=True, type=['pdf', 'txt'])

# --- 5. 判定ロジック ---
if st.button("分析を開始する", type="primary"):
    with st.spinner("AIがデータをディープスキャン中..."):
        try:
            ai_score = 5  
            reason_text = "簡易分析のためフィードバックはありません。"
            advice_text = "詳細なアドバイスは通常分析以上をご利用ください。"
            
            if mode != "1. 簡易分析（基本情報のみ）":
                file_contents = ""
                if mode == "3. 詳細分析（資料添付あり）" and uploaded_files:
                    for file in uploaded_files:
                        if file.name.endswith('.txt'):
                            file_contents += file.getvalue().decode("utf-8") + "\n"

                # ★変更：業種・職種を変数としてAIに読み込ませる
                base_prompt = f"""あなたはプロの厳格なキャリアアドバイザーです。
今回は【{target_industry}】の【{target_job}】への転職を希望する求職者を評価します。
以下の求職者の実績や資料を読み込み、志望する業界・職種の市場価値を基準に、10点満点で厳しく採点してください。
必ず以下のフォーマット通りに、3つの項目を明確に分けて出力してください。

【点数】
(0〜10の数字のみ)

【評価理由】
(なぜその点数になったのか、その業界・職種のプロ目線での具体的な理由。強みと弱みを含めること)

【改善アドバイス】
(履歴書や職務経歴書のどこを修正すべきか、面接で何をアピールすべきかの具体的な助言)

---
実績・補足事項：{achievement_text}
"""
                if mode == "3. 詳細分析（資料添付あり）":
                    prompt = base_prompt + f"\n資料内容：\n{file_contents}"
                else:
                    prompt = base_prompt
                
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt
                )
                
                full_text = response.text
                
                score_match = re.search(r'【点数】\s*(\d+)', full_text)
                if score_match:
                    ai_score = int(score_match.group(1))
                elif re.search(r'\d+', full_text):
                    ai_score = int(re.search(r'\d+', full_text).group())

                if "【評価理由】" in full_text and "【改善アドバイス】" in full_text:
                    try:
                        reason_text = full_text.split("【評価理由】")[1].split("【改善アドバイス】")[0].strip()
                        advice_text = full_text.split("【改善アドバイス】")[1].strip()
                    except:
                        reason_text = full_text
                        advice_text = "出力形式エラーのため抽出できませんでした。"
                else:
                    reason_text = full_text
                    advice_text = "（AIが指定フォーマットを返しませんでした）"

            # 総合スコア計算
            base_score = 0
            if 22 <= age <= 35: base_score += 5
            if job_changes <= 2: base_score += 5
            total_score = base_score + ai_score - (short_term * 4)

            # ランク判定
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
            st.markdown(f"""
            <div style="background-color: rgba(0, 229, 255, 0.2); padding: 10px; border-radius: 5px; border-left: 5px solid #00E5FF;">
                ✨ <b>Analysis Complete:</b> 【{target_industry} / {target_job}】専門AIによるスキャンが完了しました。
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown('<div class="cyber-panel scan-effect">', unsafe_allow_html=True)

            st.markdown("## 📊 AI キャリア分析レポート")
            st.markdown(f"<h3 style='color: {rank_color}; text-shadow: 0 0 15px {rank_color};'>総合評価: {color_name}</h3>", unsafe_allow_html=True)
            st.progress(max(0, min(total_score / 20, 1.0)))
            st.caption(f"獲得スコア: {total_score}点 / 満点: 20点")
            
            col1, col2, col3 = st.columns(3)
            col1.metric("👤 基本情報スコア", f"{base_score} pt")
            col2.metric("🤖 AI 実績評価", f"{ai_score} pt")
            col3.metric("⚠️ リスク減点", f"-{short_term * 4} pt", delta_color="inverse")
            
            st.divider()

            st.markdown("#### 📝 AI 評価理由")
            st.markdown(f'<div class="fb-box">{reason_text}</div>', unsafe_allow_html=True)

            st.markdown("#### 💡 履歴書・面接改善アドバイス")
            st.markdown(f'<div style="background: rgba(0, 255, 0, 0.05); border-left: 4px solid #00ff00; padding: 15px; border-radius: 0 5px 5px 0;">{advice_text}</div>', unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

            # エージェント向け内部アラート
            if total_score < 12: 
                st.markdown("""
                <div style="margin-top: 20px; padding: 15px; border-radius: 10px; background-color: rgba(255, 50, 50, 0.15); border: 1px solid #ff3333;">
                    🚨 <b>【エージェント向け内部アラート】対応優先度：低</b><br>
                    総合評価がCランク以下です。スキルや経歴の深掘り・書類添削に時間がかかる可能性が高いため、リソース配分に注意してください。
                </div>
                """, unsafe_allow_html=True)
            else: 
                st.markdown("""
                <div style="margin-top: 20px; padding: 15px; border-radius: 10px; background-color: rgba(0, 255, 100, 0.15); border: 1px solid #00ff66;">
                    🔥 <b>【エージェント向け内部アラート】対応優先度：高</b><br>
                    総合評価がBランク以上の有望な求職者です！他社に流れる前に、優先的な面談設定と優良案件の打診を推奨します。
                </div>
                """, unsafe_allow_html=True)

        except Exception as e:
            st.error(f"❌ 分析中にエラーが発生しました: {e}")



















