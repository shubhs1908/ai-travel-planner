import streamlit as st
import requests
import json

# Set API keys (replace with your Hugging Face API key)
HUGGINGFACE_API_KEY = "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"

# Streamlit UI
st.title("AI Travel Planner 🌍")
st.subheader("Plan your perfect trip with AI!")

# User Inputs with Refinements
destination = st.text_input("Enter your destination:")
budget = st.selectbox("Select your budget:", ["Economy", "Mid-range", "Luxury"])
duration = st.slider("Trip Duration (Days):", 1, 14, 5)
purpose = st.selectbox("Purpose of travel:", ["Leisure", "Adventure", "Business", "Cultural Exploration"])
preferences = st.text_area("Any specific preferences (food, activities, accommodation, etc.)?")

dietary_pref = st.selectbox("Do you have dietary preferences?", ["No Preference", "Vegetarian", "Vegan", "Halal", "Gluten-Free"])
activity_level = st.selectbox("Preferred Activity Level:", ["Relaxing", "Moderate", "Highly Active"])
accommodation = st.selectbox("Preferred Accommodation:", ["Budget", "Mid-range", "Luxury", "Central Location"])

# Function to get travel insights from WikiVoyage
def get_travel_guide(destination):
    url = f"https://en.wikivoyage.org/w/api.php?action=query&prop=extracts&format=json&titles={destination}"
    response = requests.get(url)
    
    if response.status_code == 200:
        try:
            data = response.json()
            page = next(iter(data["query"]["pages"].values()))  # Get first page found
            return page.get("extract", "No information available.")[:300]  # Limit guide to 300 characters
        except Exception:
            return "No travel guide found."
    return "Failed to retrieve travel guide."

# Function to generate AI itinerary
def generate_itinerary(destination, budget, duration, purpose, preferences, dietary_pref, activity_level, accommodation, travel_guide):
    prompt = f"""
    Create a {duration}-day travel itinerary for {destination}.
    - Budget: {budget}
    - Purpose: {purpose}
    - Preferences: {preferences if preferences else 'No specific preferences'}
    - Dietary Preferences: {dietary_pref}
    - Activity Level: {activity_level}
    - Accommodation Type: {accommodation}
    - Travel Guide Insights: {travel_guide}
    Ensure:
    - Logical activity flow with morning, afternoon, and evening plans.
    - Meal recommendations.
    - Activity recommendations based on budget and preferences.
    - Offbeat or hidden gems for exploration.
    """

    headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}
    data = {
        "inputs": prompt,
        "parameters": {
            "max_length": 700,  # Allow detailed response
            "temperature": 0.7,
            "top_p": 0.9,
        }
    }

    try:
        response = requests.post(
            "https://api-inference.huggingface.co/models/tiiuae/falcon-7b", 
            headers=headers, json=data
        )

        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list) and "generated_text" in result[0]:
                itinerary = result[0]["generated_text"].strip()
                return itinerary if len(itinerary) > 50 else "Error: AI response too short. Try again."
            return "Unexpected response format from API."
        
        elif response.status_code == 403:
            return "Error: Invalid API Key or rate limit exceeded."
        
        elif response.status_code == 404:
            return "Error: AI model not found. Try another model."
        
        return f"Error: {response.status_code} - {response.text}"
    
    except requests.exceptions.RequestException as e:
        return f"API Request failed: {str(e)}"

# Button to generate itinerary
if st.button("Generate Itinerary"):
    if destination.strip():
        with st.spinner("Generating itinerary... ⏳"):
            travel_guide = get_travel_guide(destination)
            itinerary = generate_itinerary(destination, budget, duration, purpose, preferences, dietary_pref, activity_level, accommodation, travel_guide)
        st.subheader("Your Personalized Itinerary:")
        st.markdown(itinerary, unsafe_allow_html=True)
    else:
        st.warning("Please enter a destination before generating an itinerary.")

st.markdown("---")
st.info("This AI travel planner generates itineraries using Hugging Face models and travel insights from WikiVoyage.")
