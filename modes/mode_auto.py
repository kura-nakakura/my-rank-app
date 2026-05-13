import streamlit as st
import re
import time

from utils import (
    safe_generate_content,
    read_files,
    get_url_text,
    get_section,
    create_google_doc,
    export_to_spreadsheet,
    AGENT_LIST,
)


def _calc_rank(age, job_changes, short_term):
    if age < 20:
        age_s = -8
    elif 20 <= age <= 21:
        age_s = 8
    elif 22 <= age <= 25:
        age_s = 10
    elif 26 <= age <= 29:
        age_s = 8
    elif 30 <= age <= 35:
        age_s = 7
    else:
        age_s = 5

    job_bonus = 0
    if age <= 24 and job_changes == 0:
        job_bonus = 10
    elif 25 <= age <= 29 and job_changes <= 1:
        job_bonus = 10
    elif 25 <= age <= 29 and job_changes <= 2:
        job_bonus = 7
    elif 30 <= age <= 35 and job_changes <= 2:
        job_bonus = 10
    elif 30 <= age <= 35 and job_changes <= 3:
        job_bonus = 7
    elif 35 <= age <= 85 and job_changes <= 2:
        job_bonus = 10
    elif 35 <= age <= 85 and job_changes <= 3:
        job_bonus = 7
    elif 50 <= age <= 85 and job_changes <= 4:
        job_bonus = 5
    elif job_changes <= 1:
        job_bonus = 5

    job_penalty = 0
    if job_changes == 2:
        job_penalty = -5
    elif job_changes == 3:
        job_penalty = -10
    elif job_changes >= 5:
        job_penalty = -20

    total = age_s + job_bonus + job_penalty - (short_term * 10) + 5

    if total >= 23:
        return total, "優秀 (Class-S)", "#00ff00"
    elif total >= 18:
        return total, "良好 (Class-A)", "#00e5ff"
    elif total >= 13:
        return total, "標準 (Class-B)", "#ffff00"
    elif total >= 8:
        return total, "要努力 (Class-C)", "#ff9900"
    else:
        return total, "測定不能 (Class-Z)", "#ff0000"


def show():
    st.title("🤖 自動化モード — 全工程一括実行")
    st.markdown(
        "面談情報・履歴書・求人票を入力するだけで、**ランク判定 → カルテ作成 → 書類生成 → 書類審査** まで自動で実行します。"
    )
    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("👤 求職者情報")
        u_files_memo = st.file_uploader(
            "面談メモ / 文字起こし (PDF/TXT)",
            accept_multiple_files=True,
            key="auto_memo_up",
        )
        raw_memo = st.text_area(
            "面談メモ・テキスト貼り付け",
            height=160,
            placeholder="ここにテキストをペースト、または手書きメモを入力してください...",
            key="auto_memo_text",
        )
        u_files_resume = st.file_uploader(
            "履歴書・職務経歴書 (PDF/TXT)",
            accept_multiple_files=True,
            key="auto_resume_up",
        )

    with col2:
        st.subheader("🏢 応募企業情報")
        corp_url = st.text_input(
            "🔗 求人票URL（自動読み取り）",
            placeholder="https://...",
            key="auto_corp_url",
        )
        u_files_corp = st.file_uploader(
            "求人票など (PDF/TXT)",
            accept_multiple_files=True,
            key="auto_corp_up",
        )
        corp_text = st.text_area(
            "求人内容・補足メモ",
            height=160,
            placeholder="求人票の内容や補足情報を貼り付けてください...",
            key="auto_corp_text",
        )

    agent_name = st.text_input(
        "アドバイザー名（推薦文・スプレッドシートに使用）",
        placeholder="山田 太郎",
        key="auto_agent",
    )

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("🚀 AI自動分析スタート", type="primary", use_container_width=True):
        memo_text = (read_files(u_files_memo) if u_files_memo else "") + "\n" + raw_memo
        resume_text = read_files(u_files_resume) if u_files_resume else ""
        corp_file_text = read_files(u_files_corp) if u_files_corp else ""
        corp_url_text = get_url_text(corp_url) if corp_url else ""
        corp_all = corp_text + "\n" + corp_file_text + "\n" + corp_url_text
        seeker_all = memo_text + "\n" + resume_text

        if not seeker_all.strip():
            st.warning("面談メモまたは履歴書を入力してください。")
            st.stop()

        # ── Step 1: 求職者情報抽出 ───────────────────────────
        with st.status("⏳ Step 1/3: 求職者情報を解析中...", expanded=True) as status:
            prompt1 = f"""
あなたは優秀なキャリアアドバイザーのアシスタントです。
以下の「面談データ・履歴書」から求職者情報を抽出してください。
情報が語られていない項目は「不明」または「記載なし」と記載してください。

【入力データ】
{seeker_all}

【抽出フォーマット（絶対厳守）】
【面談日】
(YYYY/MM/DD形式)
【エージェント名】
(必ず以下のリストから完全一致で選択、該当なしは「その他」：{AGENT_LIST})
【求職者名】
【生年月日・年齢】
【年齢数字】
(数字のみ。例：28)
【転職回数】
(数字のみ。在職中も含めた合計社数-1)
【短期離職数】
(数字のみ。1年以内の離職回数)
【応募企業名】
【保有資格】
【現在の勤務状況】
【エージェント面談の認識】
【エージェントの利用経験】
【職務経歴】
(経験社数分、以下の8項目を箇条書きで詳細に抽出)
■会社名：
・雇用形態：
・部署／役職：
・職種：
・主な業務内容：
・入社理由：
・実績や成果：
・退職理由：
【転職を考えたきっかけ】
【今回の転職で叶えたいこと】
【入社後どうなっていたいか】
【自分の強み】
【強みエピソード】
【弱み】
【自分の弱みエピソード】
【希望職種・業務】
【希望勤務地】
【現在年収・給与】
【希望年収・給与】
【勤務時間・休日】
【社風・雰囲気】
【入社希望日】
【確認事項や不安ごと】
【次回面談日】
【次回面談時間】
"""
            try:
                resp1 = safe_generate_content(prompt1)
                res1 = resp1.text
                status.update(label="✅ Step 1: 求職者情報の解析完了", state="complete")
            except Exception as e:
                st.error(f"Step 1 エラー: {e}")
                st.stop()

        # ランク計算
        age_raw = get_section("年齢数字", res1)
        age_m = re.search(r"\d+", age_raw)
        age = int(age_m.group()) if age_m else 25

        jc_raw = get_section("転職回数", res1)
        jc_m = re.search(r"\d+", jc_raw)
        job_changes = int(jc_m.group()) if jc_m else 0

        st_raw = get_section("短期離職数", res1)
        st_m = re.search(r"\d+", st_raw)
        short_term = int(st_m.group()) if st_m else 0

        total, rank_name, rank_color = _calc_rank(age, job_changes, short_term)

        seeker_name = get_section("求職者名", res1)
        agent_extracted = get_section("エージェント名", res1)
        interview_date = get_section("面談日", res1)

        # ── Step 2: 書類生成 ──────────────────────────────────
        with st.status("⏳ Step 2/3: 書類を生成中...", expanded=True) as status:
            prompt2 = f"""
あなたは人材紹介会社のプロキャリアライター兼採用目線の職務経歴書編集者です。
提供された情報を深く分析し、企業が「ぜひ会ってみたい」と思える書類を作成してください。

【企業情報】
{corp_all if corp_all.strip() else "（未入力）"}

【求職者情報】
{seeker_all}

【重要ルール】
- 実際の経験・業務内容・成果を具体的に抽出し書類に反映。架空の経験は絶対に書かない。
- 以下の【】セクションをすべて省略せず出力すること。

【評価】
(S最高/A良き！/Bいい感じ/C要努力/Z測定不能のみ)
【理由とアドバイス】
(評価の理由と面接での深掘りポイント)
【職務経歴】
1. 作成日・氏名
2. 各社ごとに以下の構成：
   ■会社名：
   雇用形態：
   事業内容：
   役職：
   ▼業務内容
   ・5〜7行で具体的に。文末は体言止め（〇〇を実施。〇〇を担当。〇〇に貢献。）
   ▼成果
   ・数値・改善・貢献を具体的に。文末は「〇〇を実現し、〇〇％改善。」のように言い切る。
【自己PR】
- 企業に最適化。400字。事実のみ。段落分けあり。敬体（です・ます）。
【志望動機】
- 企業ならではの理由を深掘り。450字。段落分けあり。
"""
            try:
                resp2 = safe_generate_content(prompt2)
                res2 = resp2.text
                status.update(label="✅ Step 2: 書類生成完了", state="complete")
            except Exception as e:
                st.error(f"Step 2 エラー: {e}")
                st.stop()

        doc_score = get_section("評価", res2)
        doc_advice = get_section("理由とアドバイス", res2)
        hist = get_section("職務経歴", res2)
        pr = get_section("自己PR", res2)
        motive = get_section("志望動機", res2)
        combined_doc = f"{hist}\n\n■自己PR\n{pr}"

        # ── Step 3: 書類審査・推薦文 ─────────────────────────
        has_match = False
        ms = 0
        rec_letter = match_advice = interview_prep = ""

        with st.status("⏳ Step 3/3: 書類審査・推薦文を生成中...", expanded=True) as status:
            if corp_all.strip():
                adv = agent_name if agent_name else "担当者"
                prompt3 = f"""
あなたは凄腕ヘッドハンター兼採用担当者です。
企業要件と求職者書類を照らし合わせ、マッチ度を算出し推薦メールを作成してください。

企業情報：{corp_all}
求職者書類：{combined_doc}
志望動機：{motive}

【絶対ルール】以下の4つの【】見出しのみ使用してください。

【マッチ度】
(0〜100の数字のみ)
【書類修正アドバイス】
(通過率を上げるための具体的な修正点)
【面接対策】
(想定質問と回答の方向性)
【推薦文】
(企業名) 採用ご担当者様
お世話になっております。キャリアアドバイザーの株式会社ライフアップの{adv}です。
この度、{seeker_name}様を推薦させていただきたく、ご連絡申し上げました。

■推薦理由
・(応募企業に活かせる強み)
・(貢献できる理由)
・(懸念点払拭があれば)
(人柄や熱意も含め200-300字程度、AI記号「」などは禁止)

ぜひ一度、面接にてご本人とお話しいただけますと幸いです。
何卒ご検討のほど、よろしくお願い申し上げます。
"""
                try:
                    resp3 = safe_generate_content(prompt3)
                    res3 = resp3.text
                    match_raw = get_section("マッチ度", res3)
                    ms = int(re.search(r"\d+", match_raw).group()) if re.search(r"\d+", match_raw) else 0
                    rec_letter = get_section("推薦文", res3)
                    match_advice = get_section("書類修正アドバイス", res3)
                    interview_prep = get_section("面接対策", res3)
                    has_match = True
                    status.update(label="✅ Step 3: 書類審査・推薦文完了", state="complete")
                except Exception as e:
                    st.error(f"Step 3 エラー: {e}")
                    status.update(label="⚠️ Step 3: エラーが発生しました", state="error")
            else:
                status.update(label="⚠️ Step 3: 企業情報なしのためスキップ", state="complete")

        # ══════════════════════════════════════════
        # 分析結果表示
        # ══════════════════════════════════════════
        st.divider()
        st.header("📊 分析結果")

        # 結果 1: ランク判定
        with st.expander("1️⃣ ランク判定結果", expanded=True):
            st.markdown(
                f'<div class="cyber-panel">'
                f'<h3>判定結果: <span style="color:{rank_color};">{rank_name}</span></h3>'
                f'<p>年齢：{age}歳 ／ 転職回数：{job_changes}回 ／ 短期離職：{short_term}回</p>'
                f'</div>',
                unsafe_allow_html=True,
            )
            if total >= 15:
                st.success("NICE❕ **【エージェント指示】** 優先度：高")
            elif 7 <= total < 15:
                st.info("safe **【エージェント指示】** 優先度：中")
            else:
                st.error("🚨 **【エージェント指示】** 優先度：低")

        # 結果 2: カルテ情報
        with st.expander("2️⃣ カルテ情報（抽出結果）", expanded=False):
            carte_fields = [
                ("面談日", interview_date),
                ("エージェント名", agent_extracted),
                ("求職者名", seeker_name),
                ("生年月日・年齢", get_section("生年月日・年齢", res1)),
                ("転職回数", str(job_changes)),
                ("短期離職数", str(short_term)),
                ("保有資格", get_section("保有資格", res1)),
                ("現在の勤務状況", get_section("現在の勤務状況", res1)),
                ("職務経歴", get_section("職務経歴", res1)),
                ("転職を考えたきっかけ", get_section("転職を考えたきっかけ", res1)),
                ("今回の転職で叶えたいこと", get_section("今回の転職で叶えたいこと", res1)),
                ("自分の強み", get_section("自分の強み", res1)),
                ("希望職種・業務", get_section("希望職種・業務", res1)),
                ("希望勤務地", get_section("希望勤務地", res1)),
                ("希望年収・給与", get_section("希望年収・給与", res1)),
            ]
            for label, val in carte_fields:
                st.markdown(f"**{label}**")
                st.text(val)
                st.divider()

        # 結果 3: 生成書類
        with st.expander("3️⃣ 生成書類（職務経歴書・自己PR・志望動機）", expanded=True):
            st.markdown(
                f'<div class="cyber-panel">'
                f'<h3>AI評価スコア: {doc_score}</h3>'
                f'<div class="fb-box">{doc_advice}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            st.markdown("<br>", unsafe_allow_html=True)
            st.subheader("📄 職務経歴書（自己PR含む）")
            st.code(combined_doc, language="text")
            st.subheader("📄 志望動機")
            st.code(motive, language="text")

        # 結果 4: 書類審査・推薦文
        if has_match:
            with st.expander("4️⃣ 書類審査・推薦文", expanded=True):
                st.metric("最終マッチ度", f"{ms} %")
                if ms >= 80:
                    st.success("🔥 合格ライン突破！")
                else:
                    st.warning("⚠️ マッチ度が基準(80%)を下回っています。")
                st.markdown(
                    f"#### ✍️ 書類修正アドバイス\n"
                    f"<div class='fb-box'>{match_advice}</div>",
                    unsafe_allow_html=True,
                )
                st.subheader("🗣️ 面接対策")
                st.write(interview_prep)
                st.subheader("📧 推薦文")
                st.code(rec_letter, language="text")

        # 出力ボタン
        st.divider()
        st.subheader("📤 出力")
        out_col1, out_col2 = st.columns(2)

        with out_col1:
            if st.button("📄 全書類をGoogle Docsに出力", type="primary", use_container_width=True):
                with st.spinner("Google Docsを作成中..."):
                    full_content = (
                        f"【求職者名】{seeker_name}\n"
                        f"【ランク判定】{rank_name}\n\n"
                        f"■ 職務経歴書・自己PR\n{combined_doc}\n\n"
                        f"■ 志望動機\n{motive}\n\n"
                    )
                    if has_match:
                        full_content += f"■ 推薦文\n{rec_letter}"
                    success, doc_url = create_google_doc(
                        f"自動生成_{seeker_name}_{time.strftime('%Y%m%d')}", full_content
                    )
                    if success:
                        st.success(f"✅ **[生成完了！ここをクリックしてDocsを開く]({doc_url})**")
                    else:
                        st.error(doc_url)

        with out_col2:
            final_agent = agent_extracted if agent_extracted in AGENT_LIST else (AGENT_LIST[0] if AGENT_LIST else "")
            if st.button("📊 スプレッドシートに自動転記", type="primary", use_container_width=True):
                with st.spinner("スプレッドシートを作成中..."):
                    info = {
                        "company_name": get_section("応募企業名", res1),
                        "age": str(age),
                        "change_count": str(job_changes),
                        "short_term_leave": str(short_term),
                        "management": get_section("職務経歴", res1),
                    }
                    success, message = export_to_spreadsheet(
                        final_agent, seeker_name, interview_date, info
                    )
                    if success:
                        st.success(message)
                    else:
                        st.error(message)
