import pandas as pd
import psycopg
import streamlit as st
from psycopg.rows import dict_row


DATABASE_URL = "dbname=hn_ai_stream"

st.set_page_config(
    page_title="Hacker News AI Stream",
    page_icon="📰",
    layout="wide",
)

st.title("Hacker News AI Stream")
st.caption("New stories are tagged by local Ollama and saved to PostgreSQL.")
st.info("Topic labels are model-generated guesses. Review them before drawing conclusions.")


@st.fragment(run_every="15s")
def render_live_dashboard():
    try:
        with psycopg.connect(DATABASE_URL, row_factory=dict_row) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        COUNT(*) AS story_count,
                        MAX(classified_at) AS latest_classification
                    FROM enriched_stories
                    """
                )
                summary = cursor.fetchone()

                cursor.execute(
                    """
                    SELECT topic, COUNT(*) AS story_count
                    FROM enriched_stories
                    GROUP BY topic
                    ORDER BY story_count DESC, topic
                    """
                )
                topic_rows = cursor.fetchall()

                cursor.execute(
                    """
                    SELECT title, topic, score, story_created_at
                    FROM enriched_stories
                    ORDER BY classified_at DESC
                    LIMIT 50
                    """
                )
                recent_rows = cursor.fetchall()

    except psycopg.Error as error:
        st.error(
            "Could not read the project database. "
            "Check that PostgreSQL is running and the table exists."
        )
        st.exception(error)
        return

    story_count = summary["story_count"]
    top_topic = topic_rows[0]["topic"] if topic_rows else "—"
    latest = summary["latest_classification"]
    latest_text = latest.strftime("%Y-%m-%d %H:%M:%S UTC") if latest else "—"

    metric_columns = st.columns(3)
    metric_columns[0].metric("Stories classified", f"{story_count:,}")
    metric_columns[1].metric("Most common topic", top_topic)
    metric_columns[2].metric("Latest classification", latest_text)

    chart_column, stories_column = st.columns([1, 2])

    with chart_column:
        st.subheader("Stories by topic")
        if topic_rows:
            topic_df = pd.DataFrame(topic_rows).set_index("topic")
            st.bar_chart(topic_df, y="story_count")
        else:
            st.info("No stories have been classified yet.")

    with stories_column:
        st.subheader("Latest stories")
        if recent_rows:
            recent_df = pd.DataFrame(recent_rows)
            st.dataframe(
                recent_df[
                    ["title", "topic", "score", "story_created_at"]
                ],
                hide_index=True,
                height=min(420, 42 + 38 * len(recent_df)),
            )
        else:
            st.info("Waiting for stories from the pipeline.")


render_live_dashboard()