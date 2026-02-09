from anki_sm_2 import Scheduler, Card, Rating, ReviewLog
from datetime import datetime, timezone
import streamlit as st
from App.Unified import get_db,text_to_speech,apply_review,update_anki_cards_flag,get_questions_due_today 
import io
import json
from streamlit_javascript import st_javascript


st.set_page_config(initial_sidebar_state="collapsed")
hide_pages = """
    <style>
    [data-testid="stSidebarNav"] {display: none;}
    </style>
"""
st.markdown(hide_pages, unsafe_allow_html=True)

if st.session_state.get("authenticated", False) is not True:
    st.warning("You must be logged in to access this page.")
    if st.button("Go to Login Page"):
        st.switch_page("login.py")
    st.stop()

mydb = get_db()
collection = mydb[st.session_state.anki_collection]
# Initialize the scheduler
scheduler = Scheduler()
today_iso_date = datetime.now(timezone.utc).date().isoformat()
def count_anki_with_tags(collection, tags):
    return collection.count_documents({"anki": 1, "tags":  tags})
def count_non_anki_with_tags(collection, tags):
    return collection.count_documents({"anki": 0, "tags":  tags})
def count_immatured_with_tags(collection, tags):
    return collection.count_documents({"anki": 1, "card.current_interval": {"$lt": 22}, "tags":  tags})
def count_matured_with_tags(collection, tags):
    return collection.count_documents({"anki": 1, "card.current_interval": {"$gt": 21}, "tags":  tags})

#initialize selected tags

selected_tags = []
if "hierarchy_tags" in st.session_state:
    selected_tags = st.session_state.hierarchy_tags
else:
    st.warning("Selected tags will reset after refresh. Please select tags in the Overview page.")
    if st.button("Go to Overview Page"):
        st.switch_page("pages/Overview.py")
    st.stop()
#st.header(f"Anki Quiz - Collection: {selected_collection_name}")
st.write("selected ", "Topic:", selected_tags[0] if len(selected_tags) > 0 else "None", "\n Selected Subtopic:", selected_tags[1] if len(selected_tags) > 1 else "None")
# Display the current card and its interval
# ...existing code...

st.write(f"Questions added in Anki: {count_anki_with_tags(collection, selected_tags)}")
st.write(f"Questions yet to be added in Anki: {count_non_anki_with_tags(collection, selected_tags)}")
st.write(f"Immatured Cards (interval < 21 days): {count_immatured_with_tags(collection, selected_tags)}")
st.write(f"Matured Cards (interval >= 21 days): {count_matured_with_tags(collection, selected_tags)}")
# Initialize session state variables

if "anki_idx" not in st.session_state:
    st.session_state.anki_idx = 0
if "q_idx" not in st.session_state:
    st.session_state.q_idx = 0        
if "results" not in st.session_state:
    st.session_state.results = []
if "submitted" not in st.session_state:
    st.session_state.submitted = False
if "responses" not in st.session_state:
    st.session_state.responses = []
#Add logic to filter questions that has due date as today
st.subheader("Add New Cards today")
daily_limit = st.number_input("Enter the card counts :", min_value=1, max_value=1000, value=5)
if st.button("Submit"):
    count = update_anki_cards_flag(collection, daily_limit, selected_tags)
    st.success(f"{count} cards flagged for Anki today.")

#Filter for the questions due today with selected tags
questions = get_questions_due_today(collection,selected_tags)
updated_questions = []
total_questions = len(questions)
# Reset index if out of range
if st.session_state.anki_idx >= total_questions:
    st.session_state.anki_idx = 0

if total_questions > 0 and st.session_state.anki_idx < total_questions:
    idx = st.session_state.anki_idx
    current = questions[idx]
    # Question display logic here

    if current.get("question type") == "mcq":
            st.write(f" {current['question']}")
            radio_key = f"selected_option_{st.session_state.q_idx}"
            selected = st.radio(
                "Select an option:",
                current["options"],
            index=None,
            key=radio_key
        )
    elif current.get("question type") == "short answer":
        st.write(f"{current['question']}")
        text_key = f"short_answer_{st.session_state.q_idx}"
        st.text_area("Your Answer:", key=text_key, label_visibility="visible", help="Type your answer")
    elif current.get("question type") == "true/false":
        #st.write(f"Question {st.session_state.q_idx + 1}: {current['question']}")
        radio_key = f"true_false_{st.session_state.q_idx}"
        selected = st.radio(
            "Select True or False:",
            ["True", "False"],
            index=None,
            key=radio_key, use_container_width=True
        )
    elif current.get("question type") == "readout loud":
        st.write(f"{current['question']}")
        audio_file = text_to_speech(current['question'])
        st.audio(audio_file, format="audio/mp3")
        st.text_area("Your Answer:", key=f"readout_loud_{st.session_state.q_idx}")
     # Show Correct Answer button
    show_answer_key = f"show_answer_{st.session_state.q_idx}"
    if st.button("Show Correct Answer", key=show_answer_key, use_container_width=True):
        st.info(f"Correct Answer: {current['answer']}")
    #st.write(f"Question {idx+1}: {question['question']}")
    #st.write(f"Card: {question['card']}")
    rating_label = st.radio(
        "Select difficulty rating:",
        ["Easy", "Good", "Hard", "Unknown"],
        key=f"rating_{idx}",
        horizontal=True  # <-- This makes the radio button horizonta
    )

    if st.button("Submit Rating", use_container_width=True):
        # Map label to Rating enum
        rating_map = {
            "Easy": Rating.Easy,
            "Good": Rating.Good,
            "Hard": Rating.Hard,
            "Unknown": Rating.Again
        }
        rating = rating_map[rating_label]
        # Apply review process
        # Improvise the logic to show the questions that are rescheduled on the same day !
        card_data = apply_review(scheduler, current["card"], rating)
        # Update the card in the database but immediate update causes latency and user cannot see the next card
        # So we will update the card after showing the next card
        collection.update_one(
            {"_id": current["_id"]},
            {"$set": {"card": card_data, "anki": 1}}
        )
        questions = get_questions_due_today(collection, selected_tags)
        # Move to next question
        total_questions = len(questions)
        st.write(f"Total Questions due today: {total_questions}")
        if total_questions > 0 and st.session_state.anki_idx < total_questions - 1:
            st.session_state.anki_idx += 1
            st.rerun()
        elif total_questions > 0:
            # Reset index to show newly rescheduled cards
            st.session_state.anki_idx = 0
            st.rerun()

else:
    st.info("No questions found in the collection.")