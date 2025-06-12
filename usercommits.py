import streamlit as st
import requests
from datetime import datetime, timedelta
import os
import sys
import pandas as pd
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.fetch import fetch_paginated_data
from utils.auth import get_gitlab_headers



GITLAB_BASE_URL = "https://code.swecha.org/api/v4"

HEADERS = get_gitlab_headers()


#-----------------api function---------------------------------

def get_commits(username):
    url = f"{GITLAB_BASE_URL}/users?search={username}"
    try:
        resp = requests.get(url, headers=HEADERS)
        resp.raise_for_status()
        users = resp.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to fetch user '{username}': {e}")
    if users:
        st.write(f"Found {len(users)} matching user(s):")
        for user in users:
            if st.button(f"👤 {user['name']} ({user['username']})"):
                st.session_state['selected_user_id'] = user['id']
                st.switch_page("pages/1_User_Details.py")
        else:
            st.error("❌ No users found.")
    else:
        st.error("❌ Failed to fetch users.")