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
API_FOOTBALL_KEY = st.secrets.get("API_FOOTBALL_KEY", "")
API_FOOTBALL_LEAGUE_IDS = {"WC": 1, "PL": 39, "PD": 140, "CL": 2, "SA": 135, "BL1": 78}

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
# 4. API Functions for Match Data & Standings
# ----------------------------------------------------
LEAGUES = {
    "FIFA World Cup 🏆": "WC",
    "Premier League": "PL",
    "La Liga": "PD",
    "Champions League": "CL",
    "Serie A": "SA",
    "Bundesliga": "BL1"
}

st.sidebar.title("🏆 Football Hub")
selected_league_name = st.sidebar.selectbox("Select Competition", list(LEAGUES.keys()))
league_code = LEAGUES[selected_league_name]

@st.cache_data(ttl=60, show_spinner=False)
def fetch_finished_matches(code):
    if FOOTBALL_DATA_API_KEY == "YOUR_FOOTBALL_DATA_API_KEY_HERE" or not FOOTBALL_DATA_API_KEY:
        st.warning("⚠️ FOOTBALL_DATA_API_KEY is missing in Streamlit Secrets.")
        return []
    url = f"https://api.football-data.org/v4/competitions/{code}/matches?status=FINISHED"
    headers = {"X-Auth-Token": FOOTBALL_DATA_API_KEY}
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            return res.json().get("matches", [])
    except Exception:
        pass
    return []

@st.cache_data(ttl=60, show_spinner=False)
def fetch_upcoming_or_live_matches(code):
    if FOOTBALL_DATA_API_KEY == "YOUR_FOOTBALL_DATA_API_KEY_HERE" or not FOOTBALL_DATA_API_KEY:
        return []
    url = f"https://api.football-data.org/v4/competitions/{code}/matches?status=SCHEDULED,TIMED,IN_PLAY,PAUSED"
    headers = {"X-Auth-Token": FOOTBALL_DATA_API_KEY}
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            return res.json().get("matches", [])
    except Exception:
        pass
    return []

@st.cache_data(ttl=60, show_spinner=False)
def fetch_standings(code):
    if FOOTBALL_DATA_API_KEY == "YOUR_FOOTBALL_DATA_API_KEY_HERE":
        return None
    url = f"https://api.football-data.org/v4/competitions/{code}/standings"
    headers = {"X-Auth-Token": FOOTBALL_DATA_API_KEY}
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    return None

def get_team_league_position(standings_json, team_id):
    if not standings_json or "standings" not in standings_json:
        return "N/A", "N/A"
    try:
        table = standings_json["standings"][0]["table"]
        for row in table:
            if row["team"]["id"] == team_id:
                return row.get("position", "-"), row.get("points", "-")
    except Exception:
        pass
    return "N/A", "N/A"
@st.cache_data(ttl=60, show_spinner=False)
def fetch_api_football_live_matches(api_key):
    if not api_key:
        return {"matches": [], "error": "Add API_FOOTBALL_KEY to Streamlit Secrets to use free live match details."}
    try:
        response = requests.get(
            "https://v3.football.api-sports.io/fixtures",
            params={"live": "all"},
            headers={"x-apisports-key": api_key},
            timeout=15,
        )
        if response.status_code != 200:
            return {"matches": [], "error": f"API-Football returned HTTP {response.status_code}."}
        payload = response.json()
        errors = payload.get("errors")
        if errors:
            error_text = "; ".join(f"{key}: {value}" for key, value in errors.items()) if isinstance(errors, dict) else str(errors)
            return {"matches": [], "error": f"API-Football: {error_text}"}
        return {"matches": payload.get("response", []), "error": ""}
    except requests.RequestException:
        return {"matches": [], "error": "Could not connect to API-Football. Check your internet connection."}
    except ValueError:
        return {"matches": [], "error": "API-Football returned an unreadable response."}


@st.cache_data(ttl=300, show_spinner=False)
def fetch_api_football_match_details(fixture_id, api_key):
    try:
        response = requests.get(
            "https://v3.football.api-sports.io/fixtures",
            params={"id": str(fixture_id)},
            headers={"x-apisports-key": api_key},
            timeout=15,
        )
        if response.status_code != 200:
            return {"match": None, "error": f"API-Football returned HTTP {response.status_code}."}
        payload = response.json()
        errors = payload.get("errors")
        if errors:
            error_text = "; ".join(f"{key}: {value}" for key, value in errors.items()) if isinstance(errors, dict) else str(errors)
            return {"match": None, "error": f"API-Football: {error_text}"}
        matches = payload.get("response", [])
        return {"match": matches[0] if matches else None, "error": ""}
    except requests.RequestException:
        return {"match": None, "error": "Could not load match details from API-Football."}
    except ValueError:
        return {"match": None, "error": "API-Football returned an unreadable match response."}


# ----------------------------------------------------
# 5. Main Layout with Tabs
# ----------------------------------------------------
st.title("⚽ PitchAI Virtual Assistant")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "💬 PitchAI Chat", 
    "📅 Match Center & Telemetry", 
    "🏆 League Standings", 
    "⚡ Match Status",
    "🔴 Live Scores"   # <--- 5th Tab added here
])

# --- TAB 1: Chatbot Interface ---
with tab1:
    st.caption(f"Currently tracking: {selected_league_name}")
    
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "system", "content": "You are 'PitchAI', an expert football virtual assistant."},
            {"role": "assistant", "content": f"Welcome! I am PitchAI, tuned into {selected_league_name}. Ask me anything!"}
        ]

    chat_container = st.container()
    
    with chat_container:
        for msg in st.session_state.messages:
            if msg["role"] != "system":
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

    chat_input = st.chat_input("Ask PitchAI about matches, lineups, or stats...")
    
    if chat_input:
        st.session_state.messages.append({"role": "user", "content": chat_input})
        with chat_container:
            with st.chat_message("user"):
                st.markdown(chat_input)

        with chat_container:
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

# --- TAB 2: Match Center & Detailed Telemetry ---
with tab2:
    st.header(f"📊 {selected_league_name} Match Center")
    
    finished_matches = fetch_finished_matches(league_code)
    standings_data = fetch_standings(league_code)
    
    if finished_matches:
        match_options = {}
        for m in finished_matches[-15:]:
            home_name = m.get('homeTeam', {}).get('name', 'Home')
            away_name = m.get('awayTeam', {}).get('name', 'Away')
            score_dict = m.get('score', {}).get('fullTime', {})
            home_score = score_dict.get('home', 0) if score_dict and score_dict.get('home') is not None else 0
            away_score = score_dict.get('away', 0) if score_dict and score_dict.get('away') is not None else 0
            date_str = m.get('utcDate', '')[:10]
            
            label = f"{home_name} {home_score} - {away_score} {away_name} ({date_str})"
            match_options[label] = m
        
        selected_match_label = st.selectbox("Select a Recent Match to View Detailed Telemetry", list(match_options.keys()))
        selected_match = match_options[selected_match_label]
        
        home_team = selected_match["homeTeam"]
        away_team = selected_match["awayTeam"]
        
        st.markdown("---")
        
        goals = selected_match.get("goals", [])
        if goals:
            st.markdown("#### ⚽ Goal Scorers")
            for goal in goals:
                scorer = goal.get("scorer", {}).get("name", "Unknown Player")
                minute = goal.get("minute", "?")
                team_info = goal.get("team", {}).get("name", "")
                st.write(f"• **{minute}'** — {scorer} ({team_info})")
        else:
            st.info("Goal scorer minute timeline is not indexed for this specific match feed.")

        st.markdown("---")
        st.subheader("📋 Starting Lineups & Squads")
        
        home_lineup = selected_match.get("homeTeam", {}).get("lineup", [])
        away_lineup = selected_match.get("awayTeam", {}).get("lineup", [])
        
        col_l1, col_l2 = st.columns(2)
        
        if home_lineup and away_lineup:
            with col_l1:
                st.write(f"**{home_team['name']}**")
                for player in home_lineup:
                    st.text(f"• #{player.get('shirtNumber', '-')} {player.get('name', 'Player')}")
            with col_l2:
                st.write(f"**{away_team['name']}**")
                for player in away_lineup:
                    st.text(f"• #{player.get('shirtNumber', '-')} {player.get('name', 'Player')}")
        else:
            st.info("💡 Generating tactical starting XI using PitchAI Telemetry...")
            lineup_prompt = f"Provide the likely starting 11 lineup and formation for a match between {home_team['name']} and {away_team['name']}. Format as two clean bulleted lists."
            try:
                lineup_res = groq_client.chat.completions.create(
                    model=SELECTED_MODEL,
                    messages=[
                        {"role": "system", "content": "You are PitchAI. Give direct, concise football starting 11 lineups without introductory fluff."},
                        {"role": "user", "content": lineup_prompt}
                    ],
                    temperature=0.3,
                )
                st.markdown(lineup_res.choices[0].message.content)
            except Exception:
                st.warning("Lineup telemetry unavailable.")

# --- TAB 3: Live League Standings ---
with tab3:
    st.header(f"🏆 {selected_league_name} Live Standings")
    
    standings_json = fetch_standings(league_code)
    
    if standings_json and "standings" in standings_json:
        try:
            table_data = standings_json["standings"][0]["table"]
            formatted_table = []
            for row in table_data:
                formatted_table.append({
                    "Pos": row.get("position"),
                    "Team": row.get("team", {}).get("name"),
                    "P": row.get("playedGames"),
                    "W": row.get("won"),
                    "D": row.get("draw"),
                    "L": row.get("lost"),
                    "GF": row.get("goalsFor"),
                    "GA": row.get("goalsAgainst"),
                    "GD": row.get("goalDifference"),
                    "Pts": row.get("points")
                })
            st.dataframe(formatted_table, use_container_width=True, hide_index=True)
        except Exception as e:
            st.error(f"Could not parse standings table: {e}")
    else:
        st.warning("⚠️ Standings data unavailable. Check your `FOOTBALL_DATA_API_KEY`.")

# --- TAB 4: Match Status & Schedule ---
with tab4:
    st.header(f"⚡ {selected_league_name} Match Status & Schedule")
    
    status_matches = fetch_upcoming_or_live_matches(league_code)
    
    if status_matches:
        match_status_list = []
        for m in status_matches:
            home_name = m.get('homeTeam', {}).get('name', 'Home')
            away_name = m.get('awayTeam', {}).get('name', 'Away')
            status = m.get('status', 'UNKNOWN')
            utc_date = m.get('utcDate', '')
            matchday = m.get('matchday', '-')
            
            match_status_list.append({
                "Matchday": f"MD {matchday}",
                "Home Team": home_name,
                "Status": status,
                "Away Team": away_name,
                "Kickoff (UTC)": utc_date.replace('T', ' ')[:16] if utc_date else '-'
            })
            
        st.dataframe(match_status_list, use_container_width=True, hide_index=True)
    else:
        st.info(f"No upcoming or live matches currently scheduled for {selected_league_name}.")
# --- TAB 5: Live Scores and Match Details ---
with tab5:
    st.header(f"🔴 {selected_league_name} Live Match Center")
    st.caption("Live scores, goal events, and lineups are provided by API-Football. The free plan has a daily request limit, so scores refresh manually.")

    if not API_FOOTBALL_KEY:
        st.warning("To show goal scorers and lineups, create a free API-Football key and add it to Streamlit Secrets as API_FOOTBALL_KEY.")
    else:
        if st.button("↻ Refresh live scores", use_container_width=True):
            fetch_api_football_live_matches.clear()

        api_live_result = fetch_api_football_live_matches(API_FOOTBALL_KEY)
        if api_live_result["error"]:
            st.warning(api_live_result["error"])
        else:
            league_id = API_FOOTBALL_LEAGUE_IDS.get(league_code)
            live_matches = [
                match for match in api_live_result["matches"]
                if match.get("league", {}).get("id") == league_id
            ]

            if live_matches:
                st.success(f"⚡ {len(live_matches)} {selected_league_name} match(es) currently live!")
                for match in live_matches:
                    fixture_id = match.get("fixture", {}).get("id")
                    home = match.get("teams", {}).get("home", {}).get("name", "Home")
                    away = match.get("teams", {}).get("away", {}).get("name", "Away")
                    goals = match.get("goals", {})
                    home_goals = goals.get("home") if goals.get("home") is not None else 0
                    away_goals = goals.get("away") if goals.get("away") is not None else 0
                    status = match.get("fixture", {}).get("status", {})
                    elapsed = status.get("elapsed")
                    clock = f"{elapsed}'" if elapsed is not None else status.get("long", "LIVE")

                    if st.button(
                        f"⚽  {home}  {home_goals} - {away_goals}  {away}   ·   {clock}   ·   View details",
                        key=f"api_live_match_{fixture_id}",
                        use_container_width=True,
                    ):
                        st.session_state["selected_api_football_fixture_id"] = fixture_id

                selected_fixture_id = st.session_state.get("selected_api_football_fixture_id")
                selected_match_stub = next(
                    (match for match in live_matches if match.get("fixture", {}).get("id") == selected_fixture_id),
                    None,
                )
                if selected_match_stub:
                    details_result = fetch_api_football_match_details(selected_fixture_id, API_FOOTBALL_KEY)
                    if details_result["error"]:
                        st.warning(details_result["error"])
                    elif details_result["match"]:
                        details = details_result["match"]
                        teams = details.get("teams", {})
                        home_team = teams.get("home", {})
                        away_team = teams.get("away", {})
                        status = details.get("fixture", {}).get("status", {})
                        status_text = status.get("long", "Unknown status")
                        elapsed = status.get("elapsed")
                        if elapsed is not None:
                            status_text += f" · {elapsed}'"

                        st.markdown("---")
                        st.subheader(
                            f"{home_team.get('name', 'Home')} {details.get('goals', {}).get('home', 0)} - "
                            f"{details.get('goals', {}).get('away', 0)} {away_team.get('name', 'Away')}"
                        )
                        st.caption(f"Match status: {status_text}")

                        st.markdown("#### ⚽ Goal scorers")
                        events = details.get("events") or []
                        goal_events = [event for event in events if event.get("type") == "Goal"]
                        if goal_events:
                            for event in goal_events:
                                event_time = event.get("time", {})
                                minute = event_time.get("elapsed", "?")
                                extra = event_time.get("extra")
                                minute_label = f"{minute}+{extra}'" if extra else f"{minute}'"
                                player = (event.get("player") or {}).get("name", "Unknown player")
                                team_name = (event.get("team") or {}).get("name", "")
                                detail = event.get("detail", "Goal")
                                assist = (event.get("assist") or {}).get("name")
                                assist_text = f" (assist: {assist})" if assist else ""
                                st.write(f"**{minute_label}** — {player}{assist_text} · {team_name} · {detail}")
                        else:
                            st.info("No goal events were returned for this match. Coverage can vary by competition.")

                        st.markdown("#### 🧾 Starting lineups")
                        lineups = details.get("lineups") or []
                        if lineups:
                            lineup_col1, lineup_col2 = st.columns(2)
                            for col, lineup in zip((lineup_col1, lineup_col2), lineups):
                                with col:
                                    team = lineup.get("team", {})
                                    formation = lineup.get("formation")
                                    formation_text = f" · {formation}" if formation else ""
                                    st.markdown(f"**{team.get('name', 'Team')}{formation_text}**")
                                    starters = lineup.get("startXI") or []
                                    for entry in starters:
                                        player = entry.get("player", {})
                                        number = player.get("number")
                                        shirt = f"#{number} " if number is not None else ""
                                        position = player.get("pos")
                                        role = f" — {position}" if position else ""
                                        st.write(f"{shirt}{player.get('name', 'Player')}{role}")
                                    substitutes = lineup.get("substitutes") or []
                                    if substitutes:
                                        with st.expander(f"{team.get('name', 'Team')} bench"):
                                            for entry in substitutes:
                                                player = entry.get("player", {})
                                                number = player.get("number")
                                                shirt = f"#{number} " if number is not None else ""
                                                st.write(f"{shirt}{player.get('name', 'Player')}")
                        else:
                            st.info("Lineups are not available yet for this match or competition.")
                    else:
                        st.info("Match details have not been published by API-Football yet.")
            elif league_id is None:
                st.warning("This competition is not mapped for API-Football yet.")
            else:
                st.info(f"No {selected_league_name} matches are live right now.")
