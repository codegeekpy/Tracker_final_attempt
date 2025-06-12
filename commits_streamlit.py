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

#Api fuction -------------------------------------------------------------------
@st.cache_data(ttl=3600)
def fetch_user_by_username(username):
    url = f"{GITLAB_BASE_URL}/users?username={username}"
    try:
        resp = requests.get(url, headers=HEADERS)
        resp.raise_for_status()
        users = resp.json()
        return users[0] if users else None
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to fetch user '{username}': {e}")
        return None

@st.cache_data(ttl=3600)
def fetch_user_projects(user_id):
    url = f"{GITLAB_BASE_URL}/users/{user_id}/projects"
    return fetch_paginated_data(url, HEADERS)

@st.cache_data(ttl=3600)
def fetch_project_commits(project_id, since_date):
    url = f"{GITLAB_BASE_URL}/projects/{project_id}/repository/commits"
    params = {'since': since_date.isoformat()}
    return fetch_paginated_data(url, HEADERS, params)

def get_collaborations_data(my_username, days_back):
    if not HEADERS:
        st.error("API Headers not available. Ensure ACCESS_TOKEN is set in your .env file.")
        return None, {}

    my_user_info = fetch_user_by_username(my_username)
    if not my_user_info:
        return None, {}

    st.success(f"✅ Successfully found user: {my_user_info['name']} ({my_user_info['username']})")

    since_date = datetime.now() - timedelta(days=days_back)
    my_projects = fetch_user_projects(my_user_info["id"])

    if not my_projects:
        st.info(f"No projects found where {my_username} is a member.")
        return my_user_info, {}
#-----------------------------------------------------------------------------------------------------------------
    collaborations = {}
    found_any_contributions = False

    st.subheader(f"Projects with Your Contributions (Last {days_back} Days)")

    for proj in my_projects:
        project_name_space = proj.get('path_with_namespace', proj.get('name', 'Unknown Project'))

        with st.expander(f"📦 *{proj['name']}* ", expanded=False):
            st.markdown(f"*Path:* {project_name_space}")
            st.markdown(f"*Web URL:* [Link]({proj['web_url']})")

            project_commits = fetch_project_commits(proj["id"], since_date)

            if project_commits:
                my_commits_in_project = [
                    commit for commit in project_commits
                    if commit.get('author_name', '').lower() == my_user_info['name'].lower() or \
                       (my_user_info.get('email') and commit.get('author_email', '').lower() == my_user_info['email'].lower())
                ]

                if my_commits_in_project:
                    found_any_contributions = True
                    st.info(f"You have *{len(my_commits_in_project)}* commit(s) in this project.")

                    all_authors = set(c.get('author_name', 'Unknown') for c in project_commits)

                    other_contributors = sorted([author for author in all_authors if author.lower() != my_user_info['name'].lower()])

                    if other_contributors:
                        st.write("*Collaborators on this project:*")
                        for contributor in other_contributors:
                            st.markdown(f"- 👤 {contributor}")
                        collaborations[proj['name']] = other_contributors
                    else:
                        st.info("You are the only listed contributor in this project based on recent commits.")

                    my_recent_commits_df = pd.DataFrame([
                        {'Date': pd.to_datetime(c['committed_date']).date(), 'Message': c['title']}
                        for c in my_commits_in_project
                    ])
                    if not my_recent_commits_df.empty:
                        st.markdown("*Your Recent Commits:*")
                        st.dataframe(my_recent_commits_df)

                else:
                    st.info("You have no recent commits in this project (within the selected days back).")
            else:
                st.warning("No recent commits found in this project (within the selected days back).")

    if not found_any_contributions:
        st.warning(f"No contributions found in any of your projects in the last {days_back} days.")

    return my_user_info, collaborations

st.set_page_config(page_title="GitLab Collaborations Report", layout="wide")
st.title("🤝 Your GitLab Collaborations Report")

st.markdown(
    """
    Enter your GitLab username below to see a report of projects where you have contributed,
    and identify other individuals who have also committed to those projects.
    """
)

with st.sidebar:
    st.header("GitLab Details")
    my_username_input = st.text_input("Your GitLab Username:", placeholder="e.g. your_username")
    days_back_slider = st.slider("Days back to check commits:", 1, 180, 30)
    fetch_report_btn = st.button("🔍 Generate Report")

if fetch_report_btn:
    if not my_username_input:
        st.warning("Please enter your GitLab username to proceed.")
        st.stop()

    with st.spinner(f"Generating collaboration report for {my_username_input}..."):
        user_info, collab_data = get_collaborations_data(my_username_input, days_back_slider)

        if user_info and collab_data:
            st.subheader("Summary of Collaborations")
            if any(collab_list for collab_list in collab_data.values()):
                for project, collaborators in collab_data.items():
                    st.markdown(f"*Project:* {project}")
                    if collaborators:
                        st.write("  *Collaborators:*")
                        for collab in collaborators:
                            st.write(f"  - {collab}")
                    else:
                        st.write("  (You are the sole listed contributor in this project)")
            else:
                st.info("No projects found with other collaborators for your contributions in the selected timeframe.")
        elif user_info:
            st.info("No projects or collaborations found for your username in the specified timeframe.")