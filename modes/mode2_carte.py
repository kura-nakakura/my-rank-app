import streamlit as st
import streamlit.components.v1 as components
import time
from utils import (
    safe_generate_content,
    read_files,
    get_section,
    create_google_doc,
    export_to_spreadsheet,
    AGENT_LIST,
)

def show():
    st.title("📄 初回面談時：カルテ自動生成")
    st.markdown("面談の**文字起こしデータ**や、求職者が準備した**履歴書・職務経歴書**（PDF/TXT）を添付するか、テキストを直接貼り付けてください。AIが自動で全項目を整理します。")

    # ==========================================
    # 🎨 スッキリした入力インターフェース
    # ==========================================
    # 音声入力をアコーディオン（折りたたみ）に収納して圧迫感をなくす
    with st.expander("🎤 音声入力（補助ツール）を使う場合はこちらを開く"):
        components.html("""
        <div style="font-family: sans-serif; margin-bottom: 10px;">
            <button id="start-btn" style="background: transparent; color: #00E5FF; border: 1px solid #00E5FF; border-radius: 5px; padding: 5px 10px; cursor: pointer;">🔴 録音開始</button>
            <button id="stop-btn" style="background: transparent; color: #ff4b4b; border: 1px solid #ff4b4b; border-radius: 5px; padding: 5px 10px; cursor: pointer;" disabled>⏹ 停止</button>
            <p style="color: #FFFFFF; font-size: 12px; margin-top: 5px;">※録音した内容は下のテキストエリアに自動入力されます</p>
        </div>
        <script>
            const startBtn = document.getElementById('start-btn'); const stopBtn = document.getElementById('stop-btn');
            let recognition;
            if ('webkitSpeechRecognition' in window) {
                recognition = new webkitSpeechRecognition(); recognition.lang = 'ja-JP'; recognition.continuous = true;
                recognition.onresult = function(event) {
                    let finalTranscript = '';
                    for (let i = event.resultIndex; i < event.results.length; ++i) {
                        if (event.results[i].isFinal) finalTranscript += event.results[i][0].transcript;
                    }
                };
                startBtn.onclick = () => { recognition.start(); startBtn.disabled = true; stopBtn.disabled = false; };
                stopBtn.onclick = () => { recognition.stop(); startBtn.disabled = false; stopBtn.disabled = true; };
            }
        </script>
        """, height=70)

    # 入力欄を2カラムに分けて見やすく配置
    col_in1, col_in2 = st.columns([1, 1.2])
    with col_in1:
        u_files_memo = st.file_uploader("📂 履歴書・職務経歴書・文字起こし (PDF/TXT)", accept_multiple_files=True, key="p0_up")
    with col_in2:
        raw_memo = st.text_area("📝 メモ / テキスト直貼り", height=120, placeholder="履歴書のテキストや面談メモを直接貼り付ける場合はこちら...")

    st.markdown("<br>", unsafe_allow_html=True)
    
    # ボタンを中央に配置
    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
    with col_btn2:
        start_btn = st.button("🪄 AIでカルテ情報を自動抽出する", type="primary", use_container_width=True)

    if start_btn:
        file_text = read_files(u_files_memo) if u_files_memo else ""
        combined_memo = file_text + "\n" + raw_memo

        if not combined_memo.strip():
            st.warning("⚠️ 履歴書などのファイルを添付するか、メモを入力してください。")
        else:
            with st.spinner("AIが求職者情報を詳細に分析中... (サーバー混雑時は数十秒かかります)"):
                prompt = f"""
                あなたは優秀なキャリアアドバイザーのアシスタントです。
                以下の「面談データ（文字起こし・履歴書・メモなど）」から、求職者の情報を抽出して整理してください。
                情報が語られていない項目は「不明」または「記載なし」と記載してください。

                【面談データ】
                {combined_memo}

                【抽出フォーマット（絶対厳守）】
                以下の【】で囲まれたセクション名を必ず使用し、各項目を個別に抽出してください。

                【面談日】
                (YYYY/MM/DD形式)
                【エージェント名】
                (必ず以下のリストから完全一致で選択してください。該当なしは「その他」：{AGENT_LIST})
                【求職者名】
                【エージェント面談の認識】
                【エージェントの利用経験】
                
                # ★修正ポイント：「2002歳」などのバグを防ぐため、年齢のみを指定
                【年齢】
                (※必ず「23」などのように年齢の数字のみを記載してください。生年月日は不要です)
                
                【保有資格】
                【現在の勤務状況】
                【転職回数】
                (在職中も含めた合計社数-1)
                【短期離職数】
                (1年以内の離職回数)
                【応募企業名】
                (具体的な社名があれば記載、なければ「未入力」)

                【職務経歴】
                (経験社数分、以下の8項目を必ず箇条書きで詳細に抽出すること)
                ■会社名：
                ・雇用形態：(正社員、アルバイト、業務委託、契約社員など)
                ・部署／役職：(あれば記載、なければなし)
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
                【求職者からの確認事項や不安ごと】
                【次回面談日】
                【次回面談時間】
                """
                try:
                    resp = safe_generate_content(prompt)
                    res = resp.text

                    st.session_state.p0_interview_date = get_section("面談日", res)
                    st.session_state.p0_agent = get_section("エージェント名", res)
                    st.session_state.p0_seeker = get_section("求職者名", res)

                    st.session_state.p0_change_count = get_section("転職回数", res)
                    st.session_state.p0_short_term = get_section("短期離職数", res)
                    st.session_state.p0_company = get_section("応募企業名", res)

                    st.session_state.p0_recog = get_section("エージェント面談の認識", res)
                    st.session_state.p0_exp = get_section("エージェントの利用経験", res)
                    st.session_state.p0_age = get_section("年齢", res) # 生年月日を除外
                    st.session_state.p0_cert = get_section("保有資格", res)
                    st.session_state.p0_status = get_section("現在の勤務状況", res)
                    st.session_state.p0_history = get_section("職務経歴", res)
                    st.session_state.p0_reason1 = get_section("転職を考えたきっかけ", res)
                    st.session_state.p0_reason2 = get_section("今回の転職で叶えたいこと", res)
                    st.session_state.p0_reason3 = get_section("入社後どうなっていたいか", res)
                    st.session_state.p0_str = get_section("自分の強み", res)
                    st.session_state.p0_str_ep = get_section("強みエピソード", res)
                    st.session_state.p0_weak = get_section("弱み", res)
                    st.session_state.p0_weak_ep = get_section("自分の弱みエピソード", res)
                    st.session_state.p0_c_job = get_section("希望職種・業務", res)
                    st.session_state.p0_c_loc = get_section("希望勤務地", res)
                    st.session_state.p0_c_cur_sal = get_section("現在年収・給与", res)
                    st.session_state.p0_c_req_sal = get_section("希望年収・給与", res)
                    st.session_state.p0_c_time = get_section("勤務時間・休日", res)
                    st.session_state.p0_c_vibes = get_section("社風・雰囲気", res)
                    st.session_state.p0_c_date = get_section("入社希望日", res)
                    st.session_state.p0_o_ans = get_section("求職者からの確認事項や不安ごと", res)
                    st.session_state.p0_o_ndate = get_section("次回面談日", res)
                    st.session_state.p0_o_ntime = get_section("次回面談時間", res)

                    st.session_state.p0_generated = True

                    carte_dict = {
                        "面談日": st.session_state.p0_interview_date,
                        "エージェント名": st.session_state.p0_agent, "求職者名": st.session_state.p0_seeker,
                        "エージェント面談の認識": st.session_state.p0_recog, "エージェントの利用経験": st.session_state.p0_exp,
                        "年齢": st.session_state.p0_age, "保有資格": st.session_state.p0_cert, "現在の勤務状況": st.session_state.p0_status,
                        "職務経歴": st.session_state.p0_history,
                        "転職を考えたきっかけ": st.session_state.p0_reason1, "今回の転職で叶えたいこと": st.session_state.p0_reason2, "今後のビジョン": st.session_state.p0_reason3,
                        "自分の強み": st.session_state.p0_str, "強みエピソード": st.session_state.p0_str_ep, "弱み": st.session_state.p0_weak, "弱みエピソード": st.session_state.p0_weak_ep,
                        "希望職種・業務": st.session_state.p0_c_job, "希望勤務地": st.session_state.p0_c_loc, "現在年収・給与": st.session_state.p0_c_cur_sal, "希望年収・給与": st.session_state.p0_c_req_sal,
                        "勤務時間・休日": st.session_state.p0_c_time, "社風・雰囲気": st.session_state.p0_c_vibes, "入社希望日": st.session_state.p0_c_date,
                        "確認事項や不安ごと": st.session_state.p0_o_ans, "次回面談日": st.session_state.p0_o_ndate, "次回面談時間": st.session_state.p0_o_ntime
                    }
                    st.session_state.carte_log.insert(0, {
                        "time": time.strftime('%Y/%m/%d %H:%M'),
                        "name": st.session_state.p0_seeker if st.session_state.p0_seeker else "未入力",
                        "data": carte_dict
                    })
                    if len(st.session_state.carte_log) > 20:
                        st.session_state.carte_log.pop()
                    st.rerun()

                except Exception as e:
                    st.error(f"解析エラー: {e}")

    # ==========================================
    # 🎯 自動抽出されたデータの表示と編集
    # ==========================================
    if st.session_state.get("p0_generated"):
        st.markdown(f'<div class="cyber-panel"><div class="scan-line"></div><h3>📋 抽出されたカルテ情報</h3><p style="color:white; font-size:14px;">※手作業で修正・追記が可能です</p></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("📄 職務経歴書に直結する情報")
        with st.container(border=True):
            st.markdown('<div class="emerald-box"></div>', unsafe_allow_html=True)
            e_seeker = st.text_input("求職者名", value=st.session_state.p0_seeker)

            st.markdown("#### 🏢 職務経歴")
            e_history = st.text_area("職務経歴 (複数社対応)", value=st.session_state.p0_history, height=200)

            st.markdown("#### 🚀 転職理由・キャリア観")
            c4, c5, c6 = st.columns(3)
            with c4: e_reason1 = st.text_area("転職を考えたきっかけ", value=st.session_state.p0_reason1, height=120)
            with c5: e_reason2 = st.text_area("転職で叶えたいこと", value=st.session_state.p0_reason2, height=120)
            with c6: e_reason3 = st.text_area("今後のビジョン", value=st.session_state.p0_reason3, height=120)

            st.markdown("#### 💪 強み・弱み")
            c7, c8 = st.columns(2)
            with c7:
                e_str = st.text_input("自分の強み", value=st.session_state.p0_str)
                e_str_ep = st.text_area("強みエピソード", value=st.session_state.p0_str_ep, height=100)
            with c8:
                e_weak = st.text_input("弱み", value=st.session_state.p0_weak)
                e_weak_ep = st.text_area("弱みエピソード", value=st.session_state.p0_weak_ep, height=100)

        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("🏢 エージェント管理・条件情報")
        with st.container(border=True):
            st.markdown('<div class="emerald-box"></div>', unsafe_allow_html=True)

            c_ag1, c_ag2 = st.columns(2)
            with c_ag1:
                agent_idx = AGENT_LIST.index(st.session_state.p0_agent) if st.session_state.p0_agent in AGENT_LIST else 0
                e_agent = st.selectbox("エージェント名", AGENT_LIST + ["その他"], index=agent_idx)
            with c_ag2:
                e_interview_date = st.text_input("面談日 (空欄時は今日の日付で転記)", value=st.session_state.p0_interview_date)

            st.markdown("#### 👤 基本情報")
            c1, c2, c3 = st.columns(3)
            with c1:
                e_status = st.text_input("現在の勤務状況", value=st.session_state.p0_status)
                e_cert = st.text_input("保有資格", value=st.session_state.p0_cert)
            with c2:
                e_recog = st.text_input("面談の認識(有/無)", value=st.session_state.p0_recog)
                e_exp = st.text_input("利用経験(有/無)", value=st.session_state.p0_exp)
            with c3:
                e_age = st.text_input("年齢", value=st.session_state.p0_age)

            st.markdown("#### 🎯 就職活動希望条件")
            c9, c10, c11 = st.columns(3)
            with c9:
                e_c_job = st.text_input("希望職種・業務", value=st.session_state.p0_c_job)
                e_company = st.text_input("応募企業名", value=st.session_state.p0_company)
                e_c_loc = st.text_input("希望勤務地", value=st.session_state.p0_c_loc)
                e_c_date = st.text_input("入社希望日", value=st.session_state.p0_c_date)
            with c10:
                e_c_cur_sal = st.text_input("現在年収・給与", value=st.session_state.p0_c_cur_sal)
                e_c_req_sal = st.text_input("希望年収・給与", value=st.session_state.p0_c_req_sal)
                e_change_count = st.text_input("転職回数", value=st.session_state.p0_change_count)
                e_short_term = st.text_input("短期離職数", value=st.session_state.p0_short_term)
            with c11:
                e_c_time = st.text_input("勤務時間・休日", value=st.session_state.p0_c_time)
                e_c_vibes = st.text_input("社風・雰囲気", value=st.session_state.p0_c_vibes)

            st.markdown("#### 📅 その他確認・次回設定")
            c12, c13 = st.columns([2, 1])
            with c12:
                e_o_ans = st.text_area("確認事項や不安ごと", value=st.session_state.p0_o_ans, height=100)
            with c13:
                e_o_ndate = st.text_input("次回面談日", value=st.session_state.p0_o_ndate)
                e_o_ntime = st.text_input("次回面談時間", value=st.session_state.p0_o_ntime)

        # ==========================================
        # 📤 出力ボタン群
        # ==========================================
        st.divider()
        c_btn_w, c_btn_s, _ = st.columns([1.5, 1.5, 1])

        with c_btn_w:
            if st.button("📄 この面談カルテをGoogle Docsに出力", type="primary", use_container_width=True):
                with st.spinner("Google Docsを作成中..."):
                    carte_dict_updated = {
                        "面談日": e_interview_date, "エージェント名": e_agent, "求職者名": e_seeker,
                        "エージェント面談の認識": e_recog, "エージェントの利用経験": e_exp,
                        "年齢": e_age, "保有資格": e_cert, "現在の勤務状況": e_status,
                        "職務経歴": e_history,
                        "転職を考えたきっかけ": e_reason1, "今回の転職で叶えたいこと": e_reason2, "今後のビジョン": e_reason3,
                        "自分の強み": e_str, "強みエピソード": e_str_ep, "弱み": e_weak, "弱みエピソード": e_weak_ep,
                        "希望職種・業務": e_c_job, "希望勤務地": e_c_loc, "現在年収・給与": e_c_cur_sal, "希望年収・給与": e_c_req_sal,
                        "勤務時間・休日": e_c_time, "社風・雰囲気": e_c_vibes, "入社希望日": e_c_date,
                        "確認事項や不安ごと": e_o_ans, "次回面談日": e_o_ndate, "次回面談時間": e_o_ntime
                    }
                    content_str = "【初回面談カルテ】\n\n"
                    for k, v in carte_dict_updated.items():
                        content_str += f"■ {k}\n{v}\n\n"
                    success, doc_url = create_google_doc(f"面談カルテ_{e_seeker}", content_str)
                    if success:
                        st.success(f"✅ **[生成完了！ここをクリックしてDocsを開く]({doc_url})**")
                    else:
                        st.error(doc_url)

        with c_btn_s:
            if st.button("📊 スプレッドシートに自動転記", type="primary", use_container_width=True):
                with st.spinner("スプレッドシートを作成中..."):
                    info = {
                        "company_name": e_company,
                        "age": e_age,
                        "change_count": e_change_count,
                        "short_term_leave": e_short_term,
                        "management": e_history
                    }

                    success, message = export_to_spreadsheet(e_agent, e_seeker, e_interview_date, info)

                    if success:
                        st.success(message)
                    else:
                        st.error(message)
