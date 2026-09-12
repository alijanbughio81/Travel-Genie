
import os
from datetime import date

import streamlit as st

# ---------------------------------------------------------
# TravelGenie - configuration
# ---------------------------------------------------------
st.set_page_config(
    page_title="TravelGenie",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Streamlit Community Cloud stores secrets in st.secrets.
# The existing agent files read GROQ_API_KEY from the environment,
# so we bridge Streamlit secrets -> environment before importing agents.
if "GROQ_API_KEY" in st.secrets:
    os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]

if "GROQ_MODEL" in st.secrets:
    os.environ["GROQ_MODEL"] = st.secrets["GROQ_MODEL"]

# Import after the environment variable has been configured.
from flights_agent import get_flights
from hotels_agent import get_hotels
from budget_agent import calculate_budget
from itinerary_agent import build_itinerary
from activities_agent import get_activities
from weather_agent import get_weather


# ---------------------------------------------------------
# Styling
# ---------------------------------------------------------
st.markdown(
    """
    <style>
    .main-title {
        font-size: 3.0rem;
        font-weight: 800;
        margin-bottom: 0.1rem;
    }
    .subtitle {
        font-size: 1.15rem;
        color: #6b7280;
        margin-bottom: 1.5rem;
    }
    .agent-card {
        border: 1px solid rgba(128,128,128,.22);
        border-radius: 14px;
        padding: 1rem;
        height: 100%;
        background: rgba(128,128,128,.04);
    }
    .small-muted {
        color: #6b7280;
        font-size: .9rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def money(value):
    try:
        return f"PKR {float(value):,.0f}"
    except Exception:
        return "PKR —"


def run_agent_safely(label, fn, *args, **kwargs):
    with st.status(label, expanded=False) as status:
        try:
            result = fn(*args, **kwargs)
            status.update(label=f"✓ {label}", state="complete")
            return result
        except Exception as exc:
            status.update(label=f"✗ {label}", state="error")
            raise exc


# ---------------------------------------------------------
# Header
# ---------------------------------------------------------
st.markdown('<div class="main-title">✈️ TravelGenie</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">Your AI travel planner — flights, hotels, activities, weather, budget and itinerary in one place.</div>',
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# Sidebar inputs
# ---------------------------------------------------------
with st.sidebar:
    st.header("🌍 Trip details")

    origin = st.text_input("From", value="Karachi, Pakistan")
    destination = st.text_input("Destination", value="Istanbul, Turkey")

    travelers = st.number_input(
        "Travelers",
        min_value=1,
        max_value=20,
        value=2,
        step=1,
    )

    duration = st.number_input(
        "Trip duration (days)",
        min_value=1,
        max_value=30,
        value=4,
        step=1,
    )

    trip_start = st.date_input(
        "Trip start date",
        value=date.today(),
        min_value=date.today(),
    )

    budget = st.number_input(
        "Total budget (PKR)",
        min_value=1000,
        max_value=100000000,
        value=100000,
        step=5000,
    )

    interests = st.multiselect(
        "Interests",
        [
            "Sightseeing",
            "Culture & history",
            "Food",
            "Nature",
            "Shopping",
            "Adventure",
            "Family",
            "Nightlife",
            "Museums",
            "Photography",
        ],
        default=["Sightseeing", "Culture & history", "Food"],
    )

    plan_button = st.button(
        "✨ Build my trip",
        type="primary",
        use_container_width=True,
    )

    st.divider()
    st.caption("TravelGenie uses Groq for AI planning and Open-Meteo for weather data.")


# ---------------------------------------------------------
# Agent overview
# ---------------------------------------------------------
cols = st.columns(6)
cards = [
    ("✈️", "Flights", "Flight options"),
    ("🏨", "Hotels", "Stay options"),
    ("🎯", "Activities", "Things to do"),
    ("🌤️", "Weather", "Daily forecast"),
    ("💰", "Budget", "Best combination"),
    ("🗓️", "Itinerary", "Day-by-day plan"),
]
for col, (icon, title, desc) in zip(cols, cards):
    with col:
        st.markdown(
            f"""
            <div class="agent-card">
                <div style="font-size:1.8rem">{icon}</div>
                <b>{title}</b><br>
                <span class="small-muted">{desc}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ---------------------------------------------------------
# Main workflow
# ---------------------------------------------------------
if plan_button:
    if not origin.strip() or not destination.strip():
        st.error("Please enter both your origin and destination.")
        st.stop()

    st.session_state["trip_inputs"] = {
        "origin": origin,
        "destination": destination,
        "travelers": int(travelers),
        "duration": int(duration),
        "trip_start": trip_start,
        "budget": float(budget),
        "interests": interests,
    }

    try:
        # 1. Independent research agents
        flights = run_agent_safely(
            "Finding flight options...",
            get_flights,
            origin.strip(),
            destination.strip(),
            float(budget),
            int(travelers),
            int(duration),
        )

        hotels = run_agent_safely(
            "Finding hotel options...",
            get_hotels,
            destination.strip(),
            float(budget),
            int(travelers),
            int(duration),
        )

        activities = run_agent_safely(
            "Finding activities...",
            get_activities,
            destination.strip(),
            float(budget),
            int(travelers),
            int(duration),
            interests,
        )

        weather = run_agent_safely(
            "Getting weather forecast...",
            get_weather,
            destination.strip(),
            int(duration),
            trip_start,
        )

        if not flights:
            st.error("The Flights agent returned no options.")
            st.stop()
        if not hotels:
            st.error("The Hotels agent returned no options.")
            st.stop()
        if not activities:
            st.warning("The Activities agent returned no activities. Budget planning will continue with no activity choices.")

        # 2. Budget agent is the decision-maker.
        budget_summary = run_agent_safely(
            "Optimizing the trip against your budget...",
            calculate_budget,
            flights,
            hotels,
            activities,
            float(budget),
            int(travelers),
            int(duration),
        )

        # 3. Itinerary agent only organizes the already-selected choices.
        itinerary = run_agent_safely(
            "Building your day-by-day itinerary...",
            build_itinerary,
            budget_summary,
            weather,
            int(duration),
        )

        st.session_state["flights"] = flights
        st.session_state["hotels"] = hotels
        st.session_state["activities"] = activities
        st.session_state["weather"] = weather
        st.session_state["budget_summary"] = budget_summary
        st.session_state["itinerary"] = itinerary

        st.success("🎉 Your TravelGenie plan is ready!")

    except Exception as exc:
        st.error(f"TravelGenie could not complete the plan: {exc}")
        st.info("Check that GROQ_API_KEY is configured and that the destination is a valid place name.")


# ---------------------------------------------------------
# Results
# ---------------------------------------------------------
if "budget_summary" in st.session_state:
    flights = st.session_state["flights"]
    hotels = st.session_state["hotels"]
    activities = st.session_state["activities"]
    weather = st.session_state["weather"]
    budget_summary = st.session_state["budget_summary"]
    itinerary = st.session_state["itinerary"]

    st.divider()
    st.header("🧭 Your TravelGenie plan")

    chosen_flight = budget_summary.get("chosen_flight")
    chosen_hotel = budget_summary.get("chosen_hotel")
    total = budget_summary.get("total_estimated_cost", 0)
    user_budget = budget_summary.get("user_budget", budget)
    within = budget_summary.get("within_budget", False)

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Estimated total", money(total))
    k2.metric("Your budget", money(user_budget))
    k3.metric("Travelers", int(travelers))
    k4.metric("Duration", f"{int(duration)} days")

    if within:
        st.success("✅ The selected plan is within your budget.")
    else:
        st.warning("⚠️ The selected plan is above budget. Review the suggestions and consider a cheaper option.")

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🗓️ Itinerary",
        "💰 Budget",
        "✈️ Flights",
        "🏨 Hotels",
        "🎯 Activities",
        "🌤️ Weather",
    ])

    with tab1:
        st.subheader("Day-by-day itinerary")
        for day in itinerary:
            day_no = day.get("day", "?")
            day_date = day.get("date", "")
            day_weather = day.get("weather", "N/A")
            day_cost = day.get("estimated_day_cost", 0)

            with st.container(border=True):
                st.markdown(f"### Day {day_no} — {day_date}")
                st.write(f"**Weather:** {day_weather}")
                if day.get("flight"):
                    flight = day["flight"]
                    st.write(
                        f"✈️ **Arrival:** {flight.get('airline', 'Flight')} "
                        f"{flight.get('departure_time', '')} → {flight.get('arrival_time', '')}"
                    )

                hotel = day.get("hotel")
                if hotel:
                    st.write(f"🏨 **Hotel:** {hotel.get('name', 'Selected hotel')}")

                acts = day.get("activities") or []
                if acts:
                    for act in acts:
                        st.write(
                            f"• **{act.get('time', '')}** — "
                            f"{act.get('activity', act.get('name', 'Activity'))} "
                            f"({money(act.get('cost', 0))})"
                        )
                else:
                    st.write("No selected activity scheduled for this day.")

                st.caption(f"Estimated day cost: {money(day_cost)}")

    with tab2:
        st.subheader("Budget breakdown")
        breakdown = budget_summary.get("breakdown", {})
        b1, b2, b3, b4 = st.columns(4)
        b1.metric("Flights", money(breakdown.get("flights", 0)))
        b2.metric("Hotels", money(breakdown.get("hotels", 0)))
        b3.metric("Activities", money(breakdown.get("activities", 0)))
        b4.metric("Misc.", money(breakdown.get("misc", 0)))

        st.write("### Selected choices")
        if chosen_flight:
            st.write(
                f"✈️ **{chosen_flight.get('airline', 'Flight')}** — "
                f"{money(chosen_flight.get('price', 0))} per person"
            )
        if chosen_hotel:
            st.write(
                f"🏨 **{chosen_hotel.get('name', 'Hotel')}** — "
                f"{money(chosen_hotel.get('price_per_night', 0))} per room/night"
            )

        suggestions = budget_summary.get("suggestions", [])
        if suggestions:
            st.write("### 💡 Suggestions")
            for suggestion in suggestions:
                st.write(f"• {suggestion}")

    with tab3:
        st.subheader("Flight options")
        for i, flight in enumerate(flights, 1):
            with st.container(border=True):
                st.markdown(f"**Option {i}: {flight.get('airline', 'Unknown airline')}**")
                c1, c2, c3 = st.columns(3)
                c1.write(f"**Price:** {money(flight.get('price', 0))} / person")
                c2.write(f"**Departure:** {flight.get('departure_time', 'N/A')}")
                c3.write(f"**Arrival:** {flight.get('arrival_time', 'N/A')}")
                st.caption(
                    f"{flight.get('from', origin)} → {flight.get('to', destination)}"
                )

    with tab4:
        st.subheader("Hotel options")
        for i, hotel in enumerate(hotels, 1):
            with st.container(border=True):
                st.markdown(f"**Option {i}: {hotel.get('name', 'Unknown hotel')}**")
                c1, c2, c3 = st.columns(3)
                c1.write(f"**Price:** {money(hotel.get('price_per_night', 0))} / night")
                c2.write(f"**Rating:** {hotel.get('rating', 'N/A')}")
                c3.write(f"**Location:** {hotel.get('location', 'N/A')}")
                amenities = hotel.get("amenities", [])
                if amenities:
                    st.caption("Amenities: " + ", ".join(map(str, amenities)))

    with tab5:
        st.subheader("Activity options")
        if activities:
            for activity in activities:
                with st.container(border=True):
                    c1, c2 = st.columns([3, 1])
                    with c1:
                        st.markdown(f"**{activity.get('name', 'Activity')}**")
                        st.caption(
                            f"{activity.get('category', 'General')} • "
                            f"{activity.get('duration', 'Flexible')} • "
                            f"{activity.get('indoor_outdoor', 'mixed').title()}"
                        )
                    with c2:
                        st.metric("Per person", money(activity.get("estimated_cost", 0)))
        else:
            st.info("No activities were returned.")

    with tab6:
        st.subheader("Weather")
        for day in weather:
            high = day.get("temp_high")
            low = day.get("temp_low")
            rain = day.get("precipitation_probability")

            if high is None:
                temperature = "Forecast unavailable"
            else:
                temperature = f"{high}°C / {low}°C"

            rain_text = "N/A" if rain is None else f"{rain}% rain chance"

            st.write(
                f"**{day.get('date', 'N/A')}** — "
                f"{day.get('condition', 'N/A')} — "
                f"{temperature} — {rain_text}"
            )

    with st.expander("🔧 View raw agent outputs"):
        st.json({
            "flights": flights,
            "hotels": hotels,
            "activities": activities,
            "weather": weather,
            "budget_summary": budget_summary,
            "itinerary": itinerary,
        })
else:
    st.info("Enter your trip details in the sidebar and click **Build my trip** to start.")
