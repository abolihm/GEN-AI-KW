import google.generativeai as genai
import streamlit as st
import requests
from bs4 import BeautifulSoup
import time
from dotenv import load_dotenv
import os

load_dotenv()  # Load environment variables from .env file

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SERP_API_KEY = os.getenv("SERP_API_KEY")

# 🔹 Configure Gemini AI
genai.configure(api_key="AIzaSyA4wbyTmdaxZjcSOigfnZr2jDGq8LTOez0")
model = genai.GenerativeModel("gemini-1.5-flash")

SERP_API_KEY = "2cba55ea8599d0e8a86086ddd18c6a98f9fb548ce68be95b1a941358d903e18f"

# 🔹 Function to extract keywords from a website
def extract_keywords_from_url(url):
    try:
        response = requests.get(url, timeout=5)
        soup = BeautifulSoup(response.text, "html.parser")
        text = ' '.join([p.text for p in soup.find_all('p')])[:1000]  # Limit text size
        prompt = f"Extract relevant keywords from this content to attract Indian audience: '{text}'. Return only the keywords, one per line."
        
        ai_response = model.generate_content(prompt)
        keywords = ai_response.text.strip().split("\n")
        return keywords if keywords else []
    except Exception as e:
        print(f"Error extracting keywords: {e}")
        return []

# 🔹 Function to expand keywords
def expand_keywords(keyword, num_keywords, language):
    prompt = f"Generate {num_keywords} related keywords for: '{keyword}' in {language} language to attract Indian audience/customers. Return only the keywords, one per line, no additional text."
    
    try:
        response = model.generate_content(prompt)
        keywords = response.text.strip().split("\n")
        return keywords if keywords else []
    except Exception as e:
        print(f"Error in expand_keywords: {e}")
        return []

# 🔹 Function to categorize keywords with category & subcategory
def categorize_keywords(keywords):
    categorized_keywords = []

    for keyword in keywords:
        prompt = f"""For the given keyword '{keyword}', return:
        - The main category.
        - The subcategory.
        - The estimated Google Search Engine ranking (1-100 or 'Not Ranked' if no ranking found).
        - Format: Keyword - Category - Subcategory - Google Rank"""

        try:
            response = model.generate_content(prompt)
            category_data = response.text.strip()
            
            # Split response into keyword, category, subcategory, google rank
            parts = category_data.split(" - ")
            if len(parts) == 4:
                categorized_keywords.append({
                    "keyword": parts[0],
                    "category": parts[1],
                    "subcategory": parts[2],
                    "google_rank": parts[3]
                })
        except Exception as e:
            print(f"Error categorizing keyword '{keyword}': {e}")

        time.sleep(1)  # Delay to avoid API rate limits

    return categorized_keywords

def analyze_keywords(keyword):
    url = f"https://serpapi.com/search.json?engine=google&q={keyword}&api_key={SERP_API_KEY}&gl=IN"

    try:
        response = requests.get(url)
        data = response.json()

        # Extract relevant data
        search_info = data.get("search_information", {})
        search_metadata = data.get("search_metadata", {})
        
        volume = search_info.get("total_results", "N/A")  # Total search volume
        difficulty = search_info.get("difficulty", "N/A")  # Keyword difficulty as number
        
        # Trend data: Check for organic result positions
        trend_data = [result.get("position", 0) for result in data.get("organic_results", [])]

        # Determine if it's trending up or down
        if trend_data == sorted(trend_data, reverse=True):  # Rankings going up (smaller positions = higher rank)
            trend = "Up-Trending"
        else:
            trend = "Down-Trending"

        # ✅ Return the updated dictionary with difficulty as a number
        return {
            "keyword": keyword,
            "volume": volume,
            "trend": trend,
            "difficulty": difficulty  # Direct number
        }

    except Exception as e:
        print(f"Error fetching keyword analysis for '{keyword}': {e}")
        return {
            "keyword": keyword,
            "volume": "N/A",
            "trend": "N/A",
            "difficulty": "N/A"
        }


# Streamlit UI Code

st.title("Keyword Extraction & Analysis Tool")

# Input Fields
website_url = st.text_input("Enter Website URL", "")
input_keyword = st.text_input("Or Enter Keyword", "")
email = st.text_input("Enter Your Email", "")
num_keywords = st.number_input("Number of Keywords to Extract", min_value=1, max_value=50, value=5)
language = st.selectbox("Select Language", ["English", "Hindi", "Other"])

# Process Keywords Button
if st.button("Generate Keywords"):
    if website_url:
        expanded_keywords = extract_keywords_from_url(website_url)
    elif input_keyword:
        expanded_keywords = expand_keywords(input_keyword, num_keywords, language)
    else:
        st.error("Please enter either a website URL or a keyword")
        expanded_keywords = []

    if expanded_keywords:
        st.session_state.expanded_keywords = expanded_keywords
        st.write("**Extracted Keywords**:")
        for keyword in expanded_keywords:
            st.write(f"- {keyword}")

# Categorize Keywords
if 'expanded_keywords' in st.session_state:
    if st.button("Categorize Keywords"):
        categorized_keywords = categorize_keywords(st.session_state.expanded_keywords)
        st.session_state.categorized_keywords = categorized_keywords
        
        st.write("**Categorized Keywords**:")
        for item in categorized_keywords:
            st.write(f"{item['keyword']} - {item['category']} - {item['subcategory']} - {item['google_rank']}")

# Analyze Keywords
if 'categorized_keywords' in st.session_state:
    if st.button("Analyze Keywords (Volume, Trend, Difficulty)"):
        analyzed_keywords = []
        for item in st.session_state.categorized_keywords:
            analysis = analyze_keywords(item['keyword'])
            analyzed_keywords.append({**item, **analysis})

        st.write("**Analyzed Keywords**:")
        for item in analyzed_keywords:
            st.write(f"{item['keyword']} - {item['category']} - {item['subcategory']} - {item['google_rank']} - {item['volume']} - {item['trend']} - {item['difficulty']}")

# If you want to persist user data, for example email:
if email:
    st.session_state.email = email
