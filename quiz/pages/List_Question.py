import streamlit as st
import pandas as pd
import pymongo
from dotenv import load_dotenv
import os
load_dotenv()
secret = os.getenv('SECRET')

myclient = pymongo.MongoClient("mongodb://localhost:32768/", username = "myTester", password = secret)
mydb = myclient["test"]
mycol = mydb[st.session_state.selected_collection]
collection_name = st.session_state.get("selected_collection", "Quiz-test")
mycol = mydb[collection_name]

st.header(f"Questions in Collection: {collection_name}")
# Pagination controls
page_size = st.radio("Questions per page:", [20, 30, 50], index=0)
total_questions = mycol.count_documents({})
total_pages = (total_questions + page_size - 1) // page_size

if "page_num" not in st.session_state:
    st.session_state.page_num = 1

col_prev, col_page, col_next = st.columns([1, 2, 1])
with col_prev:
    if st.button("Previous") and st.session_state.page_num > 1:
        st.session_state.page_num -= 1
        st.rerun()
with col_page:
    page_options = [f"Page {i+1}" for i in range(total_pages)]
    selected_page = st.selectbox("Go to page:", page_options, index=st.session_state.page_num - 1)
    new_page_num = page_options.index(selected_page) + 1
    if new_page_num != st.session_state.page_num:
        st.session_state.page_num = new_page_num
        st.rerun()
with col_next:
    if st.button("Next") and st.session_state.page_num < total_pages:
        st.session_state.page_num += 1
        st.rerun()
# Fetch questions for current page
skip = (st.session_state.page_num - 1) * page_size
questions = list(mycol.find().skip(skip).limit(page_size))

if questions:
    question_labels = [f"{skip + idx + 1}. {q['question']}" for idx, q in enumerate(questions)]
    selected_idx = st.radio("Select a question to edit or delete:", question_labels, index=0)
    selected_question = questions[question_labels.index(selected_idx)]

    st.write("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Edit Selected Question"):
            st.session_state.edit_id = str(selected_question['_id'])
            st.session_state.edit_data = {
                "question": selected_question["question"],
                "options": selected_question["options"],
                "answer": selected_question["answer"],
                "question type": selected_question.get("question type", "")
            }
            st.session_state.edit_idx = skip + question_labels.index(selected_idx) + 1
            st.rerun()
    with col2:
        if st.button("Delete Selected Question"):
            mycol.delete_one({"_id": selected_question["_id"]})
            st.success(f"Question deleted.")
            st.rerun()

    # Edit form
    if st.session_state.get("edit_id"):
        st.subheader(f"Edit Question {st.session_state.edit_idx}")
        edit_data = st.session_state.edit_data
        new_question = st.text_input("Question", value=edit_data["question"])
        new_options = []
        for i, opt in enumerate(edit_data["options"]):
            new_opt = st.text_input(f"Option {i+1}", value=opt, key=f"edit_option_{i}")
            new_options.append(new_opt)
        new_answer = st.text_input("Answer", value=edit_data["answer"])
        new_question_type = st.text_input("Question Type", value=edit_data.get("question type", ""))
        if st.button("Update Question"):
            mycol.update_one(
                {"_id": pymongo.ObjectId(st.session_state.edit_id)},
                {"$set": {
                    "question": new_question,
                    "options": new_options,
                    "answer": new_answer,
                    "question type": new_question_type
                }}
            )
            st.success("Question updated.")
            del st.session_state.edit_id
            del st.session_state.edit_data
            del st.session_state.edit_idx
            st.experimental_rerun()
        if st.button("Cancel Edit"):
            del st.session_state.edit_id
            del st.session_state.edit_data
            del st.session_state.edit_idx
            st.rerun()
else:
    st.info("No questions found in this collection.")
