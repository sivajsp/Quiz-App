# The Quiz Maker App

A quiz creation and testing platform built with **Streamlit** and **MongoDB**. Upload questions via CSV, manage collections, take quizzes, and study with spaced repetition.

## Features

- **Multiple question types**: MCQ, Short Answer, True/False, Read Aloud (text-to-speech)
- **Collection management**: Create, browse, and delete quiz collections
- **CSV import**: Bulk upload questions with format validation and preview
- **Quiz mode**: Take quizzes with progress tracking, answer reveal, and scored results
- **Anki study mode**: Spaced repetition learning using the SM-2 algorithm
- **Text-to-speech**: Audio playback for Read Aloud questions (Dutch language)

## Pages

| Page | Description |
|------|-------------|
| **Overview** | Dashboard showing all collections with stats, create/delete collections |
| **Upload Questions** | Import questions from CSV files with format guide and preview table |
| **List Questions** | Browse, edit, and delete questions with pagination and type badges |
| **Take Quiz** | Run quizzes with progress bar, question navigation, and detailed results |
| **Anki Study** | Spaced repetition flashcards with review logging |

## CSV Format

**MCQ**: `question, option_1, option_2, option_3, option_4, answer`

**Short Answer / True-False / Read Aloud**: `question, answer`

## Tech Stack

- **Frontend/Backend**: Streamlit
- **Database**: MongoDB
- **Text-to-Speech**: gTTS
- **Spaced Repetition**: anki-sm-2 (SM-2 algorithm)

## Setup

1. Install dependencies: `pip install streamlit pymongo pandas gtts anki-sm-2 python-dotenv`
2. Create a `.env` file with your MongoDB password: `SECRET=your_password`
3. Run the app: `streamlit run quiz/Overview.py`

## Roadmap

- Better organization of quizzes by topic and scores
- Load Anki cards from database collections
- Score history and tracking over time
