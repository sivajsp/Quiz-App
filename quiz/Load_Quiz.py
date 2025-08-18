# This section handles loading quiz questions from the database
import streamlit as st
import pandas as pd
import pymongo
from dotenv import load_dotenv
import os
import random
load_dotenv()
secret = os.getenv('SECRET')

myclient = pymongo.MongoClient("mongodb://localhost:32768/", username = "myTester", password = secret)
mydb = myclient["test"]
mycol = mydb[st.session_state.selected_collection]
questions = []
def load_questions_from_mongo(limit=None):
    questions = []
    for doc in mycol.find():
        questions.append({
            "question": doc["question"],
            "options": doc["options"],
            "answer": doc["answer"]
        })
    if limit is not None and limit < len(questions):
        questions = random.sample(questions, limit)
    return questions
# Define questions and options
if "questions" not in st.session_state:
    st.session_state.questions = []
num_questions = st.radio(
    "Select number of questions to load:",
    [10, 15, 20, 30],
    index=0
)
if st.button("Load Questions from Database"):
    st.session_state.questions = load_questions_from_mongo(limit=num_questions)
    st.session_state.q_idx = 0
    st.session_state.results = []
    st.session_state.submitted = False
    st.success(f"Loaded {len(st.session_state.questions)} questions from the database.")

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
    radio_key = f"selected_option_{st.session_state.q_idx}"
    selected = st.session_state.get(radio_key)
    if selected:
        st.session_state.results.append(selected == current["answer"])

def next_question():
    record_answer()
    st.session_state.q_idx += 1

if questions:       
    # Add selectbox for navigation
    question_numbers = [f"Question {i+1}" for i in range(len(questions))]
    selected_q = st.selectbox(
        "Go to question:",
        question_numbers,
        index=st.session_state.q_idx
    )
    # If user changes selection, update q_idx and rerun
    if question_numbers.index(selected_q) != st.session_state.q_idx:
        st.session_state.q_idx = question_numbers.index(selected_q)
        st.rerun()

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
    st.write("Load Questions from Database")