# Quiz Application

A Streamlit-based interactive quiz application with spaced repetition learning using the Anki SM-2 algorithm. This application integrates MongoDB for persistent data storage and supports multiple quiz formats with text-to-speech capabilities.

## Features

- **User Authentication**: Secure login system with password hashing and brute-force protection (5 failed attempts = 15-minute lockout)
- **Spaced Repetition Learning**: Anki SM-2 algorithm integration for effective memorization
- **Quiz Management**: Create, organize, and manage quiz collections with topics and subtopics
- **Multiple Question Types**: Support for various question formats including multiple choice with options
- **Text-to-Speech**: Dutch language audio generation for questions
- **MongoDB Integration**: Cloud-based database storage with collections for users, quizzes, and Anki cards
- **Role-Based Access**: Admin and user roles with different permission levels
- **User Management**: Admin panel for managing user accounts and authentication settings

## Project Structure

```
quiz/
├── login.py                    # Application entry point
├── Anki.py                     # Anki SM-2 spaced repetition implementation
├── App/
│   ├── __init__.py
│   ├── Unified.py             # Core database operations and utilities
│   └── generate.sh            # Shell script for setup
├── pages/
│   ├── Overview.py            # Quiz collection management interface
│   ├── List_Question.py       # Question listing and management
│   ├── Load_Questions.py      # Question import functionality
│   ├── Load_Quiz.py           # Quiz loading interface
│   ├── Anki-Quiz.py           # Spaced repetition quiz mode
│   ├── user-manual.py         # User documentation
│   ├── user-mgmt.py           # User management (admin)
│   └── routing.yaml           # Page routing configuration
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## Installation

### Prerequisites
- Python 3.10+
- MongoDB Atlas account or local MongoDB instance
- Virtual environment (venv)

### Setup

1. **Clone the repository**
   ```bash
   git clone <repo-url>
   cd quiz
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv .
   Scripts\Activate.ps1  # On Windows
   # or
   source bin/activate   # On Linux/Mac
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables** - Create a `.env` file:
   ```
   SERVER=your_mongodb_server
   UNAME=your_mongodb_username
   SECRET=your_mongodb_password
   ```

5. **Run the application**
   ```bash
   streamlit run login.py
   ```
   Or use the included batch file:
   ```bash
   Quiz.bat
   ```

## Usage

### Login
- Navigate to the login page and provide credentials
- First-time users: Contact admin for account creation

### Quiz Overview
- View all available quiz collections organized by topic
- Create new quizzes and manage existing ones
- Add or remove question tags

### Taking a Quiz
- Select a quiz and answer questions
- View immediate feedback on answers
- Track your progress with Anki spaced repetition

### Anki Learning Mode
- Review questions scheduled for today using spaced repetition
- Rate your confidence on each answer (Again, Hard, Good, Easy)
- System adjusts future review times based on your performance

## Technologies Used

- **Frontend**: Streamlit (Python web framework)
- **Backend**: Python
- **Database**: MongoDB
- **Learning Algorithm**: Anki SM-2 (Spaced Repetition Algorithm)
- **Text-to-Speech**: Google Text-to-Speech (gTTS)
- **Audio Processing**: PyDub

## Key Dependencies

- `streamlit` - Web app framework
- `pymongo` - MongoDB driver
- `anki_sm_2` - Spaced repetition algorithm
- `gtts` - Google Text-to-Speech
- `pandas` - Data manipulation
- `python-dotenv` - Environment variable management

## Database Collections

- **quiz_users** - User accounts and authentication data
- **config** - Quiz topics and subtopics configuration
- **[user_questions_collection]** - Quiz questions (dynamically named)
- **anki_collection** - Anki cards and review data

## User Roles

- **Admin**: Can manage users, access user management dashboard, and create system-wide quizzes
- **User**: Can take quizzes and use spaced repetition learning

## Authentication Features

- SHA-256 password hashing
- Brute-force protection with lockout mechanism
- Auth disable option for specific users
- Session-based authentication via Streamlit

## Development

### Running the application locally
```bash
streamlit run login.py --logger.level=debug
```

### Database seed data
The application can load questions from MongoDB collections and create Anki cards for spaced repetition learning.

## Future Enhancements

- Export quiz statistics and learning analytics
- Multi-language support beyond Dutch
- Advanced question types (matching, ordering, etc.)
- Customizable spaced repetition parameters
- Quiz scheduling and calendar integration
- Performance analytics dashboard

## License

(Specify your license here)

## Support

For issues or questions, please contact the admin or check the user manual accessible within the application.
