import streamlit as st
import pandas as pd
from App.Unified import get_db
if st.session_state.get("authenticated", False) is not True:
    st.warning("You must be logged in to access this page.")
    if st.button("Go to Login Page"):
        st.switch_page("login.py")
    st.stop()
mydb = get_db()
st.write(st.session_state.questions_collection, st.session_state.anki_collection, st.session_state.config_collection)
mycol = mydb[st.session_state.questions_collection]
st.set_page_config(initial_sidebar_state="collapsed")
def get_headings():
    myconfig = mydb[st.session_state.config_collection]
    # Each document should have "topic" and "subtopic" fields
    return list(myconfig.find({}, {"_id": 0, "topic": 1, "subtopic": 1}))
headings = get_headings()
topics = sorted({h["topic"] for h in headings if "topic" in h})
subtopics_by_topic = {}
for h in headings:
    if "topic" in h and "subtopic" in h:
        subtopics_by_topic.setdefault(h["topic"], set()).update(h["subtopic"] if isinstance(h["subtopic"], list) else [h["subtopic"]])
st.subheader(f"Questions in Topic: {st.session_state.hierarchy_tags}")

# Fetch questions for current page
selected_tags = []
if "hierarchy_tags" in st.session_state:
    selected_tags = st.session_state.hierarchy_tags

# Pagination controls 
if "page_num" not in st.session_state:
    st.session_state.page_num = 1

page_size = st.radio("Questions per page:", [20, 30, 50], index=0)
if selected_tags:
    # Find questions that have all selected tags
    filter_query = {"tags": {"$all": selected_tags}}
    total_questions = mycol.count_documents(filter_query)
    total_pages = (total_questions + page_size - 1) // page_size
    skip = (st.session_state.page_num - 1) * page_size
    questions = list(mycol.find(filter_query).skip(skip).limit(page_size))
else:
    # Default: show all questions
    total_questions = mycol.count_documents({})
    total_pages = (total_questions + page_size - 1) // page_size
    skip = (st.session_state.page_num - 1) * page_size
    questions = list(mycol.find().skip(skip).limit(page_size))
total_pages = (total_questions + page_size - 1) // page_size
if total_questions == 0:
    st.info("No questions found for the selected topic/subtopic.")
    st.stop()
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

if questions:
    question_labels = [f"{skip + idx + 1}. {q['question']}" for idx, q in enumerate(questions)]
    selected_idx = st.radio("Select a question to edit or delete:", question_labels, index=0)
    selected_question = questions[question_labels.index(selected_idx)]

    st.write("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Edit Selected Question"):
            st.session_state.edit_id = str(selected_question['_id'])
            if selected_question.get("question type") =="mcq":
                st.session_state.edit_data = {
                    "question": selected_question["question"],
                    "options": selected_question["options"],
                    "answer": selected_question["answer"],
                    "question type": selected_question.get("question type", ""),
                    "tags": selected_question.get("tags")
            }
            else:
                st.session_state.edit_data = {
                    "question": selected_question["question"],
                    "answer": selected_question["answer"],
                    "question type": selected_question.get("question type", ""),
                    "tags": selected_question.get("tags")
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
        if edit_data.get("question type") == "mcq":
            new_options = []
            for i, opt in enumerate(edit_data["options"]):
                new_opt = st.text_input(f"Option {i+1}", value=opt, key=f"edit_option_{i}")
                new_options.append(new_opt)
        new_answer = st.text_input("Answer", value=edit_data["answer"])
        new_question_type = st.text_input("Question Type", value=edit_data.get("question type", ""))
        # Hierarchical tag selection: topic then subtopic
        selected_topic = st.radio("Select Topic:", topics, index=topics.index(edit_data.get("tags", [None])[0]) if edit_data.get("tags") else 0) if topics else None
        selected_subtopics = []
        if selected_topic:
            subtopics = sorted(subtopics_by_topic.get(selected_topic, []))
            # Preselect subtopics if present in edit_data tags
            if edit_data.get("tags"):
                default_subtopics = [tag for tag in edit_data.get("tags", []) if tag in subtopics]
            else:
                default_subtopics = []
            selected_subtopics = st.multiselect(
                "Select Subtopics:",
                options=subtopics,
                default=default_subtopics
            )

        # Combine topic and subtopics for tags
        updated_tags = [selected_topic] if selected_topic else []
        updated_tags += selected_subtopics

        if st.button("Update Question"):
            mycol.update_one(
                {"_id": ObjectId(st.session_state.edit_id)},
                {"$set": {
                    "question": new_question,
                    "options": new_options,
                    "answer": new_answer,
                    "question type": new_question_type,
                    "tags": updated_tags
                }}
            )
            st.success("Question updated.")
            del st.session_state.edit_id
            del st.session_state.edit_data
            del st.session_state.edit_idx
            st.rerun()
        if st.button("Cancel Edit"):
            del st.session_state.edit_id
            del st.session_state.edit_data
            del st.session_state.edit_idx
            st.rerun()
else:
    st.info("No questions found in this collection.")