import streamlit as st
st.set_page_config(initial_sidebar_state="collapsed")                                                                                            
hide_pages = """
    <style>
    [data-testid="stSidebarNav"] {display: none;}
    </style>
"""
st.markdown("# User Manual")
st.markdown("""
Once logged in, you will be landed onto the Overview pages which will show all the quiz collection that you created and have access.
""")
st.subheader("1.	Tags (Topic / Subtopic) —")
st.markdown("""Prior to uploading questions you must create and assign the topic / subtopic for the questions that you want to upload.
""")
st.markdown("#### 1.	Create a Topic/Subtopic:")
st.markdown(""" 
    1.	Open Load Questions  
   \n 2.  use the Hierarchy / Tag creation controls (text inputs).
   \n 3.	Press the Save / Add Tag button.
   \n 4.	The new topic / subtopic will be available in the Topic / Subtopic selection controls for question upload.""")
st.markdown("####  2.	Delete a Subtopic")
st.markdown("""
    1.	Use Overview 
    2.  select Topic and Subtopic 
    3.  press Delete Collection (this will remove questions and that subtopic)
""")
st.subheader("2.	Upload Questions:")
st.markdown("""Two ways: Manual table editor and CSV upload
            \n Select Topic/Subtopic in UI.
##### Manual Table Editor:
    \n1.  Open Load Questions → use the data editor to add rows. 
    \n 2.	Required fields per row: question, answer. 
    \n note: For MCQ set question type please provide option1, option2, option3 and option4.
    \n Refer the below option for prior Toggle “Enable Anki for uploaded questions”
\n a.	If **ON**, questions are saved to the user’s anki collection but the user has to add them to the scheduling deck based on their convenience.
\n b.	If **OFF**, saved to the normal questions collection.
\n Hit Save Table Questions to Database.
\n ##### CSV Upload:
Prepare a CSV with columns (recommended):
1.	MCQ Type
	question, option_1, option_2, option_3, option_4, answer\n
    Example CSV header and one row:
question	option_1	option_2	option_3	option_4	answer
What is the capital of France?	Brussels	Paris	Amsterdam	London	Paris
2.  Short Answer Type
    question, answer\n
    Example CSV header and one row:
question	answer 
What is the chemical symbol for water?	H2O
3.  True/False Type
    question, answer \n
    Example CSV header and one row:
question	answer  
The Earth is flat.	False
4.  Readout Loud Type
    question, answer\n
    Example CSV header and one row:
question	answer
What is the largest mammal on Earth?	Blue Whale
\n Hit Save Questions to Database
""")
st.subheader("3.	List and Manage Questions:")
st.markdown("""
\n 1. Open Overview → List button.
\n 2. Filter by Topic/Subtopic (selected hierarchy tags).
\n 3.You can delete selected questions or delete an entire topic/subtopic from Overview (Delete Collection).""")
st.subheader("4.	Run Quizzes:")
st.markdown("""
1.  From Overview press Start Quiz → opens Load Quiz page.
2.  Choose number of questions (10, 15, 20, 30, all).
3.  Press Load Questions from Database — the app loads questions filtered by selected tags.
4.  Navigate questions with Next Question; at the end submit to see results.
5.  After submission, view summary and restart.""")
st.subheader("6.	Anki Integration and Spaced Repetition:")
st.markdown("""
Spaced repetition helps you learn by optimizing how frequently you review information, so it moves effectively from short-term to long-term memory. This method spaces out review sessions at increasing intervals, which strengthens memory pathways and reduces forgetting. Instead of cramming, you review the material just before you are likely to forget it, which consolidates the information more deeply and makes recall easier later.
Key benefits of spaced repetition include:
            
a. Reducing mental fatigue by distributing study over multiple sessions.

b. Enhancing long-term memory retention by reinforcing neural connections.
\nc. Building confidence through repeated active recall of information.
\nd. Helping learners see connections between topics for deeper understanding.
\ne. Shortening overall study time while improving mastery and recall quality.

This is achieved through the super-memo 2 algorithm follow the steps below to use the anki feature.
#####	Collections:
1.	Normal questions are stored in the user’s questions collection.
2.	Anki-targeted questions live in an separate anki collection.
#####	Two ways to mark/add to Anki:
1.	On upload: Toggle “Enable Anki” when uploading — new items go to anki collection 
2.	From Overview: Press “Add Cards to Anki” — this scans the selected questions collection. 
            
Unlike only words you can convert any questions listed in your collection to anki flash card.
#####	Anki-Quiz page.
1.	Shows counts: total anki cards, non-anki cards, immatured/matured counts.
2.	Use “Add Cards to Anki” controls to prepare a batch for Anki study. The field lets you control the required number of questions every day.
#####  Review flow:
1.	The app retrieves questions scheduled for reveiw on each day.
2.	Presents one question at a time. 
            
For read-aloud the app uses text_to_speech and plays audio.
            
3.	After answering, user selects rating (Easy / Good / Hard / Unknown). Ratings are translated to the scheduler (anki_sm_2) and update the card’s scheduling fields.
#####	Scheduling:
4.	The internal scheduler updates next review dates and current_interval; matured/immatured counts come from those fields.
""")

