import json

import requests


OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "gemma3:1b"

TOPICS = [
    "AI/ML",
    "Programming",
    "Business",
    "Science",
    "Politics",
    "Security",
    "Other",
]

OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "topic": {"type": "string", "enum": TOPICS},
    },
    "required": ["topic"],
    "additionalProperties": False,
}


def classify_title(title: str) -> dict:
    payload = {
        "model": MODEL,
        "stream": False,
        "format": OUTPUT_SCHEMA,
        "messages": [
            {
                "role": "user",
                "content": (
                    "Choose the single best topic for this headline. "
                    "Use only information explicitly present in the headline. "
                    "Return only the topic label.\n"
                    f"Headline: {title}"
                ),
            }
        ],
    }

    response = requests.post(OLLAMA_URL, json=payload, timeout=120)
    response.raise_for_status()

    content = response.json()["message"]["content"]
    result = json.loads(content)

    if set(result) != {"topic"} or result["topic"] not in TOPICS:
        raise ValueError(f"Invalid Ollama result: {result}")

    return result


if __name__ == "__main__":
    print(classify_title("Crypto industry braces for reckoning over Trump ties"))