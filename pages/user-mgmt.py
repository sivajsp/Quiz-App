import streamlit as st
from App.Unified import get_db
import hashlib
from pymongo.errors import CollectionInvalid
if st.session_state.get("authenticated", False) is not True:
    if st.session_state.get("role","") != "admin":    
        st.warning("You must be logged in to access this page.")
        if st.button("Go to Login Page"):
            st.switch_page("login.py")
        st.stop()
mydb = get_db()
usercol = mydb["quiz_users"]

def get_users():
    # Each document should have "topic" and "subtopic" fields
    return list(usercol.find({}, {"_id": 0, "user": 1, "role": 1}))
def create_user(user, hash_password, role, config_collection=None, questions_collection=None, anki_collection=None, auth_disabled=False):
    """
    Create a user document and ensure the user's collections exist in mydb.
    Stores an 'auth_disabled' boolean flag per user (default False).
    """
    cfg_col = config_collection or f"{user}_config"
    q_col = questions_collection or f"{user}_questions"
    a_col = anki_collection or f"{user}_anki"

    # Insert user document with collection names and auth flag
    usercol.insert_one({
        "user": user,
        "hash": hash_password,
        "role": role,
        "config_collection": cfg_col,
        "questions_collection": q_col,
        "anki_collection": a_col,
        "auth_disabled": bool(auth_disabled)
    })

    # Ensure collections exist (create if missing)
    for name in (cfg_col, q_col, a_col):
        try:
            if name not in mydb.list_collection_names():
                mydb.create_collection(name)
        except CollectionInvalid:
            pass
def remove_user(user):
    usercol.delete_one({"user": user})
users = get_users()
st.set_page_config(initial_sidebar_state="collapsed")                                                                                            
hide_pages = """
    <style>
    [data-testid="stSidebarNav"] {display: none;}
    </style>
"""

st.markdown(hide_pages, unsafe_allow_html=True)
st.subheader("User Management")
flag = True
# create new user
with st.form("create_user_form", clear_on_submit=True):
    st.write("Create New User")
    new_user = st.text_input("Username")
    new_password = st.text_input("Password", type="password")
    retype_password = st.text_input("Retype Password", type="password")
    role = st.selectbox("Select Role", ["admin", "user"])
    if new_password != retype_password:
        st.error("Passwords do not match.")
        flag = False
    submitted = st.form_submit_button("Create User")
    if submitted and flag:
        if new_user and new_password:
            import hashlib
            hash_password = hashlib.sha256(new_password.encode()).hexdigest()
            new_user_config = new_user+"_config"
            new_user_questions = new_user+"_questions"
            new_user_anki = new_user+"_anki"
            create_user(new_user, hash_password, role,config_collection=new_user_config,questions_collection=new_user_questions,anki_collection=new_user_anki)
            st.success(f"User '{new_user}' created successfully.")
        else:
            st.error("Username and Password cannot be empty.")
# Display existing users
st.subheader("Existing Users")
plain_users = get_users()
if plain_users:
    users = [u["user"] for u in plain_users]
    utype = [u["role"] for u in plain_users]
selected_users = st.radio("Select Subtopic:", users,captions=utype, index=0)
st.write("No users found.")
if selected_users:
    if st.button("Delete User"):
        remove_user(selected_users)
        st.success(f"User '{selected_users}' deleted successfully.")
        st.rerun()

