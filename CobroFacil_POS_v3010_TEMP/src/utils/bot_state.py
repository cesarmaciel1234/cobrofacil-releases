import os
import sqlite3
import sys

def _get_bot_db_path():
    """Returns the absolute path to bot_control.db, working from any cwd."""
    # This file is at src/utils/bot_state.py → project root is 2 levels up
    here = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(here))
    return os.path.join(project_root, "tests_e2e", "bot_control.db")

def _get_bot_txt_path():
    """Returns the absolute path to current_step.txt."""
    here = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(here))
    return os.path.join(project_root, "tests_e2e", "current_step.txt")

def update_bot_state(step_name: str):
    """Updates the user's active step/screen in both SQLite and a retro-compatible text file."""
    db_path = _get_bot_db_path()
    txt_path = _get_bot_txt_path()

    # 1. Update text file for retro-compatibility
    try:
        os.makedirs(os.path.dirname(txt_path), exist_ok=True)
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(step_name)
    except Exception as e:
        print(f"Error writing current_step.txt: {e}")

    # 2. Update the bot's private SQLite control database
    try:
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        conn = sqlite3.connect(db_path, timeout=5.0)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bot_state (
                key TEXT PRIMARY KEY,
                val TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            INSERT OR REPLACE INTO bot_state (key, val, updated_at)
            VALUES ('current_step', ?, CURRENT_TIMESTAMP)
        """, (step_name,))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error updating bot database state: {e}")
