import json
from groq import Groq

from src.config.config_loader import ConfigLoader

config = ConfigLoader()


class LLMExtractor:
    def __init__(self):
        self.client = Groq(
            api_key=config.get("GROQ_API_KEY")
        )

    def extract_route(self, query: str, stations: dict) -> tuple[str, str]:
        station_names = [data["nome"] for data in stations.values()]

        prompt = f"""
            You are a metro routing assistant.

            You MUST choose origin and destination ONLY from the provided station list.

            If no exact match exists, choose the closest match.

            Return ONLY valid JSON in this format:

            {{
            "origin": "EXACT_STATION_NAME",
            "destination": "EXACT_STATION_NAME"
            }}

            Available stations:
            {json.dumps(station_names, ensure_ascii=False)}

            User query:
            {query}
            """

        response = self.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            temperature=0,
        )

        content = response.choices[0].message.content.strip()
        # remove markdown code fences if present
        if content.startswith("```"):
            content = content.strip("`")          # removes ```
            content = content.replace("json", "", 1).strip()

        data = json.loads(content)
        print("LLM OUTPUT:")
        print(content)

        return (
            data["origin"],
            data["destination"],
        )