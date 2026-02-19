import streamlit as st
import google.generativeai as genai

# --- 1. AIの設定（ここにコピーしたキーを貼り付け） ---
genai.configure(api_key="AIzaSyCYq5C0BMRu1BPHEKaLf4qDc75uQy7DYOw")
model = genai.GenerativeModel('models/gemini-1.5-flash')

st.set_page_config(page_title="求職者ランク判定 AI版", page_icon=":robot_face:")
st.title(":robot_face: AI求職者ランク判定")

# --- 2. 入力エリア ---
with st.sidebar:
    st.header("基本情報")
    age = st.number_input("年齢", 18, 60, 25)
    job_changes = st.number_input("転職回数", 0, 10, 1)
    short_term = st.number_input("短期離職数", 0, 10, 0)

st.subheader("実績の自動分析")
achievement_text = st.text_area("職務経歴・実績を貼り付けてください", placeholder="例：営業として目標120%達成...", height=200)

if st.button("AI分析を開始"):
    if not achievement_text:
        st.warning("実績を入力してください")
    else:
        with st.spinner("AIが実績を分析中..."):
            try:
                # Geminiに判定を依頼
                prompt = f"以下の実績を10点満点で採点し『点数：〇点』とだけ答えて。実績：{achievement_text}"
                response = model.generate_content(prompt)
                
                # 数字だけ抜き出す
                import re
                score_match = re.search(r'\d+', response.text)
                ai_score = int(score_match.group()) if score_match else 5

                # 総合スコア計算
                base_score = 0
                if 20 <= age <= 25: base_score += 5
                elif 26 <= age <= 30: base_score += 3
                if job_changes == 1: base_score += 5
                total_score = base_score + ai_score - (short_term * 4)

                # ランク判定
                if total_score >= 15: rank, color = "S", "red"
                elif total_score >= 11: rank, color = "orange"
                elif total_score >= 7: rank, color = "green"
                else: rank, color = "gray"

                st.balloons()
                st.markdown(f"## 総合判定: :{color}[ランク {rank}]")
                st.write(f"内訳：AI実績スコア {ai_score}点 + 基本スコア {base_score}点 - 減点")
            
            except Exception as e:

                st.error(f"AIエラーが発生しました。APIキーが正しいか確認してください：{e}")
