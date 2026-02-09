# This is the Overview section and it provide the collection of quiz question available in the database
# It has option to create the New Collection of quiz and it creates the equivalent collection in the database
import streamlit as st
from pymongo.errors import ServerSelectionTimeoutError
import json
from App.Unified import get_db, get_headings, add_n_cards_to_anki_collection
# if user role is admin, show all collections else show only user specific collections
def delete_topic_subtopic_from_db(mydb, topic, subtopic):
    query = {"topic": topic}
    if subtopic != "None":
        query["subtopic"] = subtopic
    result = selected_collection.delete_many(query)
    return result.deleted_count
def delete_tag(topic, subtopic):
    res = config_collection.update_one({"topic": topic}, {"$pull": {"subtopic": subtopic}})
    return res.modified_count

st.set_page_config(initial_sidebar_state="collapsed")
hide_pages = """
    <style>
    [data-testid="stSidebarNav"] {display: none;}
    </style>
"""
st.markdown(hide_pages, unsafe_allow_html=True)
col_left, col_right = st.columns([10, 3])
with col_right:
    if st.button("Manual", key="user_manual_btn"):
        # Switch to your user manual page. Adjust path/name if your file differs.
        st.switch_page("pages/user-manual.py")

if st.session_state.get("authenticated", False) is not True:
    st.warning("You must be logged in to access this page.")
    if st.button("Go to Login Page"):
        st.switch_page("login.py")
    st.stop()
if st.session_state.role == "admin":
    if st.button("User Management Page"):
        st.switch_page("pages/user-mgmt.py")
    
try:
    mydb = get_db()
    config_collection = mydb[st.session_state.config_collection]
    selected_collection = mydb[st.session_state.questions_collection]
    anki_collection = mydb[st.session_state.anki_collection]
    headings = get_headings(mydb, config_collection=st.session_state.config_collection)
except ServerSelectionTimeoutError:
    st.error("Database connection timed out. Please check your connection and try again.")
    st.stop()
#st.write(st.session_state.config_collection, st.session_state.questions_collection, st.session_state.anki_collection)



st.subheader("Overview - Quiz Collections")
# Extract unique topics and subtopics
topics = sorted({h["topic"] for h in headings if "topic" in h})
subtopics_by_topic = {}
for h in headings:
    if "topic" in h and "subtopic" in h:
        subtopics_by_topic.setdefault(h["topic"], set()).update(h["subtopic"] if isinstance(h["subtopic"], list) else [h["subtopic"]])

selected_topic = st.radio("Select Topic:", topics) if topics else None
selected_subtopic = None
if selected_topic and selected_topic != "None":
    subtopics = sorted(subtopics_by_topic.get(selected_topic, []))
    selected_subtopic = st.radio("Select Subtopic:", subtopics, index=0)
else:
    selected_subtopic = "None"


#st.info(f"Collection '{selected_collection}' has {count} questions.")
st.session_state.hierarchy_tags = [selected_topic, selected_subtopic] if selected_topic and selected_subtopic else [None, None]
# persist hierarchy_tags into browser localStorage


# Action buttons
#st.write("Current hierarchy tags:", st.session_state.hierarchy_tags)
col1,col2, col3, col4 = st.columns(4)
with col1:
    if st.button("Upload"):
        st.switch_page("pages/Load_Questions.py")
with col2:
    if st.button("List"):
        st.switch_page("pages/List_Question.py")
with col3:
    if st.button("Start Quiz"):
        st.switch_page("pages/Load_Quiz.py")
with col4:
    if st.button("Delete Collection"):
        if selected_topic:
            deleted_count = delete_topic_subtopic_from_db(mydb, selected_topic, selected_subtopic)
            res = delete_tag(selected_topic, selected_subtopic)
            st.success(f"Deleted {deleted_count} questions from Topic: '{selected_topic}' Subtopic: '{selected_subtopic}'")
            st.rerun()
        

st.subheader("Anki Section")
col1,col2 = st.columns(2)
with col1:
    if st.button("Goto Anki Quiz"):
        st.switch_page("pages/Anki-Quiz.py")
with col2:
    if st.button("Add Cards to Anki"):
        count = add_n_cards_to_anki_collection(selected_collection, st.session_state.hierarchy_tags, anki_collection=anki_collection)
        st.success(f"Added {count} cards from '{st.session_state.hierarchy_tags}' to Anki collection with anki=0.")