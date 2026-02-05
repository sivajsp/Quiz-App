#This is the Overview section and it provide the collection of quiz question available in the database
#It has option to create the New Collection of quiz and it creates the equivalent collection in the database
import streamlit as st
import pandas as pd
import pymongo
from dotenv import load_dotenv
import os
import random
import gtts
import io

st.set_page_config(
    page_title="Take Quiz - Quiz App",
    page_icon="▶️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

load_dotenv()
secret = os.getenv('SECRET')

myclient = pymongo.MongoClient("mongodb://localhost:32768", username="myTester", password=secret)
mydb = myclient["test"]

collection_name = st.session_state.get("selected_collection", None)
if not collection_name:
    st.warning("No collection selected. Please go back and select one.")
    if st.button("← Back to Overview"):
        st.switch_page("Overview.py")
    st.stop()

mycol = mydb[collection_name]

# --- Back navigation ---
if st.button("← Back to Overview"):
    # Clean up quiz state when leaving
    for key in ["questions", "q_idx", "results", "submitted"]:
        st.session_state.pop(key, None)
    st.switch_page("Overview.py")

st.header(f"Quiz: {collection_name}")

def load_questions_from_mongo(limit=None):
    questions = []
    for doc in mycol.find():
        q = {
            "question": doc["question"],
            "answer": doc["answer"],
            "question type": doc.get("question type", "short answer")
        }
        if doc.get("question type") == "mcq":
            q["options"] = doc.get("options", [])
        questions.append(q)
    if isinstance(limit, int) and limit < len(questions):
        questions = random.sample(questions, limit)
    return questions

def text_to_speech(text):
    tts = gtts.gTTS(text, lang='nl', slow=False)
    audio_file = io.BytesIO()
    tts.write_to_fp(audio_file)
    audio_file.seek(0)
    return audio_file

# --- Quiz setup ---
if "questions" not in st.session_state:
    st.session_state.questions = []

total_available = mycol.count_documents({})
st.caption(f"{total_available} questions available in this collection")

num_questions = st.radio(
    "How many questions?",
    [10, 15, 20, 30, "All"],
    index=0,
    horizontal=True
)

if st.button("Load Questions", type="primary"):
    limit = None if num_questions == "All" else num_questions
    st.session_state.questions = load_questions_from_mongo(limit=limit)
    st.session_state.q_idx = 0
    st.session_state.results = []
    st.session_state.submitted = False
    st.rerun()

questions = st.session_state.questions
count = len(questions)

if "q_idx" not in st.session_state:
    st.session_state.q_idx = 0
if "results" not in st.session_state:
    st.session_state.results = []
if "submitted" not in st.session_state:
    st.session_state.submitted = False

def record_answer():
    current = questions[st.session_state.q_idx]
    q_type = current.get("question type")
    if q_type == "mcq":
        key = f"selected_option_{st.session_state.q_idx}"
    elif q_type == "true/false":
        key = f"true_false_{st.session_state.q_idx}"
    elif q_type == "readout loud":
        key = f"readout_loud_{st.session_state.q_idx}"
    else:
        key = f"short_answer_{st.session_state.q_idx}"
    selected = st.session_state.get(key)
    if selected:
        st.session_state.results.append(selected.strip().lower() == current["answer"].strip().lower())
    else:
        st.session_state.results.append(False)

def next_question():
    record_answer()
    st.session_state.q_idx += 1

if questions and not st.session_state.submitted:
    st.write("---")

    # Progress bar
    progress = st.session_state.q_idx / count
    st.progress(progress)
    st.caption(f"Question {st.session_state.q_idx + 1} of {count}")

    # Question navigation dropdown
    question_numbers = [f"Q{i+1}: {questions[i]['question'][:40]}..." for i in range(len(questions))]
    selected_q = st.selectbox(
        "Jump to question:",
        question_numbers,
        index=st.session_state.q_idx,
        label_visibility="collapsed"
    )
    new_idx = question_numbers.index(selected_q)
    if new_idx != st.session_state.q_idx:
        st.session_state.q_idx = new_idx
        st.rerun()

    if st.session_state.q_idx < len(questions):
        current = questions[st.session_state.q_idx]
        q_type = current.get("question type", "short answer")
        type_badge = {"mcq": "Multiple Choice", "short answer": "Short Answer", "true/false": "True/False", "readout loud": "Read Aloud"}.get(q_type, q_type)
        st.caption(f"Type: {type_badge}")

        # Question Display logic
        if q_type == "mcq":
            st.markdown(f"### {current['question']}")
            radio_key = f"selected_option_{st.session_state.q_idx}"
            st.radio(
                "Select an option:",
                current["options"],
                index=None,
                key=radio_key,
                label_visibility="collapsed"
            )
        elif q_type == "short answer":
            st.markdown(f"### {current['question']}")
            st.text_input("Your Answer:", key=f"short_answer_{st.session_state.q_idx}")
        elif q_type == "true/false":
            st.markdown(f"### {current['question']}")
            st.radio(
                "Select True or False:",
                ["True", "False"],
                index=None,
                key=f"true_false_{st.session_state.q_idx}",
                label_visibility="collapsed"
            )
        elif q_type == "readout loud":
            st.markdown(f"### {current['question']}")
            audio_file = text_to_speech(current['question'])
            st.audio(audio_file, format="audio/mp3")
            st.text_input("Your Answer:", key=f"readout_loud_{st.session_state.q_idx}")

        # Action buttons
        btn_col1, btn_col2, btn_col3 = st.columns(3)
        with btn_col1:
            show_answer_key = f"show_answer_{st.session_state.q_idx}"
            if st.button("Show Answer", key=show_answer_key):
                st.info(f"Correct Answer: {current['answer']}")
        with btn_col2:
            if st.session_state.q_idx < len(questions) - 1:
                if st.button("Next →"):
                    next_question()
                    st.rerun()
        with btn_col3:
            if st.button("Submit Quiz", type="primary" if st.session_state.q_idx == len(questions) - 1 else "secondary"):
                record_answer()
                st.session_state.submitted = True
                st.rerun()

elif st.session_state.submitted:
    st.write("---")
    correct = sum(st.session_state.results)
    total = count
    percentage = (correct / total * 100) if total > 0 else 0

    # Results header
    if percentage >= 80:
        st.success(f"### Great job! {correct}/{total} correct ({percentage:.0f}%)")
    elif percentage >= 50:
        st.warning(f"### Not bad! {correct}/{total} correct ({percentage:.0f}%)")
    else:
        st.error(f"### Keep practicing! {correct}/{total} correct ({percentage:.0f}%)")

    st.progress(correct / total if total > 0 else 0)

    # Detailed results
    with st.expander("View Detailed Results", expanded=True):
        for i, res in enumerate(st.session_state.results):
            if i < len(questions):
                icon = "✅" if res else "❌"
                st.markdown(f"{icon} **Q{i + 1}:** {questions[i]['question'][:80]}")
                if not res:
                    st.caption(f"   Correct answer: {questions[i]['answer']}")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Restart Quiz", type="primary"):
            for key in ["questions", "q_idx", "results", "submitted"]:
                st.session_state.pop(key, None)
            st.rerun()
    with col2:
        if st.button("Back to Overview"):
            for key in ["questions", "q_idx", "results", "submitted"]:
                st.session_state.pop(key, None)
            st.switch_page("Overview.py")
else:
    st.info("Click **Load Questions** above to start the quiz.")
