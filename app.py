import streamlit as st
import requests
from groq import Groq
from gtts import gTTS
from io import BytesIO
import base64
import datetime

# ----------------------------------------------------
# 1. Page Configuration & Custom CSS
# ----------------------------------------------------
st.set_page_config(
    page_title="PitchAI - Football Assistant",
    page_icon="⚽",
    layout="wide"
)

st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #03120c 0%, #08291b 50%, #020b07 100%);
        color: #e0f2fe;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    section[data-testid="stSidebar"] {
        background-color: #020d08 !important;
        border-right: 1px solid #10b981;
    }
    h1 {
        color: #00ff87 !important;
        text-shadow: 0px 0px 14px rgba(0, 255, 135, 0.5);
        font-weight: 800;
    }
    h2, h3 {
        color: #6ee7b7 !important;
    }
    .stButton>button, .stDownloadButton>button {
        background: linear-gradient(180deg, #0e3823 0%, #061c12 100%);
        color: #00ff87;
        border: 1px solid #059669;
        border-radius: 10px;
        font-weight: 600;
        padding: 8px 14px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.4);
        width: 100%;
    }
    .stButton>button:hover, .stDownloadButton>button:hover {
        background: #00ff87;
        color: #01160e;
        border-color: #00ff87;
        box-shadow: 0 0 16px rgba(0, 255, 135, 0.7);
        transform: translateY(-2px);
    }
    div[data-testid="stChatMessage"] {
        background-color: rgba(4, 30, 19, 0.75);
        border: 1px solid #059669;
        border-radius: 14px;
        padding: 12px;
        margin-bottom: 12px;
    }
    div[data-testid="stChatInput"] input {
        background-color: #020f09 !important;
        color: #ffffff !important;
        border: 1px solid #10b981 !important;
        border-radius: 10px !important;
    }
    </style>
""", unsafe_allow_html=True)

# ----------------------------------------------------
# 2. Setup API Keys & Groq Client
# ----------------------------------------------------
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", "YOUR_GROQ_API_KEY_HERE")
FOOTBALL_DATA_API_KEY = st.secrets.get("FOOTBALL_DATA_API_KEY", "YOUR_FOOTBALL_DATA_API_KEY_HERE")

groq_client = Groq(api_key=GROQ_API_KEY)

@st.cache_resource
def get_working_model():
    try:
        models_data = groq_client.models.list()
        available = [m.id for m in models_data.data]
        preferred = ["llama-3.3-70b-versatile", "openai/gpt-oss-20b", "llama-3.1-8b-instant"]
        for pref in preferred:
            if pref in available:
                return pref
        if available:
            return available[0]
    except Exception:
        pass
    return "llama-3.3-70b-versatile"

SELECTED_MODEL = get_working_model()

# ----------------------------------------------------
# 3. Text-To-Speech Player
# ----------------------------------------------------
def play_audio(text):
    try:
        fp = BytesIO()
        tts = gTTS(text=text, lang='en')
        tts.write_to_fp(fp)
        fp.seek(0)
        audio_bytes = fp.read()
        b64_audio = base64.b64encode(audio_bytes).decode()
        md = f"""
            <audio controls autoplay style="width: 100%; margin-top: 10px; filter: invert(0.8);">
                <source src="data:audio/mp3;base64,{b64_audio}" type="audio/mp3">
            </audio>
            """
        st.markdown(md, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Audio notice: {e}")

# ----------------------------------------------------
# 4. API Functions for Matches
# ----------------------------------------------------
LEAGUES = {
    "Premier League": "PL",
    "La Liga": "PD",
    "Champions League": "CL",
    "Serie A": "SA",
    "Bundesliga": "BL1"
}

st.sidebar.title("🏆 Football Hub")
selected_league_name = st.sidebar.selectbox("Select Competition", list(LEAGUES.keys()))
league_code = LEAGUES[selected_league_name]

def fetch_finished_matches(code):
    if FOOTBALL_DATA_API_KEY == "YOUR_FOOTBALL_DATA_API_KEY_HERE":
        return None
    url = f"https://api.football-data.org/v4/competitions/{code}/matches?status=FINISHED"
    headers = {"X-Auth-Token": FOOTBALL_DATA_API_KEY}
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            return res.json().get("matches", [])
    except Exception:
        pass
    return None

def fetch_upcoming_matches(code):
    if FOOTBALL_DATA_API_KEY == "YOUR_FOOTBALL_DATA_API_KEY_HERE":
        return None
    url = f"https://api.football-data.org/v4/competitions/{code}/matches?status=SCHEDULED"
    headers = {"X-Auth-Token": FOOTBALL_DATA_API_KEY}
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            return res.json().get("matches", [])
    except Exception:
        pass
    return None

# ----------------------------------------------------
# 5. Main Layout with Tabs (Pages)
# ----------------------------------------------------
st.title("⚽ PitchAI Virtual Assistant")

tab1, tab2 = st.tabs(["💬 PitchAI Chat", "📅 Matches & Results"])

# --- TAB 1: Chatbot Interface ---
with tab1:
    st.caption(f"Currently tracking: {selected_league_name}")
    
    st.markdown("### ⚡ Quick Prompts")
    col1, col2, col3 = st.columns(3)
    prompt_to_send = None

    with col1:
        if st.button("🏆 Recent Match Recap"):
            prompt_to_send = f"Give me a quick recap of recent results in the {selected_league_name}."
    with col2:
        if st.button("📊 Top Players Comparison"):
            prompt_to_send = "Compare the current form of Haaland, Mbappé, and Yamal."
    with col3:
        if st.button("🧠 Tactical Analysis"):
            prompt_to_send = f"Analyze the tactical trends in the {selected_league_name} this season."

    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "system", "content": "You are 'PitchAI', an expert football virtual assistant."},
            {"role": "assistant", "content": f"Welcome! I am PitchAI, tuned into {selected_league_name}. How can I help?"}
        ]

    for msg in st.session_state.messages:
        if msg["role"] != "system":
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    chat_input = st.chat_input("Ask PitchAI anything about football...")
    user_query = chat_input if chat_input else prompt_to_send

    if user_query:
        st.session_state.messages.append({"role": "user", "content": user_query})
        with st.chat_message("user"):
            st.markdown(user_query)

        with st.chat_message("assistant"):
            with st.spinner("Analyzing..."):
                try:
                    completion = groq_client.chat.completions.create(
                        model=SELECTED_MODEL,
                        messages=st.session_state.messages,
                        temperature=0.7,
                    )
                    response = completion.choices[0].message.content
                    st.markdown(response)
                    play_audio(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                except Exception as e:
                    st.error(f"Error: {e}")

# --- TAB 2: Previous & Upcoming Matches Page ---
with tab2:
    st.header(f"📊 {selected_league_name} Fixtures Center")
    
    col_prev, col_next = st.columns(2)
    
    with col_prev:
        st.subheader("⏮️ Recent Results")
        finished_matches = fetch_finished_matches(league_code)
        if finished_matches:
            # Show last 5 finished matches
            recent = finished_matches[-5:]
            recent.reverse()
            for m in recent:
                home = m["homeTeam"]["name"]
                away = m["awayTeam"]["name"]
                score_h = m["score"]["fullTime"]["home"]
                score_a = m["score"]["fullTime"]["away"]
                date_str = m["utcDate"][:10]
                st.success(f"**{home}** `{score_h} - {score_a}` **{away}**  \n*Date: {date_str}*")
        else:
            st.info("No recent results available or API key missing.")

    with col_next:
        st.subheader("⏭️ Upcoming Fixtures")
        upcoming_matches = fetch_upcoming_matches(league_code)
        if upcoming_matches:
            # Show next 5 upcoming matches
            next_five = upcoming_matches[:5]
            for m in next_five:
                home = m["homeTeam"]["name"]
                away = m["awayTeam"]["name"]
                date_str = m["utcDate"][:10]
                st.info(f"⚽ **{home}** vs **{away}**  \n*Scheduled: {date_str}*")
        else:
            st.info("No upcoming matches scheduled or API key missing.")