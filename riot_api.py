from dotenv import load_dotenv
import sqlite3
import os
import requests

load_dotenv()
RIOT_API_KEY = os.getenv("RIOT_API_KEY")
REGION = "na1"

def get_puuids():
    url = f"https://{REGION}.api.riotgames.com/lol/league/v4/challengerleagues/by-queue/RANKED_SOLO_5x5?api_key={RIOT_API_KEY}"
    response = requests.get(url)

    if response.status_code == "200":
        data = response.json()
        for entry in data['entries']:
            print(entry["puuid"])
