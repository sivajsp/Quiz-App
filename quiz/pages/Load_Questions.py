import streamlit as st
import pandas as pd
import pymongo
import gtts
from dotenv import load_dotenv
import os
import io

st.set_page_config(
    page_title="Upload Questions - Quiz App",
    page_icon="📤",
    layout="centered",
    initial_sidebar_state="collapsed"
)

load_dotenv()
secret = os.getenv('SECRET')

myclient = pymongo.MongoClient("mongodb://localhost:32768/", username="myTester", password=secret)
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
    st.switch_page("Overview.py")

st.header(f"Upload Questions to: {collection_name}")

# --- Question type selector ---
question_type = st.radio(
    "Select Question Type for Upload:",
    ["mcq", "short answer", "true/false", "readout loud"],
    index=0,
    key="upload_question_type",
    horizontal=True
)

# --- CSV format help ---
with st.expander("CSV Format Guide"):
    if question_type == "mcq":
        st.markdown("""
**Required columns:** `question`, `option_1`, `option_2`, `option_3`, `option_4`, `answer`

| question | option_1 | option_2 | option_3 | option_4 | answer |
|----------|----------|----------|----------|----------|--------|
| What is 2+2? | 3 | 4 | 5 | 6 | 4 |
        """)
    elif question_type == "short answer":
        st.markdown("""
**Required columns:** `question`, `answer`

| question | answer |
|----------|--------|
| What is the capital of France? | Paris |
        """)
    elif question_type == "true/false":
        st.markdown("""
**Required columns:** `question`, `answer`

| question | answer |
|----------|--------|
| The earth is flat. | False |
        """)
    elif question_type == "readout loud":
        st.markdown("""
**Required columns:** `question`, `answer`

| question | answer |
|----------|--------|
| Hoe gaat het met je? | How are you? |
        """)

def load_questions_from_csv(file, question_type):
    df = pd.read_csv(file, on_bad_lines='skip')
    questions = []
    for _, row in df.iterrows():
        if question_type == "mcq":
            question = {
                "question": row["question"],
                "options": [row[f"option_{i}"] for i in range(1, 5)],
                "answer": row["answer"],
                "question type": "mcq"
            }
        else:
            question = {
                "question": row["question"],
                "answer": row["answer"],
                "question type": question_type
            }
        questions.append(question)
    return questions

def text_to_speech(text):
    tts = gtts.gTTS(text, lang='nl', slow=False)
    audio_file = io.BytesIO()
    tts.write_to_fp(audio_file)
    audio_file.seek(0)
    return audio_file

# --- File upload ---
st.write("---")
uploaded_file = st.file_uploader("Upload your quiz CSV file", type=["csv"])

if uploaded_file:
    questions = load_questions_from_csv(uploaded_file, question_type)
    count = len(questions)
    st.success(f"Parsed **{count}** questions from the file.")

    # --- Preview table ---
    with st.expander(f"Preview ({min(count, 10)} of {count} questions)", expanded=True):
        preview_data = []
        for i, q in enumerate(questions[:10]):
            row = {"#": i + 1, "Question": q["question"][:60] + ("..." if len(q["question"]) > 60 else ""), "Answer": q["answer"]}
            if question_type == "mcq":
                row["Options"] = " | ".join(q["options"])
            preview_data.append(row)
        st.dataframe(pd.DataFrame(preview_data), use_container_width=True, hide_index=True)

    # --- Save button ---
    if st.button("Save to Database", type="primary"):
        result = mycol.insert_many(questions)
        st.success(f"Saved **{len(result.inserted_ids)}** questions to **{collection_name}**.")
        st.balloons()

    # --- Optional: preview questions one-by-one ---
    st.write("---")
    st.subheader("Preview Questions")

    # Initialize session state
    if "q_idx" not in st.session_state:
        st.session_state.q_idx = 0
    if "results" not in st.session_state:
        st.session_state.results = []
    if "submitted" not in st.session_state:
        st.session_state.submitted = False

    def record_answer():
        current = questions[st.session_state.q_idx]
        if current.get("question type") == "mcq":
            radio_key = f"selected_option_{st.session_state.q_idx}"
        elif current.get("question type") == "true/false":
            radio_key = f"true_false_{st.session_state.q_idx}"
        else:
            radio_key = f"short_answer_{st.session_state.q_idx}"
        selected = st.session_state.get(radio_key)
        if selected:
            st.session_state.results.append(selected == current["answer"])

    def next_question():
        record_answer()
        st.session_state.q_idx += 1

    # Progress indicator
    if st.session_state.q_idx < len(questions):
        st.progress((st.session_state.q_idx) / len(questions))
        st.caption(f"Question {st.session_state.q_idx + 1} of {count}")

    show_answer_key = f"show_answer_{st.session_state.q_idx}"
    if st.session_state.q_idx < len(questions):
        current = questions[st.session_state.q_idx]
        # Question Display logic
        if current.get("question type") == "mcq":
            st.markdown(f"**Q{st.session_state.q_idx + 1}: {current['question']}**")
            radio_key = f"selected_option_{st.session_state.q_idx}"
            selected = st.radio(
                "Select an option:",
                current["options"],
                index=None,
                key=radio_key,
                label_visibility="collapsed"
            )
        elif current.get("question type") == "short answer":
            st.markdown(f"**Q{st.session_state.q_idx + 1}: {current['question']}**")
            text_key = f"short_answer_{st.session_state.q_idx}"
            st.text_input("Your Answer:", key=text_key)
        elif current.get("question type") == "true/false":
            st.markdown(f"**Q{st.session_state.q_idx + 1}: {current['question']}**")
            radio_key = f"true_false_{st.session_state.q_idx}"
            selected = st.radio(
                "Select True or False:",
                ["True", "False"],
                index=None,
                key=radio_key,
                label_visibility="collapsed"
            )
        elif current.get("question type") == "readout loud":
            st.markdown(f"**Q{st.session_state.q_idx + 1}: {current['question']}**")
            audio_file = text_to_speech(current['question'])
            st.audio(audio_file, format="audio/mp3")
            st.text_input("Your Answer:", key=f"readout_loud_{st.session_state.q_idx}")

        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            if st.button("Show Correct Answer", key=show_answer_key):
                st.info(f"Correct Answer: {current['answer']}")
        with btn_col2:
            if st.session_state.q_idx < len(questions) - 1:
                if st.button("Next Question →"):
                    next_question()
                    st.rerun()
            else:
                if st.button("Submit"):
                    record_answer()
                    st.session_state.submitted = True
                    st.rerun()

    if st.session_state.submitted:
        st.write("---")
        correct = sum(st.session_state.results)
        st.markdown(f"### Results: {correct} / {count} correct")
        st.progress(correct / count if count > 0 else 0)
        st.button("Restart", on_click=lambda: st.session_state.clear())
else:
    st.info("Upload a CSV file to get started. Check the format guide above for the expected columns.")
