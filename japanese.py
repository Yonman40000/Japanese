from typing import TypedDict
import streamlit as st

def switch_page(page: str) -> None:
    st.session_state.page = page


QUESTIONS = [
    {
        "id": 1,
        "prompt": "「毎月」の読みかたは？",
        "choices": ["せんげつ", "まいつき", "まいげつ", "らいげつ"],
        "answer_index": 1,
    },
    {
        "id": 2,
        "prompt": "EASYの日本語は？",
        "choices": ["やすい", "むずかしい", "かんたん", "むずい"],
        "answer_index": 2,
    },
]


if "page" not in st.session_state:
    st.session_state.page = "home"
if "quiz_index" not in st.session_state:
    st.session_state.quiz_index = 0
if "quiz_answers" not in st.session_state:
    st.session_state.quiz_answers = []
if "last_feedback" not in st.session_state:
    st.session_state.last_feedback = None


def render_home() -> None:
    st.title("日本語クイズ")
    st.write("直感的なボタン操作で、今日の学習をスタートしましょう。")

    st.subheader("メニュー")
    col1, col2 = st.columns(2)

    with col1:
        if st.button("クイズを始める", use_container_width=True):
            st.session_state.quiz_index = 0
            st.session_state.quiz_answers = []
            st.session_state.last_feedback = None
            switch_page("quiz")

    with col2:
        if st.button("成績を見る", use_container_width=True):
            switch_page("result")

    st.caption("気になる項目を選んで、学習を進めてください。")


def render_quiz() -> None:
    st.header("クイズ")

    if st.session_state.last_feedback:
        feedback = st.session_state.last_feedback
        if feedback["is_correct"]:
            st.success(feedback["message"])
        else:
            st.error(feedback["message"])

    if st.session_state.quiz_index >= len(QUESTIONS):
        st.info("全ての問題が終了しました。お疲れさまです！")
        if st.button("結果を見る"):
            switch_page("result")
        if st.button("ホームに戻る"):
            switch_page("home")
        return

    question = QUESTIONS[st.session_state.quiz_index]
    st.subheader(f"第{st.session_state.quiz_index + 1}問")
    st.write(question["prompt"])

    choice_labels = [f"{i + 1}. {text}" for i, text in enumerate(question["choices"])]
    selected = st.radio(
        "答えを選んでください",
        options=list(range(len(choice_labels))),
        format_func=lambda idx: choice_labels[idx],
        key=f"choice_{st.session_state.quiz_index}",
    )

    if st.button("回答する", type="primary"):
        is_correct = selected == question["answer_index"]
        message = "正解です！" if is_correct else f"不正解です。正解は「{question['choices'][question['answer_index']]}」です。"

        st.session_state.quiz_answers.append(
            {
                "question_id": question["id"],
                "selected_index": selected,
                "is_correct": is_correct,
            }
        )

        st.session_state.last_feedback = {"is_correct": is_correct, "message": message}
        st.session_state.quiz_index += 1
        st.experimental_rerun()

    if st.button("ホームに戻る"):
        switch_page("home")


def render_result() -> None:
    st.header("成績画面")
    if not st.session_state.quiz_answers:
        st.info("まだクイズが回答されていません。")
    else:
        correct = sum(ans["is_correct"] for ans in st.session_state.quiz_answers)
        total = len(st.session_state.quiz_answers)
        st.metric("正解数", f"{correct} / {total}")

        for record in st.session_state.quiz_answers:
            question = next(q for q in QUESTIONS if q["id"] == record["question_id"])
            st.write(
                f"問題: {question['prompt']} / 回答: {question['choices'][record['selected_index']]} / 正解: {question['choices'][question['answer_index']]}"
            )

    if st.button("ホームに戻る"):
        switch_page("home")


if st.session_state.page == "home":
    render_home()
elif st.session_state.page == "quiz":
    render_quiz()
elif st.session_state.page == "result":
    render_result()

class QuestionState(TypedDict):
    question_id: int
    times_seen: int
    correct: int
    wrong: int
    last_seen: str


Question = {
    "id": 1,
    "type": "mcq",  # "mcq" or "input"
    "prompt": "「毎月」の読みかたは？",
    "choices": ["せんげつ", "まいつき", "まいげつ", "らいげつ"],
    "answer_index": 2,
    "explanation": "読みかたは「まいつき」である。",
    "tags": ["名詞", "日常会話", "N3文法"],
    "audio_path": "audio/q1.mp3",  # あれば
}

UserAnswer = {
    "user_id": "test_user",
    "question_id": 1,
    "is_correct": True,
    "answered_at": "...",
    "time_ms": 5300,
}


question_state_sample: QuestionState = {
    "question_id": 1,
    "times_seen": 3,
    "correct": 1,
    "wrong": 2,
    "last_seen": "2025-12-03",
}

all_question_states: list[QuestionState] = [
    question_state_sample,
    {
        "question_id": 2,
        "times_seen": 5,
        "correct": 4,
        "wrong": 1,
        "last_seen": "2025-12-02",
    },
    {
        "question_id": 3,
        "times_seen": 2,
        "correct": 0,
        "wrong": 2,
        "last_seen": "2025-12-01",
    },
]


def priority(qs: QuestionState) -> float:
    """誤答が多いものを優先し、正答が多いものの優先度は下げる。"""

    base = 1
    base += qs["wrong"] * 2      # 間違いが多いほど優先
    base -= qs["correct"] * 0.5  # 正解が多いと優先度下げる
    # 誤答したカードはすぐに復習させたいので、ANKI風に追加の重みを与える
    if qs["wrong"] > 0:
        base += 3
    return base


def build_review_queue(states: list[QuestionState]) -> list[int]:
    """優先度順の復習キューを返す。誤答がある問題は前方に複数回配置。"""

    weighted_queue: list[int] = []
    for qs in sorted(states, key=priority, reverse=True):
        repeat = max(1, qs["wrong"])  # 誤答回数ぶん前方に並べる
        weighted_queue.extend([qs["question_id"]] * repeat)
    return weighted_queue


# 全QuestionStateから復習キューを作る
review_queue = build_review_queue(all_question_states)

correct_count = sum(qs["correct"] for qs in all_question_states)
next_question_id = review_queue[0]


summary = {
    "total_questions": 50,
    "correct": 35,
    "top_weak_tags": [
        {"tag": "助詞（に／へ）", "wrong_count": 7},
        {"tag": "依頼表現", "wrong_count": 4},
    ],
    "recent_mistakes_examples": [
        {
            "question": "駅に着いた…？",
            "user_answer": "駅へ着いたら連絡する。",
            "correct_answer": "駅に着いたら連絡する。",
        }
    ],
    "level_estimation": "N4〜N3の間",
    "suggested_time": "1日15分〜20分の復習",
}

import os
from openai import OpenAI
api_key = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=api_key)

def generate_feedback(summary):
    system = "あなたは日本語教師です。学習者の成績データから優しいフィードバックを行います。"
    user = f"""
以下はある学習者のクイズ成績です。この情報をもとに、
1) 全体の評価（優しいトーン）
2) 特に苦手なポイントの解説
3) 具体的な復習アドバイス（3つ）
を書いてください。

成績データ:
{summary}
"""

    res = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    return res.choices[0].message.content
