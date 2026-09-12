
import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")


def _client():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not configured.")
    return Groq(api_key=api_key)


def get_activities(destination, budget, travelers, duration, interests=None):
    """
    Generate activity options for a destination.

    Contract used by budget_agent:
      [
        {
          "name": "...",
          "estimated_cost": 0,
          "category": "...",
          "duration": "...",
          "indoor_outdoor": "indoor|outdoor|mixed"
        }
      ]

    estimated_cost is PER PERSON in PKR.
    Costs are estimates, not live prices.
    """
    interests = interests or ["sightseeing", "culture", "food", "nature"]

    prompt = f"""
You are a travel activities research assistant.

Destination: {destination}
Travelers: {travelers}
Trip duration: {duration} days
Total group budget (PKR): {budget}
User interests: {json.dumps(interests)}

Task:
1. Suggest 8 realistic activities/experiences in {destination}.
2. Include a useful mix of free/low-cost and paid activities.
3. Prefer recognizable attractions and experiences that genuinely fit the destination.
4. estimated_cost must be the approximate COST PER PERSON in PKR.
5. Do not invent precise ticket prices when uncertain; use reasonable estimates.
6. Mark each activity as indoor, outdoor, or mixed.
7. Include a short duration such as "2 hours".
8. Return ONLY valid JSON. No markdown and no extra text.

Return exactly:
[
  {{
    "name": "<activity>",
    "estimated_cost": <number>,
    "category": "<category>",
    "duration": "<duration>",
    "indoor_outdoor": "<indoor|outdoor|mixed>"
  }}
]
"""

    response = _client().chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=2500,
    )

    raw = response.choices[0].message.content.strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        start, end = raw.find("["), raw.rfind("]") + 1
        try:
            data = json.loads(raw[start:end])
        except Exception:
            return []

    if not isinstance(data, list):
        return []

    cleaned = []
    for item in data:
        if not isinstance(item, dict):
            continue
        cleaned.append({
            "name": str(item.get("name", "Unknown activity")),
            "estimated_cost": float(item.get("estimated_cost", 0) or 0),
            "category": str(item.get("category", "General")),
            "duration": str(item.get("duration", "Flexible")),
            "indoor_outdoor": str(item.get("indoor_outdoor", "mixed")).lower(),
        })
    return cleaned
