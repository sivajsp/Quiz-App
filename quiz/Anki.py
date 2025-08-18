# Create the Anki logic
#  https://github.com/open-spaced-repetition/anki-sm-2
from anki_sm_2 import Scheduler, Card, Rating
from datetime import datetime, timezone
import streamlit as st
import pymongo
from dotenv import load_dotenv
import os
load_dotenv()
secret = os.getenv('SECRET')
# Initialize MongoDB client
client = pymongo.MongoClient("mongodb://localhost:32768/", username = "myTester", password = secret)
db = client["test"]
collection = db["anki_collection"]

# ...existing code...

# Test data to load into the database

# Insert test data into the database if collection is empty
# ...existing code...
# Load existing cards from the database
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
#for doc in collection.find():
#    card_data = {
#       "id": str(doc.get("_id", "")),
#        "question": doc.get("question", ""),
#        "answer": doc.get("answer", ""),
#        "tags": doc.get("tags", []),
#       "due": doc.get("due", datetime.now(timezone.utc)),
#        "state": doc.get("state", None)  # SM-2 expects a state field
#    }
#    deck.append(Card.from_dict(card_data))
#if not deck:
#    st.warning("No cards found in the collection. Please add cards to start the quiz.")
# Initialize the scheduler
scheduler = Scheduler()

# Session state for pagination and review logs
if "anki_idx" not in st.session_state:
    st.session_state.anki_idx = 0
if "anki_review_logs" not in st.session_state:
    st.session_state.anki_review_logs = []
idx = st.session_state.anki_idx
card = deck[idx]
st.write(f"Q{idx+1}: {card.question}")
user_answer = st.text_input(f"Your answer for Q{idx+1}", key=f"answer_{idx}")
rating_label = st.radio(
    "How easy was this card?",
    ["Easy", "Medium", "Hard"],
    key=f"rating_{idx}"
)

if st.button("Check"):
    if user_answer.strip().lower() == card.answer.strip().lower():
        st.success("Correct!")
    else:
        st.error(f"Incorrect! Correct answer: {card.answer}")
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
    card, review_log = scheduler.review_card(card, rating)
    st.session_state.anki_review_logs.append({
        "question": card.question,
        "answer": card.answer,
        "user_answer": user_answer,
        "rating": rating_label,
        "next_due": str(card.due),
        "review_log": review_log,
        "tags": getattr(card, "tags", [])
    })
    if idx < len(deck) - 1:
        st.session_state.anki_idx += 1
        st.rerun()
    else:
        st.session_state.anki_idx = 0
        st.success("Review session completed!")

# Show review log at the bottom
st.write("---")
st.subheader("Review Log")
for log in st.session_state.anki_review_logs:
    st.write(f"Q: {log['question']}")
    st.write(f"Your Answer: {log['user_answer']}")
    st.write(f"Correct Answer: {log['answer']}")
    st.write(f"Rating: {log['rating']}")
    st.write(f"Next Due: {log['next_due']}")
    st.write(f"Review Log: {log['review_log']}")
    st.write("---")