import os
import sqlite3
import sys

def _get_bot_db_path():
    """Returns the absolute path to bot_control.db, working from any cwd."""
    # This file is at src/utils/bot_state.py → project root is 2 levels up
    here = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(here))
    return os.path.join(project_root, "chatbot", "bot_control.db")

def _get_bot_txt_path():
    """Returns the absolute path to current_step.txt."""
    here = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(here))
    return os.path.join(project_root, "chatbot", "current_step.txt")

def update_bot_state(step_name: str):
    """(Desactivado) Updates the user's active step/screen in both SQLite and a retro-compatible text file."""
    pass
