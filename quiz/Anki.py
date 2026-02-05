# Create the Anki logic
#  https://github.com/open-spaced-repetition/anki-sm-2
from anki_sm_2 import Scheduler, Card, Rating
from datetime import datetime, timezone
import streamlit as st
import pymongo
from dotenv import load_dotenv
import os

st.set_page_config(
    page_title="Anki Study - Quiz App",
    page_icon="🧠",
    layout="centered",
    initial_sidebar_state="collapsed"
)

load_dotenv()
secret = os.getenv('SECRET')

# Initialize MongoDB client
client = pymongo.MongoClient("mongodb://localhost:32768/", username="myTester", password=secret)
db = client["test"]
collection = db["anki_collection"]

# --- Header ---
st.header("Anki Study Session")
st.caption("Spaced repetition learning with SM-2 algorithm")

# Test data to load into the database
test_data = [
    {
        "question": "What is the capital of France?",
        "answer": "Paris",
        "tags": ["geography", "europe"],
        "due": datetime.now(timezone.utc),
        "state": None
    },
    {
        "question": "What is 2 + 2?",
        "answer": "4",
        "tags": ["math", "arithmetic"],
        "due": datetime.now(timezone.utc),
        "state": None
    },
    {
        "question": "Who wrote Hamlet?",
        "answer": "Shakespeare",
        "tags": ["literature", "drama"],
        "due": datetime.now(timezone.utc),
        "state": None
    }
]

deck = test_data

# Initialize the scheduler
scheduler = Scheduler()

# Session state for pagination and review logs
if "anki_idx" not in st.session_state:
    st.session_state.anki_idx = 0
if "anki_review_logs" not in st.session_state:
    st.session_state.anki_review_logs = []

idx = st.session_state.anki_idx
total = len(deck)

# --- Progress ---
st.progress((idx) / total)
st.caption(f"Card {idx + 1} of {total}")

st.write("---")

card = deck[idx]

# --- Card display ---
st.markdown(f"### {card['question']}")
if card.get("tags"):
    st.caption(f"Tags: {', '.join(card['tags'])}")

user_answer = st.text_input("Your answer:", key=f"answer_{idx}", placeholder="Type your answer here...")

rating_label = st.radio(
    "How confident are you?",
    ["Easy", "Medium", "Hard"],
    key=f"rating_{idx}",
    horizontal=True
)

if st.button("Check Answer", type="primary"):
    if user_answer.strip().lower() == card["answer"].strip().lower():
        st.success(f"Correct! The answer is **{card['answer']}**.")
    else:
        st.error(f"Incorrect. The correct answer is **{card['answer']}**.")
        rating_label = "Again"

    # Map radio selection to SM-2 rating
    if rating_label == "Easy":
        rating = Rating.Easy
    elif rating_label == "Medium":
        rating = Rating.Good
    elif rating_label == "Hard":
        rating = Rating.Hard
    else:
        rating = Rating.Again

    card_obj = Card()
    card_obj, review_log = scheduler.review_card(card_obj, rating)
    st.session_state.anki_review_logs.append({
        "question": card["question"],
        "answer": card["answer"],
        "user_answer": user_answer,
        "rating": rating_label,
        "correct": user_answer.strip().lower() == card["answer"].strip().lower(),
        "next_due": str(card_obj.due),
        "tags": card.get("tags", [])
    })
    if idx < len(deck) - 1:
        st.session_state.anki_idx += 1
        st.rerun()
    else:
        st.session_state.anki_idx = 0
        st.success("Review session completed! Check the review log below.")

# --- Review Log ---
st.write("---")
if st.session_state.anki_review_logs:
    st.subheader(f"Review Log ({len(st.session_state.anki_review_logs)} reviews)")
    for i, log in enumerate(reversed(st.session_state.anki_review_logs)):
        icon = "✅" if log.get("correct") else "❌"
        with st.expander(f"{icon} {log['question'][:60]}"):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Your answer:** {log['user_answer']}")
                st.markdown(f"**Correct answer:** {log['answer']}")
            with col2:
                st.markdown(f"**Rating:** {log['rating']}")
                st.markdown(f"**Next due:** {log['next_due'][:10]}")
            if log.get("tags"):
                st.caption(f"Tags: {', '.join(log['tags'])}")

    if st.button("Clear Review Log"):
        st.session_state.anki_review_logs = []
        st.rerun()
else:
    st.caption("No reviews yet. Answer a question above to start.")
