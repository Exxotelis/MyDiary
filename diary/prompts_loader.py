# prompts_loader.py
import json
import random
from datetime import date
from django.conf import settings
import os

PROMPTS_PATH = os.path.join(settings.BASE_DIR, 'diary', 'data', 'prompts.json')


def get_daily_prompt():
    try:
        with open(PROMPTS_PATH, 'r', encoding='utf-8') as f:
            prompts = json.load(f)
        if not prompts:
            return None

        # Use date-based seed so the same prompt appears each day
        today = date.today().strftime("%Y%m%d")
        random.seed(int(today))
        return random.choice(prompts)
    except Exception as e:
        return None
