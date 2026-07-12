from dotenv import load_dotenv
import sqlite3
import os
import requests

load_dotenv()
RIOT_API_KEY = os.getenv("RIOT_API_KEY")
REGION = "na1"
DB_NAME = "matches.db"
def initialize_database():
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor

        cur.execute("""
            CREATE TABLE IF NOT EXISTS matches (
                    match_id TEXT PRIMARY KEY,
                    blue1 INTEGER,
                    blue2 INTEGER,
                    blue3 INTEGER,
                    blue4 INTEGER,
                    blue5 INTEGER,
                    red1 INTEGER,
                    red2 INTEGER,
                    red3 INTEGER,
                    red4 INTEGER,
                    red5 INTEGER,
                    blueW INTEGER
                )
        """)

        conn.commit()

def get_puuids():
    url = f"https://{REGION}.api.riotgames.com/lol/league/v4/challengerleagues/by-queue/RANKED_SOLO_5x5?api_key={RIOT_API_KEY}"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()['entries']
            
        for entry in data:
            puuids = entry["puuid"]
        print(len(puuids))
        return puuids
    else:
        print(response.status_code)
        print("Something went wrong")
        return []

def get_matches(puuid):
    url = f"https://americas.api.riotgames.com/lol/match/v5/matches/by-puuid/X5hQ2to4Fq-YvIbDNlfMumDu2BvJ13U1c3o5TzIjQv8qb__p4Ixea0UG68aBmIIStp2c8QAAJPx-bQ/ids?api_key={RIOT_API_KEY}"
    response = requests.get(url)

    print(response.status_code)
    print(response.json())
    if response.status_code == 200:
        return response.json()

#NA1_5599872514
# info -> participants -> players


def get_match_data(match_id):
    url = f"https://americas.api.riotgames.com/lol/match/v5/matches/{match_id}?api_key={RIOT_API_KEY}"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        participants = data["info"]["participants"]
        teams = data["info"]["teams"]

        blue = []
        red = []
        for player in participants:
            champ = player["championId"]
            if player["teamId"] == 100:
                blue.append(champ)
            else:
                red.append(champ)
        
        for team in teams:
            if team[0]["teamId"] == 100:
                if team["win"] == True:
                    blue_won = 1
                else:
                    blue_won = 0

        with sqlite3.connect(DB_NAME) as conn:
            cur = conn.cursor()

            cur.execute("""INSERT OR IGNORE INTO matches (
                        match_id,
                        blue1, blue2, blue3, blue4, blue5,
                        red1, red2, red3, red4, red5,
                        blueW
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (
                            match_id,
                            *blue,
                            *red,
                            blue_won
                        ))
                
    else:
        print(response.status_code)
        print("som,ething went wrong")


#to do: complete and test



