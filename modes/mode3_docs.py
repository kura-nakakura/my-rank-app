import streamlit as st
import streamlit.components.v1 as components
import time
import json
import os

from utils import (
    safe_generate_content,
    read_files,
    get_url_text,
    get_section,
    create_google_doc,
    fill_excel_template,
)

# ==========================================
# 🤖 モード1：CAIモード（対話型作成）
# ==========================================
def render_cai_mode():
    st.markdown("### 🤖 CAI (CA × AI) パートナー")
    st.info("企業情報や求職者の情報をチャットで教えてください。CAIが壁打ち相手となり、一緒に最高の書類を作り上げます！")

    # CAI専用のチャット履歴を初期化
    if "cai_messages" not in st.session_state:
        st.session_state.cai_messages = [
            {"role": "assistant", "content": "こんにちは！あなたの書類作成パートナー「CAI（カイ）」です。まずは応募したい企業の情報や、求職者さんの面談メモなどを教えてもらえますか？一緒に魅力的な職務経歴書を作りましょう！"}
        ]

    # チャット履歴の表示
    for msg in st.session_state.cai_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # チャット入力
    if chat_input := st.chat_input("CAIに情報を送る、または指示を出す"):
        # ユーザーの入力を追加
        st.session_state.cai_messages.append({"role": "user", "content": chat_input})
        with st.chat_message("user"):
            st.markdown(chat_input)

        # CAIの思考・応答プロセス
        with st.chat_message("assistant"):
            with st.spinner("CAIが思考中..."):
                # 過去の文脈を含めたプロンプトの構築
                history_text = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.cai_messages[-5:]]) # 最新5件のやり取りを保持
                
                system_prompt = f"""
あなたは人材紹介会社のプロキャリアアドバイザーAI「CAI（カイ）」です。
エージェント（ユーザー）と対話しながら、求職者の魅力を最大限に引き出す職務経歴書や自己PR、志望動機を一緒に作成してください。

【ルール】
1. ユーザーから情報が提供されたら、プロの視点で「どの部分が強みになるか」を分析し、書類の案を提示してください。
2. 情報が足りない場合は、「〇〇の具体的なエピソードはありますか？」など、優しく深掘りする質問を投げかけてください。
3. 最終的にユーザーがコピペして使えるような、完成度の高いテキストブロック（職務経歴、自己PRなど）を提供してください。
4. 返答は明るく、頼りがいのあるプロフェッショナルなトーンで行ってください。

【これまでの会話履歴（直近）】
{history_text}
"""
                try:
                    chat_resp = safe_generate_content(system_prompt)
                    st.markdown(chat_resp.text)
                    st.session_state.cai_messages.append({"role": "assistant", "content": chat_resp.text})
                except Exception as e:
                    st.error(f"CAI通信エラー: {e}")

# ==========================================
# ⚡ モード2：一発作成モード（従来版＋自動Excel）
# ==========================================
def render_one_click_mode():
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
                    f"【職務経歴】\n{st.session_state.get('p0_history', '')}\n\n"
                    f"【転職理由】\n{st.session_state.get('p0_reason1', '')}\n\n"
                    f"【叶えたいこと】\n{st.session_state.get('p0_reason2', '')}\n\n"
                    f"【強み】\n{st.session_state.get('p0_str', '')}\n{st.session_state.get('p0_str_ep', '')}"
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

    st.markdown("<br>", unsafe_allow_html=True)
    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
    with col_btn2:
        start_btn = st.button("✨ AI書類生成を一発で開始", type="primary", use_container_width=True)

    # 処理ロジック
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
あなたは人材紹介会社のプロキャリアライター兼採用目線の職務経歴書編集者です。
【企業情報】志望業種:{t_ind} / 志望職種:{t_job} / 企業資料:{corp_data}
【求職者情報】補足:{achievement} / 求職者資料:{seeker_data}

【出力フォーマット】（以下の【】見出しを必ず使用）
【評価】(S最高/A良/B標準/C要努力 のみ)
【理由とアドバイス】
【職務経歴】(作成日・氏名、各社ごとに■会社名、雇用形態、事業内容、役職、▼業務内容、▼成果 を具体的かつ体言止め等で言い切る)
【自己PR】(400字。適度に改行)
【志望動機】(450字。適度に改行)
"""
                try:
                    resp = safe_generate_content(prompt)
                    res = resp.text
                    st.session_state.phase2_score = get_section("評価", res)
                    st.session_state.phase2_advice = get_section("理由とアドバイス", res)
                    st.session_state.phase2_combined = f"{get_section('職務経歴', res)}\n\n■自己PR\n{get_section('自己PR', res)}"
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

    # 生成結果の表示
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
                    if success: st.success(f"✅ **[生成完了！ここをクリックしてDocsを開く]({doc_url})**")
                    else: st.error(doc_url)
        with c_btn2:
            components.html("""<button onclick="window.parent.print()" style="background:transparent; color:#00E5FF; border:1px solid #00E5FF; padding:8px 12px; border-radius:8px; font-size:13px; cursor:pointer; width:auto;">🖨️ PDF保存</button>""", height=50)

        st.subheader("📄 志望動機")
        st.code(st.session_state.phase2_motive, language="text")

        # ==========================================
        # ★大改修：Excel履歴書の自動出力
        # ==========================================
        st.divider()
        st.subheader("📊 Excel履歴書（自動マッピング出力）")
        st.info("システム内部のテンプレートを使用して、一発でExcel履歴書を作成します。")

        # サーバー（同じフォルダ）にあるテンプレートを直接指定
        TEMPLATE_PATH = "resume_template.xlsx" 

        if st.button("✨ ワンクリックでExcel履歴書を出力", type="primary"):
            if not os.path.exists(TEMPLATE_PATH):
                st.error(f"⚠️ エラー: システム内に '{TEMPLATE_PATH}' が見つかりません。プロジェクトフォルダ内にテンプレートファイルを配置してください。")
            else:
                with st.spinner("データを解析し、Excelに自動流し込み中..."):
                    try:
                        # 既存のテキストデータをまとめる
                        seeker_raw_data = read_files(u_files_seeker) if 'u_files_seeker' in locals() and u_files_seeker else ""
                        seeker_raw_data += "\n" + achievement if 'achievement' in locals() else ""

                        json_prompt = f"""
                        あなたは履歴書データ抽出のプロです。以下の求職者データから、履歴書作成に必要な項目を抽出し、必ず以下のJSONフォーマット（プレーンテキスト）のみを出力してください。マークダウン（```jsonなど）は不要です。

                        【抽出ルール】
                        - データが存在しない項目は空文字("")にしてください。
                        - 学歴の先頭には {{"year":"", "month":"", "content":"学歴"}}、職歴の先頭には {{"year":"", "month":"", "content":"職歴"}} を必ず挿入。
                        
                        【求職者データ】
                        {seeker_raw_data}

                        【出力フォーマット】
                        {{
                          "furigana": "ふりがな", "name": "氏名", "gender": "男/女",
                          "birth_age": "199X年X月X日生 (満XX歳)", "zip_code": "〒XXX-XXXX",
                          "address_furigana": "じゅうしょふりがな", "address": "住所",
                          "phone": "電話番号", "email": "メールアドレス",
                          "history": [ {{"year": "2018", "month": "4", "content": "〇〇入社"}} ],
                          "licenses": [ {{"year": "2020", "month": "10", "content": "TOEIC 800点"}} ]
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
                            replacements[f"{{{{歴年{i}}}}}"] = history[i-1].get("year", "") if i <= len(history) else ""
                            replacements[f"{{{{歴月{i}}}}}"] = history[i-1].get("month", "") if i <= len(history) else ""
                            replacements[f"{{{{歴内容{i}}}}}"] = history[i-1].get("content", "") if i <= len(history) else ""

                        licenses = data.get("licenses", [])
                        for i in range(1, 11):
                            replacements[f"{{{{資格年{i}}}}}"] = licenses[i-1].get("year", "") if i <= len(licenses) else ""
                            replacements[f"{{{{資格月{i}}}}}"] = licenses[i-1].get("month", "") if i <= len(licenses) else ""
                            replacements[f"{{{{資格内容{i}}}}}"] = licenses[i-1].get("content", "") if i <= len(licenses) else ""

                        # 魔法の自動流し込み！ローカルのファイルを指定するだけ
                        new_excel_data = fill_excel_template(TEMPLATE_PATH, replacements)

                        st.success("✨ Excelの自動出力が完了しました！")
                        safe_seeker_name = st.session_state.p0_seeker if st.session_state.get("p0_seeker") else "求職者"
                        st.download_button(
                            label="📥 完成したExcel履歴書をダウンロード",
                            data=new_excel_data,
                            file_name=f"完成版_履歴書_{safe_seeker_name}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            type="primary"
                        )
                    except json.JSONDecodeError:
                        st.error("AIからのデータ抽出に失敗しました。もう一度ボタンをお試しください。")
                    except Exception as e:
                        st.error(f"エラーが発生しました: {e}")

        # アフター編集チャット
        st.divider()
        st.subheader("💬 AIアシスタントと出力内容を調整する")
        edit_target = st.radio("🎯 修正する項目を選択", ["全体", "職務経歴", "自己PR", "志望動機"], horizontal=True)

        for msg in st.session_state.chat_messages:
            with st.chat_message(msg["role"]): st.markdown(msg["content"])

        if chat_input := st.chat_input(f"【{edit_target}】への修正依頼を入力してください"):
            st.session_state.chat_messages.append({"role": "user", "content": f"[{edit_target}] {chat_input}"})
            with st.chat_message("user"): st.markdown(f"**[{edit_target}]** {chat_input}")

            with st.chat_message("assistant"):
                chat_prompt = f"対象: {edit_target}\n以下の書類をユーザーの指示「{chat_input}」に従って修正してください。\n書類:\n{st.session_state.phase2_combined}\n志望動機:\n{st.session_state.phase2_motive}"
                try:
                    chat_resp = safe_generate_content(chat_prompt)
                    st.markdown(chat_resp.text)
                    st.session_state.chat_messages.append({"role": "assistant", "content": chat_resp.text})
                    if st.session_state.history_log:
                        st.session_state.history_log[0]["chat"] = st.session_state.chat_messages
                except Exception as e:
                    st.error(f"チャットエラー: {e}")

# ==========================================
# 🚀 画面の全体制御（モード切り替え）
# ==========================================
def show():
    st.title("📄 初回面談後: 書類作成＆分析")
    
    # 画面上部でモード切り替え用の横並びラジオボタン
    selected_mode = st.radio(
        "作成モードを選択してください",
        ["CAIモード ", "一発作成モード"],
        horizontal=True,
        label_visibility="collapsed"
    )
    
    st.divider()

    if "CAIモード" in selected_mode:
        render_cai_mode()
    else:
        render_one_click_mode()
