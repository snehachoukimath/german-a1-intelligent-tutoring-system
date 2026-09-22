# =============================================================================
# HCAI PROJECT — GROUP 21
# German A1 Intelligent Tutoring System
# app.py — Run with: python -m streamlit run app.py
# =============================================================================

import streamlit as st
from openai import OpenAI
import random
import uuid
import time
import os
from dotenv import load_dotenv

from phase2_data import (
    QUESTION_BANK,
    get_questions_by_level,
    get_all_topics,
    setup_database,
    save_interaction,
    start_session,
    end_session
)

# =============================================================================
# SETUP
# =============================================================================

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)

st.set_page_config(page_title="German A1 Tutor", page_icon="🇩🇪", layout="centered")

# =============================================================================
# SESSION STATE
# =============================================================================

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())[:8]
if "level" not in st.session_state:
    st.session_state.level = 1
if "correct_streak" not in st.session_state:
    st.session_state.correct_streak = 0
if "wrong_streak" not in st.session_state:
    st.session_state.wrong_streak = 0
if "total_correct" not in st.session_state:
    st.session_state.total_correct = 0
if "total_questions" not in st.session_state:
    st.session_state.total_questions = 0
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "current_question" not in st.session_state:
    st.session_state.current_question = None
if "topic" not in st.session_state:
    st.session_state.topic = None
if "waiting_for_answer" not in st.session_state:
    st.session_state.waiting_for_answer = False
if "session_started" not in st.session_state:
    st.session_state.session_started = False
if "asked_questions" not in st.session_state:
    st.session_state.asked_questions = []
if "db_initialized" not in st.session_state:
    conn = setup_database()
    start_session(conn, st.session_state.session_id)
    conn.close()
    st.session_state.db_initialized = True

def get_db():
    import sqlite3
    return sqlite3.connect("its_interactions.db", check_same_thread=False)

# =============================================================================
# COT PROMPT — CORE OF THE PROJECT (Gap 1 + Gap 2)
# =============================================================================

def get_cot_explanation(question, correct_answer, student_answer, level, topic):
    prompt = f"""You are a friendly German A1 language tutor.
A student answered a question incorrectly. Explain exactly why THEIR specific answer is wrong.

QUESTION: {question}
CORRECT ANSWER: {correct_answer}
STUDENT TYPED: {student_answer}
GRAMMAR TOPIC: {topic}
STUDENT LEVEL: {level} out of 5 (1=beginner, 5=advanced A1)

Keep language very simple for Level {level} out of 5.

Reply in exactly this format with each step on its own line, add a blank line between each step:

**Step 1 - What you typed wrong:** [point out their specific mistake]

**Step 2 - Why it is wrong:** [explain why their answer is incorrect]

**Step 3 - The rule:** [one simple grammar rule]

**Step 4 - Correct answer:** [state the correct answer]

**Step 5 - Memory tip:** [one simple trick to remember]

**Step 6 - Keep going!** [one encouraging sentence]

Current level: {level} out of 5."""

    # Confirmed working free models on OpenRouter as of June 2026
    models = [
        "openrouter/auto",
        "meta-llama/llama-4-scout:free",
        "meta-llama/llama-4-maverick:free",
        "deepseek/deepseek-chat-v3.1:free",
        "deepseek/deepseek-r1-0528:free",
        "qwen/qwen3-235b-a22b:free",
        "nex-agi/nex-n2-pro:free",
    ]

    for model_name in models:
        try:
            print(f"Trying model: {model_name}")
            response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500
            )
            result = response.choices[0].message.content
            if result and len(result) > 30:
                print(f"Success with: {model_name}")
                return result
        except Exception as e:
            print(f"[{model_name}] FAILED: {str(e)[:150]}")
            time.sleep(1)
            continue

    return f"Correct answer: **{correct_answer}**\n\nYou typed '{student_answer}' — check the grammar rule for {topic}.\n\nCurrent level: {level} out of 5."


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_next_question(topic, level):
    all_topic_questions = QUESTION_BANK.get(topic, [])
    if not all_topic_questions:
        return None

    asked = st.session_state.asked_questions

    # First: questions at exact level not yet asked
    level_fresh = [q for q in all_topic_questions
                   if q["difficulty"] == level and q["question"] not in asked]

    # Second: any question in topic not yet asked
    if not level_fresh:
        any_fresh = [q for q in all_topic_questions if q["question"] not in asked]
        if any_fresh:
            chosen = random.choice(any_fresh)
        else:
            # All asked — reset and start over
            st.session_state.asked_questions = []
            chosen = random.choice(all_topic_questions)
    else:
        chosen = random.choice(level_fresh)

    st.session_state.asked_questions.append(chosen["question"])
    return chosen


def update_difficulty(is_correct):
    msg = None
    if is_correct:
        st.session_state.correct_streak += 1
        st.session_state.wrong_streak = 0
        st.session_state.total_correct += 1
        if st.session_state.correct_streak >= 3 and st.session_state.level < 5:
            st.session_state.level += 1
            st.session_state.correct_streak = 0
            msg = f"⬆️ Level up! 3 correct in a row. Now at Level {st.session_state.level} out of 5."
    else:
        st.session_state.wrong_streak += 1
        st.session_state.correct_streak = 0
        if st.session_state.wrong_streak >= 2 and st.session_state.level > 1:
            st.session_state.level -= 1
            st.session_state.wrong_streak = 0
            msg = f"⬇️ Level adjusted to Level {st.session_state.level} out of 5. Keep practising!"
    return msg


# =============================================================================
# SIDEBAR
# =============================================================================

topic_display = {
    "articles": "📖 Articles (der/die/das)",
    "greetings": "👋 Greetings",
    "numbers": "🔢 Numbers",
    "verbs": "⚡ Verbs",
    "sentences": "💬 Sentences",
    "questions": "❓ Questions"
}

with st.sidebar:
    st.title("🇩🇪 German A1 Tutor")
    st.caption("HCAI Project — Group 21 — OVGU 2026")
    st.divider()
    st.subheader("Choose a topic")
    selected_topic = st.selectbox(
        "Topic", options=get_all_topics(),
        format_func=lambda x: topic_display.get(x, x),
        label_visibility="collapsed"
    )
    st.divider()
    st.subheader("Your progress")
    c1, c2 = st.columns(2)
    with c1:
        st.metric("Level", f"{st.session_state.level} / 5")
    with c2:
        acc = round(st.session_state.total_correct / st.session_state.total_questions * 100) if st.session_state.total_questions > 0 else 0
        st.metric("Accuracy", f"{acc}%")
    st.metric("Questions answered", st.session_state.total_questions)
    st.metric("Correct", st.session_state.total_correct)
    st.divider()
    level_desc = {1:"Beginner",2:"Elementary",3:"Pre-intermediate",4:"Intermediate",5:"Upper A1"}
    st.caption(f"Level {st.session_state.level}: {level_desc[st.session_state.level]}")
    st.divider()
    if st.button("🔄 New session", use_container_width=True):
        conn = get_db()
        end_session(conn, st.session_state.session_id,
                    st.session_state.total_questions,
                    st.session_state.total_correct,
                    st.session_state.level)
        conn.close()
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()


# =============================================================================
# MAIN CHAT
# =============================================================================

st.title("German A1 Intelligent Tutor")
st.caption("Type your answer. The AI explains YOUR specific mistake — not a generic tip.")

if not st.session_state.session_started:
    st.session_state.chat_history.append({
        "role": "assistant",
        "content": (
            f"👋 Welcome! I am your German A1 tutor.\n\n"
            f"Topic: **{topic_display.get(selected_topic, selected_topic)}** | "
            f"Starting at **Level {st.session_state.level} out of 5**\n\n"
            f"Get 3 correct in a row to level up! Click **Ask me a question** to begin. 🚀"
        )
    })
    st.session_state.session_started = True
    st.session_state.topic = selected_topic

if selected_topic != st.session_state.topic:
    st.session_state.topic = selected_topic
    st.session_state.current_question = None
    st.session_state.waiting_for_answer = False
    st.session_state.chat_history.append({
        "role": "assistant",
        "content": f"Topic changed to **{topic_display.get(selected_topic, selected_topic)}**. Click 'Ask me a question' to continue!"
    })

for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if not st.session_state.waiting_for_answer:
    if st.button("📝 Ask me a question", use_container_width=True, type="primary"):
        q = get_next_question(st.session_state.topic, st.session_state.level)
        if q:
            st.session_state.current_question = q
            st.session_state.waiting_for_answer = True
            st.session_state.total_questions += 1
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": f"**Question** (Level {st.session_state.level}/5 | {q['topic']})\n\n**{q['question']}**"
            })
            st.rerun()

if st.session_state.waiting_for_answer and st.session_state.current_question:
    answer = st.chat_input("Type your answer in German here...")
    if answer:
        st.session_state.chat_history.append({"role": "user", "content": answer})
        q = st.session_state.current_question
        is_correct = answer.strip().lower() == q["correct_answer"].strip().lower()

        if is_correct:
            lvl_msg = update_difficulty(True)
            resp = f"✅ **Correct!** Well done!\n\nAnswer: **{q['correct_answer']}**"
            if lvl_msg:
                resp += f"\n\n{lvl_msg}"
            resp += f"\n\nCurrent level: {st.session_state.level} out of 5."
            st.session_state.chat_history.append({"role": "assistant", "content": resp})
            conn = get_db()
            save_interaction(conn, st.session_state.session_id, st.session_state.topic,
                           q["question"], answer, q["correct_answer"], True,
                           st.session_state.level, "")
            conn.close()
        else:
            with st.spinner("Generating your personalised explanation..."):
                explanation = get_cot_explanation(
                    q["question"], q["correct_answer"], answer,
                    st.session_state.level, q["topic"]
                )
            lvl_msg = update_difficulty(False)
            resp = f"❌ **Not quite.** Here is your personalised explanation:\n\n{explanation}"
            if lvl_msg:
                resp += f"\n\n{lvl_msg}"
            # Add search links to the explanation
            import urllib.parse
            search_query = urllib.parse.quote(f"German grammar {q['question']} {q['correct_answer']}")
            gpt_query = urllib.parse.quote(f"Explain this German grammar question in simple English: {q['question']} The correct answer is {q['correct_answer']}. I typed {answer}. Why is my answer wrong?")
            google_url = f"https://www.google.com/search?q={search_query}"
            chatgpt_url = f"https://chatgpt.com/?q={gpt_query}"
            resp += f"""

---
🔍 **Want to learn more?**
- [🌐 Google this topic]({google_url})
- [🤖 Ask ChatGPT to explain more]({chatgpt_url})
"""
            st.session_state.chat_history.append({"role": "assistant", "content": resp})
            conn = get_db()
            save_interaction(conn, st.session_state.session_id, st.session_state.topic,
                           q["question"], answer, q["correct_answer"], False,
                           st.session_state.level, explanation)
            conn.close()

        st.session_state.waiting_for_answer = False
        st.session_state.current_question = None
        st.rerun()
