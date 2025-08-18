import streamlit as st
import pandas as pd
import pymongo
from dotenv import load_dotenv
import os
load_dotenv()
secret = os.getenv('SECRET')

myclient = pymongo.MongoClient("mongodb://localhost:32768/", username = "myTester", password = secret)
mydb = myclient["test"]
mycol = mydb[st.session_state.selected_collection]
def load_questions_from_csv(file):
    df = pd.read_csv(file, on_bad_lines='skip')
    questions = []
    for _, row in df.iterrows():
        question = {
            "question": row["question"],
            "options": [row[f"option_{i}"] for i in range(1, 5)],
            "answer": row["answer"]
        }
        questions.append(question)
    return questions
# Define questions and options

uploaded_file = st.file_uploader("Upload your quiz CSV file", type=["csv"])
if uploaded_file:
    questions = load_questions_from_csv(uploaded_file)
    count = len(questions)
    if st.button("Save Quiz to Database"):
        # Insert each question as a document
        result = mycol.insert_many(questions)
        st.success(f"Saved {len(result.inserted_ids)} questions to the database.")
# Initialize session state
    if "q_idx" not in st.session_state:
        st.session_state.q_idx = 0
    if "results" not in st.session_state:
        st.session_state.results = []
    if "submitted" not in st.session_state:
        st.session_state.submitted = False
    def record_answer():
        current = questions[st.session_state.q_idx]
        radio_key = f"selected_option_{st.session_state.q_idx}"
        selected = st.session_state.get(radio_key)
        if selected:
            st.session_state.results.append(selected == current["answer"])
    def next_question():
        record_answer()
        st.session_state.q_idx += 1       
# Display current question
# Show button to enable the practice mode
# practice mode lets the user view the correct answers after each question
    st.header("Load Questions for Quiz here")
    show_answer_key = f"show_answer_{st.session_state.q_idx}"
    if st.session_state.q_idx < len(questions):
        current = questions[st.session_state.q_idx]
        st.write(f"Question {st.session_state.q_idx + 1}: {current['question']}")
        radio_key = f"selected_option_{st.session_state.q_idx}"
        selected = st.radio(
            "Select an option:",
            current["options"],
            index=None,
            key=radio_key
        )
        if st.button("Show Correct Answer", key=show_answer_key):
            st.info(f"Correct Answer: {current['answer']}")

        if st.session_state.q_idx < len(questions) - 1:
            if st.button("Next Question"):
                next_question()
                st.rerun()
        else:
            if st.button("Submit"):
                record_answer()
                st.session_state.submitted = True
                st.rerun()
    if st.session_state.submitted:
        st.write("Thank you for completing the quiz!")
        st.write(f"You answered {sum(st.session_state.results)} out of {count} questions correctly.")
        st.button("Restart Quiz", on_click=lambda: st.session_state.clear())
        if st.button("Show Summary"):
            for i, res in enumerate(st.session_state.results):
                st.write(f"Question {i + 1}: {'Correct' if res else 'Incorrect'}")
else:
    st.info("Please upload a CSV file to start the quiz.")