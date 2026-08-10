"""Pytest configuration: mock Streamlit and OpenAI so the app module imports cleanly."""
import sys
from unittest.mock import MagicMock

# Mock streamlit before any test imports the app
if "streamlit" not in sys.modules:
    sys.modules["streamlit"] = MagicMock()

# Mock openai before any test imports the app
if "openai" not in sys.modules:
    sys.modules["openai"] = MagicMock()