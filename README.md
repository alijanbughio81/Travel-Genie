# ✈️ TravelGenie

TravelGenie is a multi-agent AI travel planner built with Streamlit and Groq.

## Agents

1. Flights Agent — generates flight options.
2. Hotels Agent — generates hotel options.
3. Activities Agent — generates destination activities.
4. Weather Agent — gets daily weather data from Open-Meteo.
5. Budget Agent — selects the flight, hotel and activities that fit the budget.
6. Itinerary Agent — organizes the selected choices into a day-by-day plan.

## Project structure

```text
TravelGenie/
├── app.py
├── flights_agent.py
├── hotels_agent.py
├── activities_agent.py
├── weather_agent.py
├── budget_agent.py
├── itinerary_agent.py
├── requirements.txt
├── .gitignore
└── README.md
```

## Run locally

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
# source .venv/bin/activate

pip install -r requirements.txt
```

Create `.streamlit/secrets.toml`:

```toml
GROQ_API_KEY = "your_groq_api_key"
GROQ_MODEL = "openai/gpt-oss-120b"
```

Then:

```bash
streamlit run app.py
```

You can also set `GROQ_API_KEY` as an environment variable.

## Deploy to Streamlit Community Cloud

Push the project to GitHub, then create a Streamlit Community Cloud app using `app.py` as the entrypoint.

In the app's Secrets settings, add:

```toml
GROQ_API_KEY = "your_groq_api_key"
GROQ_MODEL = "openai/gpt-oss-120b"
```

Never commit your API key to GitHub.

## Important accuracy note

The Flights, Hotels and Activities agents generate estimates with the LLM. They are not live booking systems. For production use, replace these estimates with live APIs/search providers.

The Weather Agent uses Open-Meteo and therefore does not require a weather API key.
