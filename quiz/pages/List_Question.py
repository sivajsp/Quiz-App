import streamlit as st
import pandas as pd
import pymongo
from bson import ObjectId
from dotenv import load_dotenv
import os

st.set_page_config(
    page_title="Questions - Quiz App",
    page_icon="📋",
    layout="centered",
    initial_sidebar_state="collapsed"
)

load_dotenv()
secret = os.getenv('SECRET')

myclient = pymongo.MongoClient("mongodb://localhost:32768/", username="myTester", password=secret)
mydb = myclient["test"]

collection_name = st.session_state.get("selected_collection", None)
if not collection_name:
    st.warning("No collection selected. Please go back and select one.")
    if st.button("← Back to Overview"):
        st.switch_page("Overview.py")
    st.stop()

mycol = mydb[collection_name]

# --- Back navigation ---
if st.button("← Back to Overview"):
    st.switch_page("Overview.py")

st.header(f"Questions in: {collection_name}")

# Pagination controls
total_questions = mycol.count_documents({})
st.caption(f"{total_questions} question{'s' if total_questions != 1 else ''} total")

if total_questions == 0:
    st.info("No questions found in this collection. Upload some questions first.")
    st.stop()

page_size = st.selectbox("Questions per page:", [20, 30, 50], index=0)
total_pages = max(1, (total_questions + page_size - 1) // page_size)

if "page_num" not in st.session_state:
    st.session_state.page_num = 1

# Clamp page number to valid range
if st.session_state.page_num > total_pages:
    st.session_state.page_num = total_pages

col_prev, col_page, col_next = st.columns([1, 2, 1])
with col_prev:
    if st.button("← Previous", disabled=st.session_state.page_num <= 1):
        st.session_state.page_num -= 1
        st.rerun()
with col_page:
    st.markdown(
        f"<div style='text-align:center; padding-top:0.5rem;'>Page {st.session_state.page_num} of {total_pages}</div>",
        unsafe_allow_html=True
    )
with col_next:
    if st.button("Next →", disabled=st.session_state.page_num >= total_pages):
        st.session_state.page_num += 1
        st.rerun()

st.write("---")

# Fetch questions for current page
skip = (st.session_state.page_num - 1) * page_size
questions = list(mycol.find().skip(skip).limit(page_size))

if questions:
    for idx, q in enumerate(questions):
        q_num = skip + idx + 1
        q_type = q.get("question type", "unknown")
        type_badge = {"mcq": "🔘", "short answer": "✏️", "true/false": "✅", "readout loud": "🔊"}.get(q_type, "❓")

        with st.expander(f"{type_badge} Q{q_num}: {q['question'][:80]}{'...' if len(q['question']) > 80 else ''}"):
            st.markdown(f"**Question:** {q['question']}")

            if q_type == "mcq" and "options" in q:
                st.markdown("**Options:**")
                for i, opt in enumerate(q.get("options", [])):
                    prefix = "→" if opt == q.get("answer") else " "
                    st.markdown(f"{prefix} {chr(65+i)}. {opt}")
            st.markdown(f"**Answer:** {q['answer']}")
            st.caption(f"Type: {q_type}")

            action_col1, action_col2 = st.columns(2)
            with action_col1:
                if st.button("Edit", key=f"edit_{q_num}"):
                    st.session_state.edit_id = str(q['_id'])
                    st.session_state.edit_data = {
                        "question": q["question"],
                        "options": q.get("options", []),
                        "answer": q["answer"],
                        "question type": q.get("question type", "")
                    }
                    st.session_state.edit_idx = q_num
                    st.rerun()
            with action_col2:
                if st.button("Delete", key=f"del_{q_num}"):
                    st.session_state.confirm_delete_q = str(q["_id"])
                    st.session_state.confirm_delete_q_num = q_num
                    st.rerun()

    # Delete confirmation
    if st.session_state.get("confirm_delete_q"):
        q_num = st.session_state.get("confirm_delete_q_num", "?")
        st.warning(f"Are you sure you want to delete Question {q_num}?")
        d_col1, d_col2, _ = st.columns([1, 1, 2])
        with d_col1:
            if st.button("Yes, delete", type="primary"):
                mycol.delete_one({"_id": ObjectId(st.session_state.confirm_delete_q)})
                st.session_state.pop("confirm_delete_q", None)
                st.session_state.pop("confirm_delete_q_num", None)
                st.rerun()
        with d_col2:
            if st.button("Cancel", key="cancel_delete_q"):
                st.session_state.pop("confirm_delete_q", None)
                st.session_state.pop("confirm_delete_q_num", None)
                st.rerun()

    # Edit form
    if st.session_state.get("edit_id"):
        st.write("---")
        st.subheader(f"Edit Question {st.session_state.edit_idx}")
        edit_data = st.session_state.edit_data
        q_type = edit_data.get("question type", "")

        new_question = st.text_area("Question", value=edit_data["question"], height=100)

        # Only show options for MCQ type
        new_options = []
        if q_type == "mcq" and edit_data.get("options"):
            st.markdown("**Options:**")
            for i, opt in enumerate(edit_data["options"]):
                new_opt = st.text_input(f"Option {chr(65+i)}", value=opt, key=f"edit_option_{i}")
                new_options.append(new_opt)

        new_answer = st.text_input("Answer", value=edit_data["answer"])

        new_question_type = st.selectbox(
            "Question Type",
            ["mcq", "short answer", "true/false", "readout loud"],
            index=["mcq", "short answer", "true/false", "readout loud"].index(q_type) if q_type in ["mcq", "short answer", "true/false", "readout loud"] else 0
        )

        save_col, cancel_col = st.columns(2)
        with save_col:
            if st.button("Save Changes", type="primary"):
                update_doc = {
                    "question": new_question,
                    "answer": new_answer,
                    "question type": new_question_type
                }
                if new_question_type == "mcq" and new_options:
                    update_doc["options"] = new_options
                mycol.update_one(
                    {"_id": ObjectId(st.session_state.edit_id)},
                    {"$set": update_doc}
                )
                st.success("Question updated.")
                del st.session_state.edit_id
                del st.session_state.edit_data
                del st.session_state.edit_idx
                st.rerun()
        with cancel_col:
            if st.button("Cancel Edit"):
                del st.session_state.edit_id
                del st.session_state.edit_data
                del st.session_state.edit_idx
                st.rerun()
