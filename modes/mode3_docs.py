import streamlit as st
import streamlit.components.v1 as components
import time
import json

from utils import (
    safe_generate_content,
    read_files,
    get_url_text,
    get_section,
    create_google_doc,
    fill_excel_template,
)


def show():
    st.title("📄 初回面談後: 書類作成＆分析")
    st.markdown("企業情報と求職者情報を元に、AIが最適な職務経歴書・自己PR・志望動機を自動生成します。")

    # ==========================================
    # 🎨 スッキリした入力インターフェース
    # ==========================================
    c_top1, c_top2 = st.columns(2)
    with c_top1: t_ind = st.text_input("志望業種", placeholder="未入力の場合は添付資料から判断します")
    with c_top2: t_job = st.text_input("志望職種", placeholder="未入力の場合は添付資料から判断します")

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    
    # 🏢 左カラム：企業情報
    with col1:
        st.subheader("🏢 企業・募集情報")
        with st.container(border=True):
            u_url_corp = st.text_input("🔗 求人票URL (自動読み取り)", placeholder="https://...")
            u_files_corp = st.file_uploader("📂 企業求人票など", accept_multiple_files=True, key="corp_up")

    # 📂 右カラム：求職者情報
    with col2:
        st.subheader("📂 求職者情報")
        with st.container(border=True):
            if st.button("🔄 Phase 0のカルテ情報を読み込む", use_container_width=True):
                st.session_state.p2_sync_achievement = (
                    f"【職務経歴】\n{st.session_state.p0_history}\n\n"
                    f"【転職理由】\n{st.session_state.p0_reason1}\n\n"
                    f"【叶えたいこと】\n{st.session_state.p0_reason2}\n\n"
                    f"【強み】\n{st.session_state.p0_str}\n{st.session_state.p0_str_ep}"
                )
                st.success("Phase 0のカルテデータを読み込みました！")

            u_files_seeker = st.file_uploader("📂 履歴書・面談文字起こし", accept_multiple_files=True, key="seeker_up")

            achievement = st.text_area("📝 求職者の補足事項・メモ", value=st.session_state.get("p2_sync_achievement", ""), height=100)

            # 音声入力を折りたたんで圧迫感を消す
            with st.expander("🎤 音声入力（補助ツール）を使う場合はこちらを開く"):
                components.html("""
                <div style="font-family: sans-serif; margin-top: -10px;">
                    <button id="start-btn" style="background: transparent; color: #00E5FF; border: 1px solid #00E5FF; border-radius: 5px; padding: 5px 10px; cursor: pointer;">🔴 録音開始</button>
                    <button id="stop-btn" style="background: transparent; color: #ff4b4b; border: 1px solid #ff4b4b; border-radius: 5px; padding: 5px 10px; cursor: pointer;" disabled>⏹ 停止</button>
                    <textarea id="result" style="width: 100%; height: 70px; background: rgba(0,0,0,0.3); color: white; border: 1px solid #00E5FF; border-radius: 5px; padding: 5px; margin-top: 10px;" placeholder="ここに音声が文字起こしされます..."></textarea>
                </div>
                <script>
                    const startBtn = document.getElementById('start-btn'); const stopBtn = document.getElementById('stop-btn');
                    const resultArea = document.getElementById('result'); let recognition;
                    if ('webkitSpeechRecognition' in window) {
                        recognition = new webkitSpeechRecognition(); recognition.lang = 'ja-JP'; recognition.continuous = true;
                        recognition.onresult = function(event) {
                            let finalTranscript = '';
                            for (let i = event.resultIndex; i < event.results.length; ++i) {
                                if (event.results[i].isFinal) finalTranscript += event.results[i][0].transcript;
                            }
                            if(finalTranscript) resultArea.value += finalTranscript + '\\n';
                        };
                        startBtn.onclick = () => { recognition.start(); startBtn.disabled = true; stopBtn.disabled = false; };
                        stopBtn.onclick = () => { recognition.stop(); startBtn.disabled = false; stopBtn.disabled = true; };
                    }
                </script>
                """, height=150)

    # メインボタンを中央に配置して目立たせる
    st.markdown("<br>", unsafe_allow_html=True)
    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
    with col_btn2:
        start_btn = st.button("✨ AI書類生成を開始", type="primary", use_container_width=True)

    # ==========================================
    # ⚙️ 処理ロジック（以下、一切変更なし）
    # ==========================================
    if start_btn:
        corp_url_data = get_url_text(u_url_corp) if u_url_corp else ""
        corp_file_data = read_files(u_files_corp) if u_files_corp else ""
        corp_data = corp_file_data + "\n" + corp_url_data
        seeker_data = read_files(u_files_seeker) if u_files_seeker else ""

        if not (t_ind or t_job or corp_data.strip()):
            st.warning("企業情報を入力してください。")
        elif not (achievement or seeker_data.strip()):
            st.warning("求職者情報を入力してください。")
        else:
            with st.spinner("情報を深く分析中... (サーバー混雑時は数十秒かかります)"):
                prompt = f"""
あなたは人材紹介会社の**プロキャリアライター兼採用目線の職務経歴書編集者**です。
提供された「企業情報」と「求職者情報」を深く分析し、企業が「ぜひ会ってみたい」と思える具体的・誠実・読みやすい書類を作成してください。

【入力：企業情報】
志望業種：{t_ind if t_ind else "未入力（企業資料から判断してください）"}
志望職種：{t_job if t_job else "未入力（企業資料から判断してください）"}
企業側資料：{corp_data if corp_data else "なし"}

【入力：求職者情報】
補足メモ：{achievement if achievement else "なし"}
求職者側資料（履歴書・面談文字起こし等）：{seeker_data if seeker_data else "なし"}

---
【重要ルール】
- 提供された「求職者情報」から、実際の経験・業務内容・成果を具体的に抽出し、必ず書類に反映させてください。架空の経験は絶対に書かないでください。
- 「企業情報」の求める人物像に合わせ、求職者の強みを最適化して記載してください。
- 以下の【】で囲まれた各セクションを、「一切省略せずに」出力してください。

【評価】
(S最高/A良き！/Bいい感じ/C要努力/Z測定不能のみ)

【理由とアドバイス】
(評価の理由と、プロのエージェントとしての鋭い視点や、面接での深掘りポイントのアドバイスを記載)

【職務経歴】
1. 作成日・氏名
2. 職務経歴（各社ごとに以下の構成を維持。必ず求職者資料の事実を元に書くこと）
   ■会社名：〇〇
   雇用形態：〇〇
   事業内容：〇〇
   役職：〇〇
   ▼業務内容
   ・実際の業務内容（タスク・役割）を5〜7行で具体的に記載。
   ・【絶対ルール】文末は「〜ました」「〜です」を禁止し、必ず「〇〇を実施。」「〇〇を担当。」「〇〇に貢献。」と簡潔に言い切ること。
   ▼成果
   ・数値・改善・貢献を具体的に記載。
   ・【絶対ルール】文末は「〜ました」を禁止し、「〇〇を実現し、〇〇％改善。」「〇〇件の契約を継続的に達成。」のように言い切ること。

【自己PR】
- 企業情報に最適化された自己PR。
- 企業の理念・社風・仕事内容に合わせ、経験をどう活かせるか、なぜ惹かれたかを記載。
- 400字で構成。事実を元にし、嘘や推測は含めない。
- 【絶対ルール】長文で読みにくくなるのを防ぐため、内容の区切りごとに必ず「改行（段落分け）」を行ってください。
- 「」や""や・などAI文章だとわかる記号は控える。文体は敬体（です・ます）。
- 一文は60文字以内で簡潔に。丁寧・誠実・安定感のある文体で統一。
- キャリアコンサルタントの視点を取り入れ、求職者の泥臭い努力や具体的なエピソードを魅力的に引き立たせてください。

【志望動機】
- 企業情報と求職者情報を結びつけ、なぜこの企業なのかを具体的に記載。
- ありきたりな言葉ではなく、その企業ならではの強みや特徴に惹かれた理由を深く掘り下げてください。
- 企業にマイナスにならないのを前提に、年齢に合わせた文章・言葉使いにする。
- 約450字で作成。業務や実績は推測や嘘を避ける。
- 【絶対ルール】長文で読みにくくなるのを防ぐため、内容の区切りごとに必ず「改行（段落分け）」を行ってください。
- 「」や""や・などは控える。
"""
                try:
                    resp = safe_generate_content(prompt)
                    res = resp.text
                    st.session_state.phase2_score = get_section("評価", res)
                    st.session_state.phase2_advice = get_section("理由とアドバイス", res)
                    hist = get_section('職務経歴', res)
                    pr = get_section('自己PR', res)
                    st.session_state.phase2_combined = f"{hist}\n\n■自己PR\n{pr}"
                    st.session_state.phase2_motive = get_section('志望動機', res)
                    st.session_state.phase2_generated = True
                    st.session_state.chat_messages = []

                    st.session_state.history_log.insert(0, {
                        "time": time.strftime('%Y/%m/%d %H:%M'),
                        "job": t_job if t_job else "未指定",
                        "score": st.session_state.phase2_score,
                        "advice": st.session_state.phase2_advice,
                        "combined": st.session_state.phase2_combined,
                        "motive": st.session_state.phase2_motive,
                        "chat": []
                    })
                    if len(st.session_state.history_log) > 20:
                        st.session_state.history_log.pop()
                    st.rerun()

                except Exception as e:
                    st.error(f"解析エラー: {e}")

    if st.session_state.get("phase2_generated"):
        st.markdown(f'<div class="cyber-panel"><div class="scan-line"></div><h3>AI分析評価スコア: {st.session_state.phase2_score}</h3><div class="fb-box">{st.session_state.phase2_advice}</div></div>', unsafe_allow_html=True)
        st.divider()
        st.subheader("📄 職務経歴書（自己PR含む・高品質版）")
        st.code(st.session_state.phase2_combined, language="text")

        c_btn1, c_btn2, _ = st.columns([1.8, 1.2, 2.5])
        with c_btn1:
            if st.button("📄 この職務経歴書をGoogle Docsに出力", type="primary", use_container_width=True):
                with st.spinner("Google Docsを作成中..."):
                    doc_content_str = f"職務経歴書（自己PR含む）\n\n{st.session_state.phase2_combined}\n\n■志望動機\n{st.session_state.phase2_motive}"
                    success, doc_url = create_google_doc(f"職務経歴書_{time.strftime('%Y%m%d')}", doc_content_str)
                    if success:
                        st.success(f"✅ **[生成完了！ここをクリックしてDocsを開く]({doc_url})**")
                    else:
                        st.error(doc_url)
        with c_btn2:
            components.html("""<button onclick="window.parent.print()" style="background:transparent; color:#00E5FF; border:1px solid #00E5FF; padding:8px 12px; border-radius:8px; font-size:13px; cursor:pointer; width:auto;">🖨️ PDF保存</button>""", height=50)

        st.subheader("📄 志望動機")
        st.code(st.session_state.phase2_motive, language="text")

        # Excel履歴書への流し込み機能
        st.divider()
        st.subheader("📊 Excel履歴書への完全自動流し込み")
        st.info("※タグ（{{ふりがな}}や{{歴年1}}など）を配置したExcelテンプレートをアップロードしてください。")

        u_excel_template = st.file_uploader("履歴書テンプレート (Excel形式: .xlsx)", type=["xlsx"], key="excel_tpl_up")

        if u_excel_template:
            if st.button("✨ 履歴書データを解析してExcelに流し込む", type="primary"):
                with st.spinner("求職者のデータを解析し、Excelにマッピング中..."):
                    try:
                        seeker_raw_data = read_files(u_files_seeker) if u_files_seeker else ""
                        seeker_raw_data += "\n" + achievement

                        json_prompt = f"""
                        あなたは履歴書データ抽出のプロです。以下の求職者データから、履歴書作成に必要な項目を抽出し、必ず以下のJSONフォーマット（プレーンテキスト）のみを出力してください。マークダウン（```jsonなど）は不要です。

                        【抽出ルール】
                        - データが存在しない項目は空文字("")にしてください。
                        - 年はすべて「西暦」で統一してください。
                        - 学歴と職歴は同じリスト(history)にまとめ、学歴の先頭には {{"year":"", "month":"", "content":"学歴"}} を、職歴の先頭には {{"year":"", "month":"", "content":"職歴"}} となる見出し行を必ず挿入してください。
                        - 資格も同様にリスト(licenses)にしてください。

                        【求職者データ】
                        {seeker_raw_data}

                        【出力フォーマット】
                        {{
                          "furigana": "ふりがな",
                          "name": "氏名",
                          "gender": "男/女",
                          "birth_age": "199X年X月X日生 (満XX歳)",
                          "zip_code": "〒XXX-XXXX",
                          "address_furigana": "じゅうしょふりがな",
                          "address": "住所",
                          "phone": "電話番号",
                          "email": "メールアドレス",
                          "history": [
                             {{"year": "", "month": "", "content": "学歴"}},
                             {{"year": "2015", "month": "4", "content": "〇〇高校 入学"}},
                             {{"year": "2018", "month": "3", "content": "〇〇高校 卒業"}},
                             {{"year": "", "month": "", "content": "職歴"}},
                             {{"year": "2018", "month": "4", "content": "株式会社〇〇 入社"}}
                          ],
                          "licenses": [
                             {{"year": "2020", "month": "10", "content": "TOEIC公開テスト 800点取得"}}
                          ]
                        }}
                        """
                        resp_json = safe_generate_content(json_prompt)
                        json_text = resp_json.text.replace('```json', '').replace('```', '').strip()
                        data = json.loads(json_text)

                        replacements = {
                            "{{ふりがな}}": data.get("furigana", ""),
                            "{{氏名}}": data.get("name", ""),
                            "{{性別}}": data.get("gender", ""),
                            "{{生年月日_年齢}}": data.get("birth_age", ""),
                            "{{郵便番号}}": data.get("zip_code", ""),
                            "{{住所ふりがな}}": data.get("address_furigana", ""),
                            "{{住所}}": data.get("address", ""),
                            "{{電話番号}}": data.get("phone", ""),
                            "{{Email}}": data.get("email", ""),
                            "{{志望動機}}": st.session_state.phase2_motive,
                        }

                        history = data.get("history", [])
                        for i in range(1, 31):
                            if i <= len(history):
                                replacements[f"{{{{歴年{i}}}}}"] = history[i-1].get("year", "")
                                replacements[f"{{{{歴月{i}}}}}"] = history[i-1].get("month", "")
                                replacements[f"{{{{歴内容{i}}}}}"] = history[i-1].get("content", "")
                            else:
                                replacements[f"{{{{歴年{i}}}}}"] = ""
                                replacements[f"{{{{歴月{i}}}}}"] = ""
                                replacements[f"{{{{歴内容{i}}}}}"] = ""

                        licenses = data.get("licenses", [])
                        for i in range(1, 11):
                            if i <= len(licenses):
                                replacements[f"{{{{資格年{i}}}}}"] = licenses[i-1].get("year", "")
                                replacements[f"{{{{資格月{i}}}}}"] = licenses[i-1].get("month", "")
                                replacements[f"{{{{資格内容{i}}}}}"] = licenses[i-1].get("content", "")
                            else:
                                replacements[f"{{{{資格年{i}}}}}"] = ""
                                replacements[f"{{{{資格月{i}}}}}"] = ""
                                replacements[f"{{{{資格内容{i}}}}}"] = ""

                        new_excel_data = fill_excel_template(u_excel_template, replacements)

                        st.success("✨ データの抽出とExcelへの流し込みが完了しました！")
                        safe_seeker_name = st.session_state.p0_seeker if st.session_state.get("p0_seeker") else "求職者"
                        st.download_button(
                            label="📥 完成したExcel履歴書をダウンロード",
                            data=new_excel_data,
                            file_name=f"完成版_履歴書_{safe_seeker_name}_{time.strftime('%Y%m%d')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            type="primary"
                        )

                    except json.JSONDecodeError:
                        st.error("AIからのデータ抽出に失敗しました。もう一度ボタンを押してお試しください。")
                    except Exception as e:
                        st.error(f"エラーが発生しました: {e}")

        # AIチャット機能
        st.divider()
        st.subheader("💬 AIアシスタントと内容を調整する")

        edit_target = st.radio("🎯 修正する項目を選択", ["全体", "職務経歴", "自己PR", "志望動機"], horizontal=True)

        for msg in st.session_state.chat_messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        if chat_input := st.chat_input(f"【{edit_target}】への修正依頼を入力してください"):
            st.session_state.chat_messages.append({"role": "user", "content": f"[{edit_target}] {chat_input}"})
            with st.chat_message("user"):
                st.markdown(f"**[{edit_target}]** {chat_input}")

            with st.chat_message("assistant"):
                chat_prompt = f"""
あなたはプロのキャリアコンサルタントです。ユーザーの【修正指示】に基づき、書類をより魅力的で具体的に改善してください。

【対象セクション】: {edit_target}

【厳守ルール】
1. 指定された「{edit_target}」の部分のみを修正してください（「全体」の場合は全体のバランスを見て修正）。
2. 修正対象外のセクションは一切変更せず、そのまま出力してください。
3. 元の改行、見出し(■,▼,・)、箇条書き、体言止めのフォーマットを絶対に崩さない。
4. 自己PRや志望動機を修正する場合は、必ず適度な「改行（段落分け）」を入れて読みやすくすること。
5. プロの視点から、より具体的で説得力のある表現にブラッシュアップすること。

【現在の書類データ】
{st.session_state.phase2_combined}
志望動機：{st.session_state.phase2_motive}

【ユーザーからの修正指示】
{chat_input}
"""
                try:
                    chat_resp = safe_generate_content(chat_prompt)
                    st.markdown(chat_resp.text)
                    st.session_state.chat_messages.append({"role": "assistant", "content": chat_resp.text})
                    if st.session_state.history_log:
                        st.session_state.history_log[0]["chat"] = st.session_state.chat_messages
                except Exception as e:
                    st.error(f"チャットエラー: {e}")
