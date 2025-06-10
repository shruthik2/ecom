import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai
from datetime import date

# Setup Gemini API
genai.configure(api_key="AIzaSyDrA2-nxoGG5VoupuYhpXcOrQiE0w2tqUM")

# Load mood data
def load_data():
    try:
        return pd.read_csv("mood_log.csv", parse_dates=["Date"])
    except:
        return pd.DataFrame(columns=["Date", "Mood", "Note"])

# Save new mood entry
def save_data(new_entry):
    df = load_data()
    df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
    df.to_csv("mood_log.csv", index=False)

st.title("🧠 Daily Mood Tracker with AI")

mood = st.selectbox("How are you feeling today?", ["Happy", "Sad", "Angry", "Excited", "Anxious", "Neutral"])
note = st.text_area("Why do you feel this way? (optional)")
selected_date = st.date_input("Date", date.today())

if st.button("Save Mood"):
    entry = {
        "Date": selected_date,
        "Mood": mood,
        "Note": note
    }
    save_data(entry)
    st.success("Mood saved!")

    # Use Gemini to give advice
    model = genai.GenerativeModel('gemini-2.0-flash')
    prompt = f"I am feeling {mood} today. Give me short advice or encouragement."
    response = model.generate_content(prompt)
    st.markdown("🌟 **Gemini Advice:**")
    st.write(response.text)

# Show mood history
df = load_data()
st.subheader("📅 Mood History")
st.dataframe(df)

# Chart
if not df.empty:
    fig = px.histogram(df, x="Date", color="Mood", title="Mood Over Time")
    st.plotly_chart(fig)
