import hashlib
import streamlit as st
from pymongo.errors import ServerSelectionTimeoutError
from App.Unified import get_db
from datetime import datetime, timedelta
st.set_page_config(initial_sidebar_state="collapsed")
hide_pages = """
    <style>
    [data-testid="stSidebarNav"] {display: none;}
    </style>
"""
st.markdown(hide_pages, unsafe_allow_html=True)
mydb = get_db()
usercol = mydb["quiz_users"]

# --- Authentication helpers ---

def _verify_credentials(username: str, password: str) -> bool:
    """Verify user credentials against the database. If auth_disabled is True, allow login without password."""
    try:
        user_doc = usercol.find_one({"user": username})
        if not user_doc:
            return False
        # If the user's auth is disabled, allow login (no password required)
        if user_doc.get("auth_disabled", False):
            return True
        # Otherwise check password hash
        hash_password = hashlib.sha256(password.encode()).hexdigest()
        return hash_password == user_doc.get("hash", "")
    except ServerSelectionTimeoutError:
        st.error("Database connection timed out. Please check your connection and try again.")
        return False
st.session_state.authenticated = False

MAX_FAILED = 5
LOCK_MINUTES = 15

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "failed_attempts" not in st.session_state:
    st.session_state.failed_attempts = 0
if "lockout_until" not in st.session_state:
    st.session_state.lockout_until = None

# If currently locked out, check expiry
now = datetime.utcnow()
if st.session_state.lockout_until:
    try:
        if now >= st.session_state.lockout_until:
            # lock expired -> reset counters
            st.session_state.failed_attempts = 0
            st.session_state.lockout_until = None
    except Exception:
        st.session_state.lockout_until = None

# If locked out, show message and prevent login attempts
if st.session_state.lockout_until and now < st.session_state.lockout_until:
    remaining = st.session_state.lockout_until - now
    minutes = int(remaining.total_seconds() // 60) + 1
    st.markdown("### Login temporarily disabled")
    st.error(f"Too many failed login attempts. Try again in ~{minutes} minute(s).")
    st.stop()

# If auth not yet done, show login form
if not st.session_state.authenticated:
    st.markdown("### Login required")
    with st.form("login_form", clear_on_submit=False):
        user = st.text_input("Username")
        pwd = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        if submitted:
            user_doc = usercol.find_one({"user": user}) if user else None
            if user_doc and user_doc.get("auth_disabled", False):
                st.info("Authentication disabled for this user — logging in without password.")
            if _verify_credentials(user, pwd):
                # success -> reset counters and set session
                st.session_state.authenticated = True
                st.session_state.failed_attempts = 0
                st.session_state.lockout_until = None
                st.session_state.username = user
                st.session_state.role = usercol.find_one({"user": user}).get("role", "user")
                st.session_state.config_collection = usercol.find_one({"user": user}).get("config_collection", f"{user}_config")
                st.session_state.questions_collection = usercol.find_one({"user": user}).get("questions_collection", f"{user}_questions")
                st.session_state.anki_collection = usercol.find_one({"user": user}).get("anki_collection", f"{user}_anki")
                st.success("Login successful!")
                st.switch_page("pages/Overview.py")
                st.rerun()
            else:
                # failed attempt -> increment and possibly lock
                st.session_state.failed_attempts += 1
                remaining = MAX_FAILED - st.session_state.failed_attempts
                if st.session_state.failed_attempts >= MAX_FAILED:
                    st.session_state.lockout_until = now + timedelta(minutes=LOCK_MINUTES)
                    st.error(f"Too many failed attempts. Login disabled for {LOCK_MINUTES} minutes.")
                else:
                    st.error(f"Invalid username or password. {remaining} attempt(s) remaining.")
    st.stop()


# If auth is enabled require login
# prevent access until authenticated
    
# ...existing code...
st.set_page_config(initial_sidebar_state="collapsed")
hide_pages = """
    <style>
    [data-testid="stSidebarNav"] {display: none;}
    </style>
"""
st.markdown(hide_pages, unsafe_allow_html=True)

# ...existing code...