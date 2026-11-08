import threading
from datetime import datetime, timezone
from queue import Empty, Queue

import psycopg
import requests
from psycopg.types.json import Jsonb

from classifier import classify_title


HN_BASE_URL = "https://hacker-news.firebaseio.com/v0"
DATABASE_URL = "dbname=hn_ai_stream"
MODEL_NAME = "gemma3:1b"
POLL_SECONDS = 15

event_queue = Queue(maxsize=100)
stop_event = threading.Event()


def get_json(url: str):
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.json()


def produce_events():
    initial_ids = get_json(f"{HN_BASE_URL}/newstories.json")
    known_ids = set(initial_ids)
    print(f"Watching Hacker News; startup baseline has {len(known_ids)} story IDs.")

    for story_id in reversed(initial_ids[:3]):
        try:
            story = get_json(f"{HN_BASE_URL}/item/{story_id}.json")
            if story and story.get("type") == "story" and story.get("title"):
                event_queue.put(story)
                print(f"Queued startup sample: {story['title']}")
        except requests.RequestException as error:
            print(f"Could not fetch startup story {story_id}: {error}")

    while not stop_event.is_set():
        try:
            current_ids = get_json(f"{HN_BASE_URL}/newstories.json")
            fresh_ids = [story_id for story_id in current_ids if story_id not in known_ids]

            if not fresh_ids:
                print("No new stories yet.")
            else:
                for story_id in reversed(fresh_ids):
                    story = get_json(f"{HN_BASE_URL}/item/{story_id}.json")
                    known_ids.add(story_id)

                    if story and story.get("type") == "story" and story.get("title"):
                        event_queue.put(story)
                        print(f"Queued: {story['title']}")

        except requests.RequestException as error:
            print(f"Hacker News API request failed: {error}")

        stop_event.wait(POLL_SECONDS)


def process_story(story: dict):
    story_id = story["id"]

    with psycopg.connect(DATABASE_URL) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT 1 FROM enriched_stories WHERE story_id = %s",
                (story_id,),
            )
            if cursor.fetchone():
                print(f"Already stored: {story_id}")
                return

    classification = classify_title(story["title"])
    story_created_at = datetime.fromtimestamp(story["time"], tz=timezone.utc)

    with psycopg.connect(DATABASE_URL) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO enriched_stories (
                    story_id, title, url, author, score,
                    story_created_at, raw_payload, topic, model_name
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (story_id) DO NOTHING
                """,
                (
                    story_id,
                    story["title"],
                    story.get("url"),
                    story.get("by"),
                    story.get("score", 0),
                    story_created_at,
                    Jsonb(story),
                    classification["topic"],
                    MODEL_NAME,
                ),
            )

    print(f"Saved [{classification['topic']}]: {story['title']}")


def main():
    producer = threading.Thread(target=produce_events, daemon=True)
    producer.start()

    try:
        while True:
            try:
                story = event_queue.get(timeout=1)
            except Empty:
                continue

            try:
                process_story(story)
            finally:
                event_queue.task_done()

    except KeyboardInterrupt:
        print("\nStopping the stream...")

    finally:
        stop_event.set()
        producer.join(timeout=2)


if __name__ == "__main__":
    main()