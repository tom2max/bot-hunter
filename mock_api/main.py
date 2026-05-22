from fastapi import FastAPI
from datetime import datetime, timedelta
import random, uuid

app = FastAPI(title="Mock API Sociale")

def generer_publications(profil_id: str, nb: int, est_bot: bool):
    publications = []
    base_time = datetime.now()
    for i in range(nb):
        if est_bot:
            delta = timedelta(minutes=random.randint(1, 5))
            contenu = random.choice([
                "Achetez maintenant ! Offre limitée !",
                "Cliquez ici pour gagner un prix !",
                "Promotion exclusive, ne ratez pas !",
            ])
        else:
            delta = timedelta(hours=random.randint(2, 48))
            contenu = random.choice([
                "Belle journée aujourd'hui !",
                "Je viens de lire un livre intéressant.",
                "Qu'est-ce que vous pensez de cette actualité ?",
                "Photo de mon déjeuner 😄",
            ])
        publications.append({
            "id": str(uuid.uuid4()),
            "profil_id": profil_id,
            "contenu": contenu,
            "timestamp": (base_time - delta * i).isoformat(),
            "likes": random.randint(0, 5) if est_bot else random.randint(10, 500),
            "retweets": random.randint(0, 2) if est_bot else random.randint(1, 100),
        })
    return publications

@app.get("/profil/{profil_id}")
def get_profil(profil_id: str):
    est_bot = profil_id.startswith("bot")
    return {
        "id": profil_id,
        "username": f"user_{profil_id[:8]}",
        "nb_followers": random.randint(10, 50) if est_bot else random.randint(100, 10000),
        "date_creation": "2024-01-15" if est_bot else "2019-06-20",
        "is_verified": False if est_bot else random.choice([True, False]),
        "source": "twitter_mock",
        "publications": generer_publications(profil_id, 20, est_bot)
    }

@app.get("/")
def root():
    return {"message": "Mock API Sociale opérationnelle"}
