"""Configuration for Style Agent"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Paths
BASE_DIR = Path(__file__).parent
SAMPLES_DIR = BASE_DIR / "samples"
STYLE_PROFILE_DIR = BASE_DIR / "profiles"

# Create directories if they don't exist
SAMPLES_DIR.mkdir(exist_ok=True)
STYLE_PROFILE_DIR.mkdir(exist_ok=True)

# API Keys
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# LLM Settings
DEFAULT_MODEL = "claude-sonnet-4-20250514"  # or "gpt-4" for OpenAI
MAX_TOKENS = 4096
TEMPERATURE = 0.7
