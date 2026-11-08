# Hacker News AI Stream

A local near-real-time pipeline that polls Hacker News for stories, classifies headlines with Ollama, stores the results in PostgreSQL, and displays them in a Streamlit dashboard.

## Data flow

Hacker News API -> Python polling producer -> in-memory event queue -> Ollama topic classifier -> PostgreSQL -> Streamlit dashboard

The producer polls every 15 seconds. At startup, it queues up to three current stories as sample events, then watches for new story IDs. The consumer asks the local gemma3:1b model to assign one topic using structured JSON output. PostgreSQL uses the Hacker News story ID as a primary key to avoid duplicate records. The dashboard refreshes from PostgreSQL every 15 seconds.

## Technology

- Python and requests
- Hacker News Firebase API
- Python queue and producer thread
- Ollama with gemma3:1b
- PostgreSQL
- Streamlit and pandas

## Run locally

Prerequisites: Python 3.11 or later, PostgreSQL, and Ollama.

    python3 -m venv .venv
    source .venv/bin/activate
    python -m pip install -r requirements.txt

    ollama pull gemma3:1b
    createdb hn_ai_stream
    psql -d hn_ai_stream -f sql/schema.sql

Start Ollama, then run the pipeline in one terminal:

    source .venv/bin/activate
    python src/pipeline.py

Run the dashboard in another terminal:

    source .venv/bin/activate
    streamlit run dashboard.py

Open the local URL printed by Streamlit. The dashboard shows saved stories, topic counts, and the latest classification time.

## Design notes and limitations

- This is a local polling demo with an in-memory queue, not a Kafka deployment.
- Stories waiting in the queue are lost if the process stops. Successfully inserted records remain in PostgreSQL.
- Ollama sees only each headline, not the linked article. Topic labels are heuristic and should be reviewed before drawing conclusions.
- The pipeline processes the current top three stories as a sample at startup and then handles newly appearing stories. It does not backfill the complete Hacker News history.

## Sources

- [Hacker News API](https://github.com/HackerNews/API)
- [Ollama API](https://github.com/ollama/ollama/blob/main/docs/api.md)
