# Create the Anki logic
#  https://github.com/open-spaced-repetition/anki-sm-2
from anki_sm_2 import Scheduler, Card, Rating
from datetime import datetime, timezone
import streamlit as st
import pymongo
from App.Unified import get_db,text_to_speech,apply_review,update_anki_cards_flag,get_questions_due_today,load_questions_from_mongo
# Initialize MongoDB client
db = get_db()
collection = db["anki_collection"]
selected_tags = ['Vocabulary','1000 words']
questions = load_questions_from_mongo(collection, limit=10, selected_tags=selected_tags)
print(list(questions)[1])