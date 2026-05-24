from fastapi import FastAPI
from datetime import datetime, timedelta
import random

app = FastAPI(title="Mock API Sociale")

def generate_publications(profil_id: str, nb: int = 20):
    pubs = []
    base_time = datetime.now()
    for i in range(nb):
        pubs.append({
            "id": f"{profil_id}_pub_{i}",
            "contenu": f"Publication numéro {i} du profil {profil_id}",
            "timestamp": (base_time - timedelta(hours=i*2)).isoformat(),
            "likes": random.randint(0, 500),
            "retweets": random.randint(0, 100)
        })
    return pubs

@app.get("/")
def root():
    return {"message": "Mock API Sociale opérationnelle"}

@app.get("/profil/{profil_id}")
def get_profil(profil_id: str):
    return {
        "id": profil_id,
        "username": f"user_{profil_id}",
        "nb_followers": random.randint(100, 10000),
        "date_creation": "2022-01-15",
        "is_verified": False,
        "source": "mock",
        "publications": generate_publications(profil_id)
    }
