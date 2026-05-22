from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import psycopg2, os, uuid, httpx
from dotenv import load_dotenv

load_dotenv()
app = FastAPI(title="Score Engine")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

ALPHA = 0.45
BETA  = 0.55

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

def classifier(score: float) -> str:
    if score >= 0.6:
        return "BOT"
    elif score >= 0.4:
        return "SUSPECT"
    else:
        return "HUMAIN"

@app.get("/analyser/{profil_id}")
def analyser(profil_id: str):
    profil_uuid = to_uuid(profil_id)
    try:
        r_freq = httpx.get(f"http://localhost:8003/analyser/{profil_id}", timeout=10)
        r_sem  = httpx.get(f"http://localhost:8004/analyser/{profil_id}", timeout=10)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Analyseur inaccessible: {e}")

    freq = r_freq.json()
    sem  = r_sem.json()

    if "error" in freq or "error" in sem:
        raise HTTPException(status_code=404, detail="Données insuffisantes")

    score_freq   = freq["score_frequence"]
    score_sem    = sem["score_semantique"]
    score_global = round(ALPHA * score_freq + BETA * score_sem, 3)
    label        = classifier(score_global)

    conn = get_db()
    cur  = conn.cursor()
    rapport_id = str(uuid.uuid4())
    cur.execute("""
        INSERT INTO rapport_analyse (id, profil_id, score_freq, score_sem, score_global, label)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (rapport_id, profil_uuid, score_freq, score_sem, score_global, label))
    conn.commit()
    cur.close()
    conn.close()

    return {
        "profil_id": profil_uuid,
        "score_frequence": score_freq,
        "score_semantique": score_sem,
        "score_global": score_global,
        "label": label,
        "preuves": {
            "cadence_minutes": freq.get("cadence_moyenne_minutes"),
            "ratio_pics": freq.get("ratio_pics"),
            "repetition_rate": sem.get("repetition_rate"),
            "llm_probability": sem.get("llm_probability")
        }
    }

@app.get("/historique")
def historique():
    conn = get_db()
    cur  = conn.cursor()
    cur.execute("""
        SELECT profil_id, score_freq, score_sem, score_global, label, date_analyse
        FROM rapport_analyse ORDER BY date_analyse DESC LIMIT 20
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [{"profil_id": str(r[0]), "score_freq": r[1], "score_sem": r[2],
             "score_global": r[3], "label": r[4], "date_analyse": str(r[5])} for r in rows]

@app.get("/")
def root():
    return {"message": "Score Engine opérationnel"}
