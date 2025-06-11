import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
import google.generativeai as genai
import os
import json
import re

# Streamlit page configuration
st.set_page_config(page_title="Time Management Coach", layout="wide")

# Title and description
st.title("Time Management Coach")
st.markdown("Input your daily tasks and priorities to get a personalized schedule with time-blocking tips and productivity insights, powered by Gemini.")

# Configure Gemini API
try:
    GOOGLE_API_KEY = "AIzaSyDrA2-nxoGG5VoupuYhpXcOrQiE0w2tqUM"  # Use Streamlit secrets for API key
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')  # Use Gemini 1.5 Flash model
except KeyError:
    st.error("Please set your GOOGLE_API_KEY in Streamlit secrets. Create a .streamlit/secrets.toml file with [secrets] GOOGLE_API_KEY = 'your-api-key'.")
    st.stop()

# Initialize session state for tasks
if 'tasks' not in st.session_state:
    st.session_state.tasks = []

# Function to add a task
def add_task(task_name, duration, priority, category):
    st.session_state.tasks.append({
        'Task': task_name,
        'Duration (hours)': duration,
        'Priority': priority,
        'Category': category
    })

# Function to validate start time format (HH:MM)
def is_valid_time_format(time_str):
    if not time_str or not isinstance(time_str, str):  # Check for empty or non-string input
        st.write(f"Debug: Input start time = '{time_str}' (invalid: empty or non-string)")
        return False
    time_str = time_str.strip()  # Remove leading/trailing whitespace
    st.write(f"Debug: Input start time after strip = '{time_str}'")
    pattern = r'^(0[0-9]|1[0-9]|2[0-3]):[0-5][0-9]$'  # Matches HH:MM (00:00 to 23:59)
    is_valid = bool(re.match(pattern, time_str))
    st.write(f"Debug: Time format valid = {is_valid}")
    return is_valid

# Function to generate schedule and insights using Gemini API
def generate_schedule_with_gemini(tasks, start_time, max_work_hours=8):
    tasks_str = "\n".join([f"- Task: {t['Task']}, Duration: {t['Duration (hours)']} hours, Priority: {t['Priority']}, Category: {t['Category']}" for t in tasks])
    prompt = f"""
You are a Time Management Coach. Create a personalized daily schedule with time-blocking for the following tasks, starting at {start_time}. Ensure the total task duration does not exceed {max_work_hours} hours, and include 15-minute breaks between tasks where possible. Sort tasks by priority (High > Medium > Low). Provide the schedule in JSON format with fields: Task, Start Time, End Time, Duration, Category. Also, provide productivity insights and time-blocking tips as a list of strings.

Tasks:
{tasks_str}

Output format:
```json
{{
  "schedule": [
    {{"Task": "task_name", "Start Time": "HH:MM", "End Time": "HH:MM", "Duration": hours, "Category": "category"}},
    ...
  ],
  "insights": ["insight 1", "insight 2", ...]
}}
```
"""
    try:
        response = model.generate_content(prompt)
        response_text = response.text.strip('```json\n').strip('```')
        result = json.loads(response_text)
        return result['schedule'], result['insights']
    except Exception as e:
        st.error(f"Error generating schedule with Gemini: {str(e)}")
        return [], []

# Sidebar for task input
st.sidebar.header("Add Your Tasks")
with st.sidebar.form("task_form"):
    task_name = st.text_input("Task Name")
    duration = st.number_input("Duration (hours)", min_value=0.5, max_value=8.0, step=0.5)
    priority = st.selectbox("Priority", ["High", "Medium", "Low"])
    category = st.selectbox("Category", ["Work", "Personal", "Health", "Other"])
    submit = st.form_submit_button("Add Task")
    
    if submit and task_name:
        add_task(task_name, duration, priority, category)
        st.sidebar.success(f"Added task: {task_name}")

# Main content
st.header("Your Tasks")
if st.session_state.tasks:
    tasks_df = pd.DataFrame(st.session_state.tasks)
    st.dataframe(tasks_df)
    
    # Schedule generation settings
    st.header("Generate Schedule")
    start_time = st.text_input("Start Time (HH:MM, e.g., 09:00)", value="09:00")
    
    # Validate start time before attempting schedule generation
    if not is_valid_time_format(start_time):
        st.warning(f"Invalid start time format: '{start_time}'. Please use HH:MM (e.g., 09:00). Using default start time: 09:00.")
        start_time = "09:00"
    
    generate = st.button("Generate Schedule")
    
    if generate:
        schedule, insights = generate_schedule_with_gemini(st.session_state.tasks, start_time)
        schedule_df = pd.DataFrame(schedule)
        
        if not schedule_df.empty:
            st.header("Your Personalized Schedule")
            st.dataframe(schedule_df)
            
            # Visualize schedule with Plotly
            fig = px.timeline(schedule_df, x_start="Start Time", x_end="End Time", y="Task", color="Category",
                             title="Your Daily Schedule",
                             labels={"Task": "Task", "Start Time": "Start", "End Time": "End"})
            fig.update_yaxes(autorange="reversed")
            st.plotly_chart(fig, use_container_width=True)
            
            # Productivity Insights
            st.header("Productivity Insights")
            for insight in insights:
                st.write(f"- {insight}")
        else:
            st.warning("No schedule generated. Total task duration may exceed the 8-hour limit or Gemini failed to respond.")
else:
    st.info("Add tasks using the sidebar to generate your schedule.")

# Clear tasks button
if st.button("Clear All Tasks"):
    st.session_state.tasks = []
    st.rerun()