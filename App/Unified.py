import pymongo
from dotenv import load_dotenv
import os
from urllib.parse import quote_plus
import random
import gtts
from anki_sm_2 import Scheduler, Card, Rating, ReviewLog
import pandas as pd
import streamlit as st
import io
import datetime
from datetime import datetime, timezone

load_dotenv()
#username = quote_plus(os.getenv('local_user'))
#secret = quote_plus(os.getenv('local_secret'))
SERVER = os.getenv('SERVER')
username = quote_plus(os.getenv('UNAME'))
secret = quote_plus(os.getenv('SECRET'))
connectionstring = f"mongodb+srv://{username}:{secret}@{SERVER}/?retryWrites=true&w=majority&appName=quiz"
#connectionstring = f"mongodb://{username}:{secret}@localhost:32768/?authSource=test"

def get_db():
    client = pymongo.MongoClient(connectionstring)
    return client["Quiz"]
def get_headings(mydb, config_collection="config"):
    myconfig = mydb[config_collection]
    # Each document should have "topic" and "subtopic" fields
    return list(myconfig.find({}, {"_id": 0, "topic": 1, "subtopic": 1}))
def add_n_cards_to_anki_collection(selected_collection, selected_tags=None,anki_collection=None):
    """
    Add n cards from the selected source collection to the anki_collection.
    Each card will have 'anki' = 0.
    """
    # Filter documents by selected tags
    docs = list(selected_collection.find({"tags": {"$all": selected_tags}})) 
    
    added_count = 0
    for doc in docs:
        # Prepare the new card document
        new_card = {
            "question": doc.get("question", ""),
            "answer": doc.get("answer", ""),
            "tags": doc.get("tags", []),
            "anki": 0
        }
        # Add options and question type if present
        if "options" in doc:
            new_card["options"] = doc["options"]
        if "question type" in doc:
            new_card["question type"] = doc["question type"]
        # Insert into anki_collection
        anki_collection.insert_one(new_card)
        added_count += 1
    return added_count
def load_questions_from_mongo(mycol, limit=None, selected_tags=None):
    questions = []
    # Build filter for selected tags
    filter_query = {}
    if limit is None:
        if selected_tags:
            filter_query = {"tags": {"$all": selected_tags}}
        questions= mycol.find(filter_query)
    else:
        if selected_tags:
            filter_query = {"tags": {"$all": selected_tags}}
        questions= mycol.find(filter_query).limit(limit)
    return questions
def text_to_speech(text):
    """
    Return a BytesIO audio file for the given text or None on error.
    Defensive: converts non-string inputs, rejects empty/boolean, and catches gTTS errors.
    """
    try:
        # reject None / empty early
        if text is None:
            return None
        # Avoid boolean being treated as text (bool has no strip)
        if isinstance(text, bool):
            text = str(text)
        text = str(text).strip()
        if not text:
            return None

        tts = gtts.gTTS(text, lang='nl', slow=False)
        audio_file = io.BytesIO()
        tts.write_to_fp(audio_file)
        audio_file.seek(0)
        return audio_file
    except Exception as e:
        # don't raise in UI code; return None so caller can handle missing audio
        try:
            st.warning(f"Text-to-speech failed: {e}")
        except Exception:
            pass
        return None
def add_topic_subtopic(mydb, topic, subtopic):
    myconfig = mydb[st.session_state.config_collection]
    # Check if topic exists
    topic_doc = myconfig.find_one({"topic": topic})
    if not topic_doc:
        # Topic not present, add new topic with subtopic as list
        myconfig.insert_one({"topic": topic, "subtopic": [subtopic]})
    else:
        # Topic exists, check if subtopic is present
        subtopics = topic_doc.get("subtopic", [])
        if subtopic in subtopics:
            st.warning("It already exists.")
        else:
            # Add new subtopic to existing topic
            myconfig.update_one(
                {"topic": topic},
                {"$push": {"subtopic": subtopic}}
            )
def load_questions_from_csv(file, question_type, tags):
    df = pd.read_csv(file, on_bad_lines='skip')
    if question_type == "mcq":        
        questions = []
        for _, row in df.iterrows():
            options = [row[col] for col in row.index if col.startswith("option_") and pd.notna(row[col])]
            question = {
                "question": row["question"],
                "options": options,
                "answer": row["answer"],
                "question type": "mcq",
                "tags": tags
            }
            questions.append(question)
    elif question_type == "short answer":
        questions = []
        for _, row in df.iterrows():
            question = {
                "question": row["question"],
                "answer": row["answer"],
                "question type": "short answer",
                "tags": tags
            }
            questions.append(question)
    elif question_type == "true/false":
        questions = []
        for _, row in df.iterrows():
            question = {
                "question": row["question"],
                "answer": row["answer"],
                "question type": "true/false",
                "tags": tags
            }
            questions.append(question)
    elif question_type == "readout loud":
        questions = []
        for _, row in df.iterrows():
            question = {
                "question": row["question"],
                "answer": row["answer"],
                "question type": "readout loud",
                "tags": tags
            }
            questions.append(question)
    else:
        return []
    return questions
def get_questions_due_today(collection, selected_tags):
    today = datetime.now(timezone.utc).date()
    # Build filter for due date before or on today
    filter_query = {
        "card.due": {"$lte": today.isoformat()}
    }
    # Use $regex for today and $lt for before today
    filter_query = {
        "$or": [
            {"card.due": {"$regex": f"^{today.isoformat()}"}},
            {"card.due": {"$lt": today.isoformat()}}
        ]
    }
    if selected_tags:
        filter_query["tags"] = {"$all": selected_tags}
    return list(collection.find(filter_query))
def update_anki_cards_flag(collection,n, selected_tags):
    #update only n cards in the collection where anki == 0, set anki = 1 and assign a new card
    #Need to improvise the logic to do the flagging for every n cards in the each tags !
    docs = list(collection.find({"anki": 0, "tags": {"$all": selected_tags}}).limit(n))
    updated_count = 0
    for doc in docs:
        card = Card()
        collection.update_one(
            {"_id": doc["_id"]},
            {"$set": {"anki": 1, "card": card.to_dict()}}
        )
        updated_count += 1
    return updated_count

def apply_review(scheduler, card_data, rating):
    card = Card.from_dict(card_data)
    card, review_log = scheduler.review_card(card, rating)
    card_dict = card.to_dict()
    return card_dict