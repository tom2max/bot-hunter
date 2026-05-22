from fastapi import FastAPI
import psycopg2, os, uuid
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
app = FastAPI(title="Freq Analyzer")

def get_db():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )

def to_uuid(val: str) -> str:
    try:
        return str(uuid.UUID(val))
    except ValueError:
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, val))

@app.get("/analyser/{profil_id}")
def analyser_frequence(profil_id: str):
    profil_uuid = to_uuid(profil_id)
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT timestamp FROM publication
        WHERE profil_id = %s ORDER BY timestamp ASC
    """, (profil_uuid,))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    if not rows:
        return {"error": "Aucune publication trouvée"}

    df = pd.DataFrame(rows, columns=["timestamp"])
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp")

    deltas = df["timestamp"].diff().dropna()
    cadence_minutes = deltas.dt.total_seconds().mean() / 60
    pics = deltas[deltas.dt.total_seconds() < 600]
    nb_pics = len(pics)
    ratio_pics = nb_pics / max(len(deltas), 1)

    df["heure"] = df["timestamp"].dt.hour
    ratio_nuit = len(df[df["heure"].between(0, 6)]) / max(len(df), 1)

    score = 0.0
    if cadence_minutes < 10:
        score += 0.5
    elif cadence_minutes < 30:
        score += 0.3
    elif cadence_minutes < 60:
        score += 0.1
    score += ratio_pics * 0.3
    score += ratio_nuit * 0.2
    score = min(round(score, 3), 1.0)

    return {
        "profil_id": profil_uuid,
        "nb_publications": len(df),
        "cadence_moyenne_minutes": round(cadence_minutes, 2),
        "nb_pics": nb_pics,
        "ratio_pics": round(ratio_pics, 3),
        "ratio_nuit": round(ratio_nuit, 3),
        "score_frequence": score
    }

@app.get("/")
def root():
    return {"message": "Freq Analyzer opérationnel"}
