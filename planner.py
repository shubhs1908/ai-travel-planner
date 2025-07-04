import requests
import re
import streamlit as st

# Set your OpenRouter API key
OPENROUTER_API_KEY = "YOUR-API-KEY"

# Function to extract details from user input
def extract_travel_details(user_input):
    details = {
        "starting_city": None,
        "destination": None,
        "days": None,
        "budget": None,
        "purpose": None,
        "preferences": None,
        "dietary": None,
        "accommodation": None
    }
    
    patterns = {
        "starting_city": r"from\s([A-Za-z\s]+?)\s+to",  # Ensuring we capture the city name before "to"
        "destination": r"to\s([A-Za-z\s]+?)(?=\s(for|with|and|a|the|\Z))",  # Adjusted for more flexible capture
        "days": r"(\d+)\s*(?:day|days)",  # A simple match for days, whether singular or plural
        "budget": r"budget of (\d+)",  # remains unchanged
        "purpose": r"for ([A-Za-z\s]+) travel",  # remains unchanged
        "preferences": r"prefer ([A-Za-z,\s]+)",  # remains unchanged
        "dietary": r"(?:love|want to try) ([A-Za-z,\s]+) (food|cuisine)",  # remains unchanged
        "accommodation": r"(?:want a|looking for|prefer) ([A-Za-z,\s]+) stay"  # remains unchanged
    }
    
    for key, pattern in patterns.items():
        match = re.search(pattern, user_input, re.IGNORECASE)
        if match:
            details[key] = match.group(1).strip()
    
    if details["days"]:
        try:
            details["days"] = int(details["days"])
        except ValueError:
            details["days"] = None
    
    return details

# Function to get city coordinates
def get_coordinates(city):
    url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=en&format=json"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        if "results" not in data or not data["results"]:
            return None, None
        lat = data["results"][0]["latitude"]
        lon = data["results"][0]["longitude"]
        return lat, lon
    except requests.exceptions.RequestException as e:
        print("API Error:", e)  # Debugging
        return None, None


# Function to fetch places using Overpass API
def get_places(city, place_type):
    lat, lon = get_coordinates(city)
    if lat is None or lon is None:
        return ["❌ Location not found. Try another city."]

    overpass_url = "https://overpass.kumi.systems/api/interpreter"  # Faster alternative
    radius = 50000 

    query = f"""
    [out:json];
    node["{place_type.split('=')[0]}"="{place_type.split('=')[1]}"](around:{radius}, {lat}, {lon});
    out center 10;
    """

    try:
        response = requests.get(overpass_url, params={"data": query}, timeout=15)  # Reduce timeout to 15s
        response.raise_for_status()
        data = response.json()

        places = [element.get("tags", {}).get("name", "Unnamed Location") for element in data.get("elements", [])]

        return places if places else ["❌ No matching places found."]
    
    except requests.exceptions.RequestException as e:
        print("Overpass API Error:", e)  # Debugging
        return ["❌ Could not retrieve data."]

# Function to generate AI-based descriptions using OpenRouter API
def generate_description(place):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "mistralai/mistral-7b-instruct",
        "messages": [{"role": "user", "content": f"Write a very short travel description for {place}. Keep it within one or two sentences."}],
        "max_tokens": 50
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()
    except requests.exceptions.RequestException:
        return "⚠️ Error generating description."

# Function to generate a travel itinerary
def generate_itinerary(city, days):
    attractions = get_places(city, "tourism=attraction")[:days * 3]
    if attractions[0].startswith("❌"):
        return {"Error": attractions[0]}

    itinerary = {}
    for day in range(1, days + 1):
        start_idx = (day - 1) * 3
        day_places = attractions[start_idx: start_idx + 3]
        
        while len(day_places) < 3:
            day_places.append("🚫 No more attractions found.")

        itinerary[f"Day {day}"] = [
            f"➡️ **{place}**: {generate_description(place) if place != '🚫 No more attractions found.' else 'Enjoy a relaxing break or revisit your favorite spots.'}"
            for place in day_places
        ]
    
    return itinerary

# Streamlit UI Styling
st.set_page_config(page_title="Travel Itinerary Planner", layout="wide")

st.markdown("""
    <h1 style='text-align: center;'>🌍 Travel Itinerary Planner ✈️</h1>
    """, unsafe_allow_html=True)

user_input = st.text_area("✏️ Describe your travel plan:", height=150)
if st.button("🚀 Generate Itinerary", use_container_width=True):
    if user_input:
        travel_details = extract_travel_details(user_input)
        if not travel_details["days"]:
            travel_details["days"] = 2 
        if not travel_details["destination"]:
            st.error("🚨 Please provide a valid destination and number of days.")
        else:
            hotels = get_places(travel_details["destination"], "tourism=hotel")
            restaurants = get_places(travel_details["destination"], "amenity=restaurant")
            itinerary = generate_itinerary(travel_details["destination"], travel_details["days"])
            
            if "Error" in itinerary:
                st.error(itinerary["Error"])
            else:
                st.markdown(f"### 🏨 Hotels")
                for hotel in hotels[:5]:
                    st.markdown(f"- {hotel}")
                
                st.markdown(f"### 🍽️ Restaurants")
                for restaurant in restaurants[:5]:
                    st.markdown(f"- {restaurant}")
                
                for day, statements in itinerary.items():
                    st.markdown(f"### 📅 {day}")
                    for statement in statements:
                        st.markdown(f"- {statement}")
    else:
        st.error("❌ Please enter a travel description.")
