# utils/formatter.py
from datetime import datetime

def generate_summary(tasks_by_user):
    html = f"""
    <h1>Daily Standup Summary - {datetime.now().strftime("%B %d, %Y")}</h1>
    """
    for user, tasks in tasks_by_user.items():
        html += f"<h2>{user}</h2><ul>"
        for task in tasks:
            html += f"<li>{task['title']} ({task['status']})</li>"
        html += "</ul>"
    return html