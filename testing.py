import streamlit as st
import requests
from datetime import datetime, timedelta
import json

# Configuration
HUGGINGFACE_API_KEY = "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"
GOOGLE_CSE_ID = "f2c61b7a10fe44af2"  # Add your Custom Search Engine ID
GOOGLE_API_KEY = "AIzaSyA6hAoph3oIz-6Wh2Zad_E-VdEg6yx6Ez8"  # Add your Google API Key

# Initialize session state for conversation flow
if "conversation" not in st.session_state:
    st.session_state.conversation = []
if "details_collected" not in st.session_state:
    st.session_state.details_collected = False

# System Prompts (Modular Approach)
SYSTEM_PROMPTS = {
    "initial_greeting": """You are a friendly travel assistant. Start by welcoming the user and asking for:
    1. Destination
    2. Travel dates
    3. Number of travelers
    4. Primary purpose (leisure/business/etc.)
    Keep questions conversational.""",
    
    "preference_refinement": """Ask follow-up questions about:
    - Dietary restrictions (vegan/gluten-free/etc.)
    - Mobility considerations
    - Must-see attractions
    - Preferred pace (relaxed/balanced/fast)
    - Accommodation style""",
    
    "activity_search": """Search web for {destination} activities considering:
    - {budget} budget
    - {preferences}
    - Current season {month}
    - {activity_level} activity level
    Prioritize local experiences and hidden gems""",
    
    "itinerary_generation": """Create {duration}-day itinerary for {destination}:
    - Budget: {budget}
    - Travelers: {travelers}
    - Preferences: {preferences}
    Structure each day with:
    Morning | Afternoon | Evening
    Include:
    - Transportation tips
    - Meal recommendations
    - Cost estimates
    - Time buffers"""
}

# Enhanced UI
st.set_page_config(page_title="AI Travel Planner", layout="wide")
st.title("🧭 AI Travel Companion")
st.markdown("### Your Personalized Journey Architect")

# Sidebar for conversation history
with st.sidebar:
    st.header("Conversation History")
    for msg in st.session_state.conversation:
        st.markdown(f"**{msg['role']}**: {msg['content']}")

# Main chat interface
col1, col2 = st.columns([3,1])

# Enhanced AI Query Function
def query_huggingface(prompt, max_length=1500):
    headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}
    data = {
        "inputs": prompt,
        "parameters": {
            "max_length": max_length,
            "temperature": 0.7,
            "top_p": 0.95,
            "repetition_penalty": 1.2
        }
    }
    
    try:
        response = requests.post(
            "https://api-inference.huggingface.co/models/mistralai/Mixtral-8x7B-Instruct-v0.1",
            headers=headers,
            json=data
        )
        return response.json()[0]["generated_text"].strip()
    except Exception as e:
        return f"Error: {str(e)}"

# Bonus Challenge Implementation
def handle_vague_inputs(user_input):
    clarification_prompt = f"""
    User wrote: "{user_input}"
    This input might be vague or incomplete. Ask one specific clarifying question about:
    - Budget specifics (e.g., exact amount or range)
    - Activity preferences (e.g., outdoor vs. indoor, cultural vs. adventure)
    - Travel style (e.g., luxury vs. budget, fast-paced vs. relaxed)
    - Any missing key information (destination, dates, number of travelers)
    Make the question conversational and friendly.
    """
    return query_huggingface(clarification_prompt)

with col1:
    # Dynamic conversation flow
    if not st.session_state.details_collected:
        response = query_huggingface(SYSTEM_PROMPTS["initial_greeting"])
        st.session_state.conversation.append({"role": "Assistant", "content": response})
        st.session_state.details_collected = True
    
    user_input = st.chat_input("Type your travel preferences...")
    
    if user_input:
        st.session_state.conversation.append({"role": "User", "content": user_input})
        
        # Check for vague inputs (Bonus Challenge)
        if len(user_input.split()) < 5 or "moderate budget" in user_input.lower() or "mix of" in user_input.lower():
            clarification = handle_vague_inputs(user_input)
            st.session_state.conversation.append({"role": "Assistant", "content": clarification})
        else:
            # Get refined preferences
            refinement_prompt = f"""
            Current conversation:
            {st.session_state.conversation[-3:]}
            
            {SYSTEM_PROMPTS["preference_refinement"]}
            """
            ai_response = query_huggingface(refinement_prompt)
            st.session_state.conversation.append({"role": "Assistant", "content": ai_response})

# Web Search Integration        
def google_search(query):
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "q": query,
        "cx": GOOGLE_CSE_ID,
        "key": GOOGLE_API_KEY,
        "num": 5
    }
    response = requests.get(url, params=params)
    return [item["snippet"] for item in response.json().get("items", [])]

# Itinerary Generation with Web Data
def generate_final_itinerary():
    user_data = extract_user_data()
    activities = google_search(
        f"{user_data['destination']} {user_data['preferences']} activities"
    )[:3]
    
    final_prompt = SYSTEM_PROMPTS["itinerary_generation"].format(
        **user_data,
        activities=", ".join(activities),
        month=datetime.now().strftime("%B")
    )
    
    return query_huggingface(final_prompt, max_length=2000)

# Helper function to extract user data from conversation
def extract_user_data():
    # This is a placeholder. In a real implementation, you'd parse the conversation
    # to extract key details like destination, budget, preferences, etc.
    return {
        "destination": "Paris",
        "budget": "moderate",
        "duration": "5 days",
        "travelers": "2",
        "preferences": "cultural sights, local cuisine"
    }

# Deployment Ready Configuration
st.markdown("---")
with st.expander("Advanced Options"):
    st.write("Model Settings")
    temperature = st.slider("Creativity Level", 0.1, 1.0, 0.7)
    max_length = st.selectbox("Response Length", [512, 1024, 2048], index=1)

# Display Final Itinerary
if st.button("Generate Final Itinerary"):
    with st.spinner("🧭 Crafting your perfect journey..."):
        itinerary = generate_final_itinerary()
        st.subheader("Your Personalized Travel Plan")
        st.markdown(itinerary)
        st.download_button("Download Itinerary", itinerary, file_name="travel_plan.md")