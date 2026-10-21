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
    page_title="PitchAI - Football & World Cup Hub",
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
        backdrop-filter: blur(6px);
    }
    div[data-testid="stChatInput"] input {
        background-color: #020f09 !important;
        color: #ffffff !important;
        border: 1px solid #10b981 !important;
        border-radius: 10px !important;
    }
    ::-webkit-scrollbar {
        width: 8px;
    }
    ::-webkit-scrollbar-track {
        background: #020d08;
    }
    ::-webkit-scrollbar-thumb {
        background: #059669;
        border-radius: 4px;
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
# 4. Sidebar: Multi-League & FIFA World Cup Hub
# ----------------------------------------------------
LEAGUES = {
    "FIFA World Cup 🏆": "WC",
    "Premier League": "PL",
    "La Liga": "PD",
    "Champions League": "CL",
    "Serie A": "SA",
    "Bundesliga": "BL1"
}

st.sidebar.title("🏆 Football & World Cup Hub")
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

if selected_league_name == "FIFA World Cup 🏆":
    st.sidebar.markdown("### 🥇 2026 World Cup Final")
    st.sidebar.info("🏆 **Champions:** Spain 🇪🇸 (1–0 vs Argentina in ET)\n\n⚽ **Winner Goal:** Ferran Torres (106')")
    
    st.sidebar.markdown("### 📜 World Cup Roll of Honor")
    st.sidebar.write("• **2026:** Spain 🇪🇸")
    st.sidebar.write("• **2022:** Argentina 🇦🇷")
    st.sidebar.write("• **2018:** France 🇫🇷")
    st.sidebar.write("• **2014:** Germany 🇩🇪")
    st.sidebar.write("• **2010:** Spain 🇪🇸")
else:
    if FOOTBALL_DATA_API_KEY == "YOUR_FOOTBALL_DATA_API_KEY_HERE":
        st.sidebar.warning("⚠️ Add `FOOTBALL_DATA_API_KEY` to Streamlit Secrets for live standings.")
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
                st.info("Standings currently unavailable.")

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
                st.info("No upcoming scheduled fixtures found.")

# Chat Export
st.sidebar.markdown("---")
st.sidebar.subheader("💾 Export Chat Log")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "system",
            "content": (
                "You are 'PitchAI', an expert football virtual assistant. "
                "You possess knowledge of football tactics, player stats, historical records, and tournament outcomes. "
                "Keep in mind that Spain won the 2026 FIFA World Cup, defeating Argentina 1-0 in the final after extra time, "
                "with Ferran Torres scoring the winning goal in the 106th minute. Argentina won in 2022. "
                "Maintain an enthusiastic, accurate, and concise tone."
            )
        },
        {
            "role": "assistant",
            "content": f"Welcome! I am PitchAI, tuned into {selected_league_name}. Ask me about World Cup records, player stats, or match tactics!"
        }
    ]

chat_history_text = f"=== PitchAI Chat Log ({datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}) ===\n\n"
for msg in st.session_state.messages:
    if msg["role"] != "system":
        sender = "PitchAI" if msg["role"] == "assistant" else "You"
        chat_history_text += f"[{sender}]: {msg['content']}\n\n"

st.sidebar.download_button(
    label="📥 Download Log (.txt)",
    data=chat_history_text,
    file_name=f"PitchAI_Chat_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
    mime="text/plain"
)

# ----------------------------------------------------
# 5. Main Dashboard & Tactical Shortcuts
# ----------------------------------------------------
st.title("⚽ PitchAI Virtual Assistant")
st.caption(f"Tracking: {selected_league_name} & World Football Telemetry")

st.markdown("### ⚡ Quick Insights & Player Intelligence")
col1, col2, col3 = st.columns(3)

prompt_to_send = None

with col1:
    if st.button("🏆 2026 World Cup Recap"):
        prompt_to_send = "Can you summarize the 2026 FIFA World Cup final match between Spain and Argentina, including key goals and moments?"
with col2:
    if st.button("📊 Custom Player Analytics"):
        prompt_to_send = "Provide a comprehensive career and stat breakdown comparing Kylian Mbappé, Erling Haaland, and Lamine Yamal."
with col3:
    if st.button("👑 All-Time GOAT Rankings"):
        prompt_to_send = "Compare the prime statistics, World Cup achievements, and playing styles of Lionel Messi, Pelé, and Diego Maradona."

# ----------------------------------------------------
# 6.