from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx, psycopg2, os, uuid
from dotenv import load_dotenv

load_dotenv()
app = FastAPI(title="Profil Service")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

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

@app.get("/profil/{profil_id}")
def fetch_and_store(profil_id: str):
    try:
        r = httpx.get(f"http://localhost:8001/profil/{profil_id}", timeout=5)
        data = r.json()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Mock API inaccessible: {e}")

    conn = get_db()
    cur  = conn.cursor()
    profil_uuid = to_uuid(data["id"])

    cur.execute("""
        INSERT INTO profil_social (id, username, nb_followers, date_creation, is_verified, source)
        VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT (id) DO NOTHING
    """, (profil_uuid, data["username"], data["nb_followers"],
          data["date_creation"], data["is_verified"], data["source"]))

    for pub in data.get("publications", []):
        pub_uuid = to_uuid(pub["id"])
        cur.execute("""
            INSERT INTO publication (id, profil_id, contenu, timestamp, likes, retweets)
            VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT (id) DO NOTHING
        """, (pub_uuid, profil_uuid, pub["contenu"],
              pub["timestamp"], pub["likes"], pub["retweets"]))

    conn.commit()
    cur.close()
    conn.close()
    return {"message": "Profil sauvegardé", "profil_id": profil_uuid, "publications": len(data["publications"])}

@app.get("/")
def root():
    return {"message": "Profil Service opérationnel"}
