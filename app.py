import streamlit as st
import requests
from groq import Groq
from gtts import gTTS
from io import BytesIO
import base64
import datetime

# ----------------------------------------------------
# 1. Page Configuration & Custom Football Theme (CSS)
# ----------------------------------------------------
st.set_page_config(
    page_title="PitchAI - Football Assistant",
    page_icon="⚽",
    layout="wide"
)

st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #051911 0%, #0a2e20 50%, #03120b 100%);
        color: #e0f2fe;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    section[data-testid="stSidebar"] {
        background-color: #04120c !important;
        border-right: 1px solid #164e33;
    }
    h1 {
        color: #00ff87 !important;
        text-shadow: 0px 0px 12px rgba(0, 255, 135, 0.4);
        font-weight: 800;
    }
    .stButton>button, .stDownloadButton>button {
        background: linear-gradient(180deg, #103a27 0%, #0a2519 100%);
        color: #6ee7b7;
        border: 1px solid #059669;
        border-radius: 12px;
        font-weight: 600;
        padding: 10px 16px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
        width: 100%;
    }
    .stButton>button:hover, .stDownloadButton>button:hover {
        background: #00ff87;
        color: #022c22;
        border-color: #00ff87;
        box-shadow: 0 0 15px rgba(0, 255, 135, 0.6);
        transform: translateY(-2px);
    }
    div[data-testid="stChatMessage"] {
        background-color: rgba(6, 44, 28, 0.6);
        border: 1px solid #0f5132;
        border-radius: 16px;
        padding: 12px;
        margin-bottom: 12px;
        backdrop-filter: blur(5px);
    }
    div[data-testid="stChatInput"] input {
        background-color: #041a10 !important;
        color: #ffffff !important;
        border: 1px solid #10b981 !important;
        border-radius: 10px !important;
    }
    ::-webkit-scrollbar {
        width: 8px;
    }
    ::-webkit-scrollbar-track {
        background: #04120c;
    }
    ::-webkit-scrollbar-thumb {
        background: #059669;
        border-radius: 4px;
    }
    </style>
""", unsafe_allow_html=True)

# ----------------------------------------------------
# 2. Setup API Keys
# ----------------------------------------------------
# ----------------------------------------------------
# 2. Setup API Keys
# ----------------------------------------------------
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", "YOUR_GROQ_API_KEY_HERE")
FOOTBALL_DATA_API_KEY = st.secrets.get("FOOTBALL_DATA_API_KEY", "YOUR_FOOTBALL_DATA_API_KEY_HERE")

groq_client = Groq(api_key=GROQ_API_KEY)
@st.cache_resource
def get_working_model():
    try:
        models_data = groq_client.models.list()
        available = [m.id for m in models_data.data]
        preferred = [
            "llama-3.3-70b-versatile",
            "openai/gpt-oss-20b",
            "llama-3.1-8b-instant",
            "qwen/qwen3.8-27b"
        ]
        for pref in preferred:
            if pref in available:
                return pref
        if available:
            return available[0]
    except Exception:
        pass
    return "openai/gpt-oss-20b"

SELECTED_MODEL = get_working_model()

# ----------------------------------------------------
# 3. Audio Player Helper Function
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
# 4. Sidebar: Multi-League Hub & Chat Log Exporter
# ----------------------------------------------------
LEAGUES = {
    "Premier League": "PL",
    "La Liga": "PD",
    "Champions League": "CL",
    "Serie A": "SA",
    "Bundesliga": "BL1",
    "FIFA World Cup 🏆": "WC"  # Add this!
}

st.sidebar.title("🏆 Global Football Hub")
selected_league_name = st.sidebar.selectbox("Select Competition", list(LEAGUES.keys()))
league_code = LEAGUES[selected_league_name]

def fetch_standings(code):
    if FOOTBALL_DATA_API_KEY == "YOUR_FOOTBALL_DATA_API_KEY_HERE":
        return None
    url = f"https://api.football-data.org/v4/competitions/{code}/standings"
    headers = {"X-Auth-Token": FOOTBALL_DATA_API_KEY}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return None

def fetch_upcoming_matches(code):
    if FOOTBALL_DATA_API_KEY == "YOUR_FOOTBALL_DATA_API_KEY_HERE":
        return None
    url = f"https://api.football-data.org/v4/competitions/{code}/matches?status=SCHEDULED"
    headers = {"X-Auth-Token": FOOTBALL_DATA_API_KEY}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return None

if FOOTBALL_DATA_API_KEY == "YOUR_FOOTBALL_DATA_API_KEY_HERE":
    st.sidebar.warning("⚠️ Add your `FOOTBALL_DATA_API_KEY` for live standings!")
else:
    with st.sidebar:
        st.subheader(f"📊 {selected_league_name} Standings")
        standings_data = fetch_standings(league_code)
        
        if standings_data and "standings" in standings_data:
            table_type = 0
            if "table" in standings_data["standings"][table_type]:
                table = standings_data["standings"][table_type]["table"][:5]
                for team in table:
                    st.write(f"**{team.get('position', '-')}. {team['team']['name']}** - {team.get('points', 0)} pts")
            else:
                st.info("Standings format updating.")
        else:
            st.info("Could not load standings for this league.")

        st.markdown("---")
        st.subheader("📅 Upcoming Fixtures")
        matches_data = fetch_upcoming_matches(league_code)
        if matches_data and "matches" in matches_data:
            upcoming = matches_data["matches"][:3]
            for match in upcoming:
                home = match["homeTeam"]["name"]
                away = match["awayTeam"]["name"]
                st.write(f"⚽ **{home}** vs **{away}**")
        else:
            st.info("No upcoming matches found.")

# Chat Log Export in Sidebar
st.sidebar.markdown("---")
st.sidebar.subheader("💾 Export Chat History")

# Initialize Chat Messages
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "system",
            "content": (
                "You are 'PitchAI', an expert football virtual assistant. "
                "You know everything about football tactics, players, history, and real-time scores across major world leagues. "
                "and legendary FIFA World Cup moments (from past tournaments up to the 2026 World Cup!). "
                "Keep responses enthusiastic, accurate, and concise."
            )
        },
        {
            "role": "assistant",
            "content": f"Welcome back! I am tuned into the {selected_league_name}. Switch leagues in the sidebar or ask me anything!"
        }
    ]

# Format chat log for download
chat_history_text = f"=== PitchAI Chat Log ({datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}) ===\n\n"
for msg in st.session_state.messages:
    if msg["role"] != "system":
        sender = "PitchAI" if msg["role"] == "assistant" else "You"
        chat_history_text += f"[{sender}]: {msg['content']}\n\n"

st.sidebar.download_button(
    label="📥 Download Chat Log (.txt)",
    data=chat_history_text,
    file_name=f"PitchAI_Chat_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
    mime="text/plain"
)

# ----------------------------------------------------
# 5. Main UI & Quick Prompt Buttons
# ----------------------------------------------------
st.title("⚽ PitchAI Virtual Assistant")
st.caption(f"Currently tracking: {selected_league_name} & Global Football Intelligence")

st.markdown("### ⚡ Quick Tactics")
col1, col2, col3 = st.columns(3)

prompt_to_send = None

with col1:
    if st.button("🌟 Top 5 Wonderkids"):
        prompt_to_send = "Who are the top 5 teenage wonderkids to watch out for in world football right now?"
with col2:
    if st.button("🧠 Tactical Breakdown"):
        prompt_to_send = f"Can you analyze the current title race and tactics in the {selected_league_name}?"
with col3:
    if st.button("🌍 World Cup Legends"):
        prompt_to_send = "What are some of the most iconic moments and greatest matches in FIFA World Cup history?"

# ----------------------------------------------------
# 6. Chat Logic
# ----------------------------------------------------
for msg in st.session_state.messages:
    if msg["role"] != "system":
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

chat_input = st.chat_input("Ask PitchAI a football question...")
user_query = chat_input if chat_input else prompt_to_send

if user_query:
    st.session_state.messages.append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.markdown(user_query)

    with st.chat_message("assistant"):
        with st.spinner("Analyzing pitch telemetry & synthesizing speech..."):
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