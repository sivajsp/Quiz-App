#This is the Overview section and it provide the collection of quiz question available in the database
#It has option to create the New Collection of quiz and it creates the equivalent collection in the database
import streamlit as st
import pandas as pd
import gtts
from App.Unified import get_db, load_questions_from_mongo, text_to_speech
if st.session_state.get("authenticated", False) is not True:
    st.warning("You must be logged in to access this page.")
    if st.button("Go to Login Page"):
        st.switch_page("login.py")
    st.stop()
st.set_page_config(initial_sidebar_state="collapsed")
mydb = get_db()
mycol = mydb[st.session_state.questions_collection]
questions = []

# Define questions and options
if "questions" not in st.session_state:
    st.session_state.questions = []
num_questions = st.radio(
    "Select number of questions to load:",
    [10, 15, 20, 30, "all"],
    index=0
)
if st.button("Load Questions from Database"):
    if num_questions == "all":
        st.session_state.questions = list(load_questions_from_mongo(mycol, selected_tags=st.session_state.get("hierarchy_tags", [])))
    else:
        st.session_state.questions = list(load_questions_from_mongo(mycol, limit=num_questions, selected_tags=st.session_state.get("hierarchy_tags", [])))
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
if "responses" not in st.session_state:
    st.session_state.responses = []
def record_answer():
    current = questions[st.session_state.q_idx]
    selected = ""
    if current.get("question type") == "mcq":
        radio_key = f"selected_option_{st.session_state.q_idx}"
        selected = st.session_state.get(radio_key)
    elif current.get("question type") == "short answer":
        text_key = f"short_answer_{st.session_state.q_idx}"
        selected = st.session_state.get(text_key)
        # Case-insensitive comparison for short answer
        if selected is not None:
            selected = selected.strip().lower().rstrip(".")

            is_correct = selected == current["answer"].strip().lower().rstrip(".")
            st.session_state.results.append(is_correct)
            st.session_state.responses.append(selected)
            return
    elif current.get("question type") == "true/false":
        radio_key = f"true_false_{st.session_state.q_idx}"
        selected = st.session_state.get(radio_key)
    elif current.get("question type") == "readout loud":
        text_key = f"readout_loud_{st.session_state.q_idx}"
        selected = st.session_state.get(text_key)
    if selected is not None:
        st.session_state.results.append(selected == current["answer"])
        st.session_state.responses.append(selected)

def next_question():
    record_answer()
    st.session_state.q_idx += 1

if questions:       
    # Add selectbox for navigation
    question_numbers = [f"Question {i+1}" for i in range(count)]
    selected_q = st.selectbox(
        "Go to question:",
        question_numbers,
        index=st.session_state.q_idx
    )
    # If user changes selection, update q_idx and rerun
    if question_numbers.index(selected_q) != st.session_state.q_idx:
        st.session_state.q_idx = question_numbers.index(selected_q)
        st.rerun()

    if st.session_state.q_idx < count:
        current = questions[st.session_state.q_idx]
         # Question Display logic
        if current.get("question type") == "mcq":
            st.write(f"Question {st.session_state.q_idx + 1}: {current['question']}")
            radio_key = f"selected_option_{st.session_state.q_idx}"
            selected = st.radio(
                "Select an option:",
                current["options"],
            index=None,
            key=radio_key
        )
        elif current.get("question type") == "short answer":
            st.write(f"Question {st.session_state.q_idx + 1}: {current['question']}")
            text_key = f"short_answer_{st.session_state.q_idx}"
            st.text_input("Your Answer:", key=text_key)
        elif current.get("question type") == "true/false":
            st.write(f"Question {st.session_state.q_idx + 1}: {current['question']}")
            radio_key = f"true_false_{st.session_state.q_idx}"
            selected = st.radio(
                "Select True or False:",
                ["True", "False"],
                index=None,
                key=radio_key
            )
        elif current.get("question type") == "readout loud":
            st.write(f"Question {st.session_state.q_idx + 1}: {current['question']}")
            audio_file = text_to_speech(current['question'])
            st.audio(audio_file, format="audio/mp3")
            st.text_input("Your Answer:", key=f"readout_loud_{st.session_state.q_idx}")
         # Show Correct Answer button
        show_answer_key = f"show_answer_{st.session_state.q_idx}"
        if st.button("Show Correct Answer", key=show_answer_key):
            st.info(f"Correct Answer: {current['answer']}")
            
        if st.session_state.q_idx < count - 1:
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
        counter = 0
        # Show Correct Answers
        if st.button("Show Summary"):
            for i, res in enumerate(st.session_state.results):
                question = questions[i]
                
            # Get user's response
                if question.get("question type") == "mcq":
                    user_response = st.session_state.get(f"selected_option_{i}", "")
                elif question.get("question type") == "short answer":
                    user_response = st.session_state.get(f"short_answer_{i}", "")
                elif question.get("question type") == "true/false":
                    user_response = st.session_state.get(f"true_false_{i}", "")
                elif question.get("question type") == "readout loud":
                    user_response = st.session_state.get(f"readout_loud_{i}", "")
                else:
                    user_response = ""
                st.write(f"Question {i + 1}: {'Correct' if res else 'Incorrect'}")
                st.write(f"Your Response: {st.session_state.responses[i]}")
                st.write(f"Correct Answer: {question['answer']}")
                counter += 1
else:
    st.write("Load Questions from Database")
