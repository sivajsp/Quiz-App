# This is the Overview section and it provide the collection of quiz question available in the database
# It has option to create the New Collection of quiz and it creates the equivalent collection in the database
import streamlit as st
import pandas as pd
import pymongo
from dotenv import load_dotenv
import os
import random
load_dotenv()
secret = os.getenv('SECRET')
# ...existing code...

# Connect to MongoDB
myclient = pymongo.MongoClient("mongodb://localhost:32768/", username="myTester", password=secret)
mydb = myclient["test"]



# List collections in the database
collections = mydb.list_collection_names()
st.subheader("Available Quiz Collections")

selected_collection = None
if collections:
    selected_collection = st.radio(
        "Select a quiz collection:",
        collections,
        index=0
    )
    col = mydb[selected_collection]
    count = col.count_documents({})
    st.info(f"Collection '{selected_collection}' has {count} questions.")

    # Action buttons
    st.write("---")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("Upload"):
            st.session_state.selected_collection = selected_collection
            st.switch_page("pages/Load_Questions.py")
    with col2:
        if st.button("List"):
            st.session_state.selected_collection = selected_collection
            st.switch_page("pages/List_Question.py")
    with col3:
        if st.button("Start Quiz"):
            st.session_state.selected_collection = selected_collection
            st.switch_page("pages/Load_Quiz.py")
    with col4:
        if st.button("Delete"):
            col.drop()
            st.error(f"Collection '{selected_collection}' deleted.")
            st.rerun()
else:
    st.info("No quiz collections found in the database.")
if st.button("Create New Collection"):
    st.session_state.show_create = True

if st.session_state.get("show_create", False):
    new_collection_name = st.text_input("Enter new collection name:")
    if st.button("Add Collection"):
        if new_collection_name:
            if new_collection_name in collections:
                st.error("Collection already exists.")
            else:
                mydb.create_collection(new_collection_name)
                st.success(f"Collection '{new_collection_name}' created.")
                st.session_state.show_create = False
                st.rerun()
        else:
            st.warning("Please enter a collection name.")

# ...existing code...

# ...existing code...