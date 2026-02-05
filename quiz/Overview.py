# This is the Overview section and it provide the collection of quiz question available in the database
# It has option to create the New Collection of quiz and it creates the equivalent collection in the database
import streamlit as st
import pandas as pd
import pymongo
from dotenv import load_dotenv
import os
import random

st.set_page_config(
    page_title="Quiz App",
    page_icon="📝",
    layout="centered",
    initial_sidebar_state="collapsed"
)

load_dotenv()
secret = os.getenv('SECRET')

# Connect to MongoDB
myclient = pymongo.MongoClient("mongodb://localhost:32768/", username="myTester", password=secret)
mydb = myclient["test"]

# --- Custom CSS ---
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        color: #666;
        font-size: 1rem;
        margin-bottom: 1.5rem;
    }
    .collection-card {
        background: #f8f9fa;
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.8rem;
    }
    .stat-number {
        font-size: 1.8rem;
        font-weight: 700;
        color: #4F8BF9;
    }
    .stat-label {
        font-size: 0.85rem;
        color: #888;
    }
    div.stButton > button {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# --- Header ---
st.markdown('<div class="main-header">Quiz App</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Create, manage, and take quizzes from your question bank</div>', unsafe_allow_html=True)

# --- Filter out system/internal collections ---
SYSTEM_COLLECTIONS = {"system.views", "system.buckets", "anki_collection"}
all_collections = mydb.list_collection_names()
collections = [c for c in all_collections if c not in SYSTEM_COLLECTIONS]
collections.sort()

# --- Stats row ---
col_stat1, col_stat2 = st.columns(2)
with col_stat1:
    st.markdown(f'<div class="stat-number">{len(collections)}</div><div class="stat-label">Collections</div>', unsafe_allow_html=True)
with col_stat2:
    total_q = sum(mydb[c].count_documents({}) for c in collections) if collections else 0
    st.markdown(f'<div class="stat-number">{total_q}</div><div class="stat-label">Total Questions</div>', unsafe_allow_html=True)

st.write("---")

# --- Collection list ---
selected_collection = None
if collections:
    st.subheader("Your Collections")

    selected_collection = st.radio(
        "Select a collection to work with:",
        collections,
        index=0,
        label_visibility="collapsed"
    )
    col = mydb[selected_collection]
    count = col.count_documents({})

    # Show selected collection info
    st.info(f"**{selected_collection}** — {count} question{'s' if count != 1 else ''}")

    # Action buttons
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("📤 Upload", help="Upload questions from a CSV file"):
            st.session_state.selected_collection = selected_collection
            st.switch_page("pages/Load_Questions.py")
    with col2:
        if st.button("📋 List", help="Browse and edit questions"):
            st.session_state.selected_collection = selected_collection
            st.switch_page("pages/List_Question.py")
    with col3:
        if st.button("▶️ Start Quiz", help="Take a quiz from this collection"):
            st.session_state.selected_collection = selected_collection
            st.switch_page("pages/Load_Quiz.py")
    with col4:
        if st.button("🗑️ Delete", help="Permanently delete this collection"):
            st.session_state.confirm_delete = selected_collection

    # Delete confirmation dialog
    if st.session_state.get("confirm_delete"):
        coll_to_delete = st.session_state.confirm_delete
        st.warning(f"Are you sure you want to delete **{coll_to_delete}**? This cannot be undone.")
        confirm_col1, confirm_col2, _ = st.columns([1, 1, 2])
        with confirm_col1:
            if st.button("Yes, delete it", type="primary"):
                mydb[coll_to_delete].drop()
                st.session_state.pop("confirm_delete", None)
                st.rerun()
        with confirm_col2:
            if st.button("Cancel"):
                st.session_state.pop("confirm_delete", None)
                st.rerun()
else:
    st.info("No quiz collections found. Create one below to get started.")

# --- Create new collection ---
st.write("---")
with st.expander("➕ Create New Collection", expanded=not bool(collections)):
    new_collection_name = st.text_input("Collection name:", placeholder="e.g. Biology Chapter 5")
    if st.button("Create Collection"):
        if new_collection_name:
            if new_collection_name in collections:
                st.error("A collection with this name already exists.")
            else:
                mydb.create_collection(new_collection_name)
                st.success(f"Collection **{new_collection_name}** created.")
                st.rerun()
        else:
            st.warning("Please enter a collection name.")
