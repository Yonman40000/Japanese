import streamlit as st

if "page" not in st.session_state:
    st.session_state.page = "home"

if st.session_state.page == "home":
    # トップ画面を描画
elif st.session_state.page == "quiz":
    # クイズ画面
elif st.session_state.page == "result":
    # 成績画面

Question = {
    "id": 1,
    "type": "mcq",  # "mcq" or "input"
    "prompt": "この文として自然なのはどれ？",
    "choices": ["A案", "B案", "C案", "D案"],
    "answer_index": 2,
    "explanation": "解説テキスト…",
    "tags": ["助詞", "日常会話", "N3文法"],
    "audio_path": "audio/q1.mp3"  # あれば
}

UserAnswer = {
    "user_id": "test_user",
    "question_id": 1,
    "is_correct": True,
    "answered_at": "...",
    "time_ms": 5300,
}


QuestionState = {
    "question_id": 1,
    "times_seen": 3,
    "correct": 1,
    "wrong": 2,
    "last_seen": "2025-12-03",
}

def priority(qs: QuestionState) -> float:
    base = 1
    base += qs["wrong"] * 2      # 間違いが多いほど優先
    base -= qs["correct"] * 0.5  # 正解が多いと優先度下げる
    # さらに最近出したものは少し優先度を下げるなどもOK
    return base


# 全QuestionStateの中から、まだ出してOKなやつをリストにする
candidates = all_question_states

# priorityが高い順にソートして先頭から使う
sorted_list = sorted(candidates, key=priority, reverse=True)
next_question_id = sorted_list[0]["question_id"]


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