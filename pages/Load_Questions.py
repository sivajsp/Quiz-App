import streamlit as st
import pandas as pd
import gtts
from App.Unified import get_db, get_headings, add_topic_subtopic, text_to_speech,load_questions_from_csv
if st.session_state.get("authenticated", False) is not True:
    st.warning("You must be logged in to access this page.")
    if st.button("Go to Login Page"):
        st.switch_page("login.py")
    st.stop()
mydb = get_db()
anki_col = mydb[st.session_state.anki_collection]
mycol = mydb[st.session_state.questions_collection]
st.set_page_config(initial_sidebar_state="collapsed")
hide_pages = """
    <style>
    [data-testid="stSidebarNav"] {display: none;}
    </style>
"""
st.markdown(hide_pages, unsafe_allow_html=True)
question_type = st.radio(
    "Select Question Type for Upload:",
    ["mcq", "short answer", "true/false", "readout loud"],
    index=0,
    key="upload_question_type"
)


headings = get_headings(mydb, config_collection=st.session_state.config_collection)
topics = sorted({h["topic"] for h in headings if "topic" in h})
subtopics_by_topic = {}
for h in headings:
    if "topic" in h and "subtopic" in h:
        subtopics_by_topic.setdefault(h["topic"], set()).update(h["subtopic"] if isinstance(h["subtopic"], list) else [h["subtopic"]])
# Define questions and options 
selected_topic = st.radio("Select Topic for Upload:", topics) if topics else None
selected_subtopics = []
if selected_topic:
    subtopics = sorted(subtopics_by_topic.get(selected_topic, []))
    selected_subtopics = st.multiselect("Select Subtopics for Upload:", subtopics) if subtopics else []
enable_anki = st.toggle("Upload the question into Anki deck", value=False)
target_col = anki_col if enable_anki else mycol 
st.write(f"Questions will be uploaded to collection: '{target_col.name}'")
uploaded_file = st.file_uploader("1. Upload your quiz CSV file", type=["csv"])


# Hierarchy selection UI


st.info("Enter Questions Manually")
# Define columns for your question type
columns = {
    "mcq": ["question", "option1", "option2", "option3", "option4", "answer"],
    "short answer": ["question", "answer"],
    "true/false": ["question", "answer"],
    "readout loud": ["question", "answer"]
}
selected_type = st.session_state.get("upload_question_type", question_type)
table_cols = columns[selected_type]
# Provide an empty DataFrame for user input
if (
    "manual_questions_type" not in st.session_state
    or st.session_state.manual_questions_type != selected_type
):
    st.session_state.manual_questions = pd.DataFrame(columns=table_cols)
    st.session_state.manual_questions_type = selected_type

edited_df = st.data_editor(
    st.session_state.manual_questions,
    num_rows="dynamic",
    use_container_width=True,
    key="manual_questions_editor"
)
st.session_state.manual_questions = edited_df # Update session state with edited DataFrame

if st.button("Save Table Questions to Database"):
    # Convert DataFrame to list of dicts, filter out empty rows
    questions = []
    for _, row in edited_df.iterrows():
        q = row.dropna().to_dict()
        if q.get("question") and q.get("answer"):
            # For MCQ, collect options
            if selected_type == "mcq":
                q["options"] = [q.get(f"option{i}") for i in range(1, 5) if q.get(f"option{i}")]
            q["question type"] = selected_type
            q["anki"] = 0
            questions.append(q)
    if questions:
        result = target_col.insert_many(questions)
        st.write(f"Saved {len(result.inserted_ids)} questions to the {target_col.name} database.")
        st.success(f"Saved {len(result.inserted_ids)} questions to the {target_col.name} database.")
    else:
        st.warning("No valid questions to save.")


if uploaded_file:
    tags = [selected_topic] if selected_topic else []
    tags += selected_subtopics
    questions = load_questions_from_csv(uploaded_file, question_type, tags)
    for q in questions:
        q["anki"] = 0
    count = len(questions)
    
    if st.button("Save Quiz to Database"):
        # Insert each question as a document
        result = target_col.insert_many(questions)
        st.success(f"Saved {len(result.inserted_ids)} questions to the {target_col.name}  database.")
# Initialize session state
    if "q_idx" not in st.session_state:
        st.session_state.q_idx = 0
    if "results" not in st.session_state:
        st.session_state.results = []
    if "submitted" not in st.session_state:
        st.session_state.submitted = False
    def record_answer():
        current = questions[st.session_state.q_idx]
        radio_key = f"selected_option_{st.session_state.q_idx}"
        selected = st.session_state.get(radio_key)
        if selected:
            st.session_state.results.append(selected == current["answer"])
    def next_question():
        record_answer()
        st.session_state.q_idx += 1       
# Display current question
# Show button to enable the practice mode
# practice mode lets the user view the correct answers after each question
    st.header("Load Questions for Quiz here")
    if "q_idx" not in st.session_state:
        st.session_state.q_idx = 0
    show_answer_key = f"show_answer_{st.session_state.q_idx}"
    if st.session_state.q_idx < len(questions):
        current = questions[st.session_state.q_idx]
        # Question Display logic
        if current.get("question type") == "mcq":
            st.write(f"Question {st.session_state.q_idx + 1}: {current['question']}")
            radio_key = f"selected_option_{st.session_state.q_idx}"
            selected = st.radio(
                "Select an option:",
                current["options"],
            index=None,
            key=radio_key
        )
        elif current.get("question type") == "short answer":
            st.write(f"Question {st.session_state.q_idx + 1}: {current['question']}")
            text_key = f"short_answer_{st.session_state.q_idx}"
            st.text_input("Your Answer:", key=text_key)
        elif current.get("question type") == "true/false":
            st.write(f"Question {st.session_state.q_idx + 1}: {current['question']}")
            radio_key = f"true_false_{st.session_state.q_idx}"
            selected = st.radio(
                "Select True or False:",
                ["True", "False"],
                index=None,
                key=radio_key
            )
        elif current.get("question type") == "readout loud":
            st.write(f"Question {st.session_state.q_idx + 1}: {current['question']}")
            audio_file = text_to_speech(current['question'])
            st.audio(audio_file, format="audio/mp3")
            st.text_input("Your Answer:", key=f"readout_loud_{st.session_state.q_idx}")
        if st.button("Show Correct Answer", key=show_answer_key):
            st.info(f"Correct Answer: {current['answer']}")

        if st.session_state.q_idx < len(questions) - 1:
            if st.button("Next Question"):
                next_question()
                st.rerun()
        else:
            if st.button("Submit"):
                record_answer()
                st.session_state.submitted = True
                st.rerun()
    if st.session_state.submitted:
        st.write("Thank you for completing the quiz!")
        st.write(f"You answered {sum(st.session_state.results)} out of {count} questions correctly.")
        st.button("Restart Quiz", on_click=lambda: st.session_state.clear())
        if st.button("Show Summary"):
            for i, res in enumerate(st.session_state.results):
                st.write(f"Question {i + 1}: {'Correct' if res else 'Incorrect'}")


# Step 1: Define hierarchy levels
st.info("Create Hierarchy Tags")
hierarchy_levels = ["Topic", "Subtopic"]
hierarchy = {}
selected_collection = st.session_state.questions_collection
for level in hierarchy_levels:
    hierarchy[level] = st.text_input(f"Enter {level} name:", key=f"hierarchy_{level}")
if st.button("Save Hierarchy"):
    topic = hierarchy.get("Topic", "").strip()
    subtopic = hierarchy.get("Subtopic", "").strip()
    if topic and subtopic:
        add_topic_subtopic(mydb, topic, subtopic)
        st.session_state.hierarchy_tags = [topic, subtopic]
        st.success(f"Hierarchy set: {st.session_state.hierarchy_tags}")
    else:
        st.warning("Please enter both topic and subtopic.")