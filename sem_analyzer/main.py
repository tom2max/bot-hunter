from fastapi import FastAPI
import psycopg2, os, uuid, spacy
from dotenv import load_dotenv
from collections import Counter

load_dotenv()
app = FastAPI(title="Sem Analyzer")
nlp = spacy.load("fr_core_news_sm")

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
def analyser_semantique(profil_id: str):
    profil_uuid = to_uuid(profil_id)
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT contenu FROM publication WHERE profil_id = %s", (profil_uuid,))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    if not rows:
        return {"error": "Aucune publication trouvée"}

    textes = [r[0] for r in rows]

    # 1. Taux de répétition (publications identiques)
    compteur = Counter(textes)
    nb_uniques = len(compteur)
    repetition_rate = 1.0 - (nb_uniques / max(len(textes), 1))

    # 2. Analyse NLP avec spaCy
    sentiments = []
    longueurs = []
    for texte in textes:
        doc = nlp(texte)
        longueurs.append(len(doc))
        # Indicateur simple : ratio de mots positifs/négatifs
        pos_count = sum(1 for t in doc if t.pos_ in ["NOUN", "VERB"])
        sentiments.append(pos_count / max(len(doc), 1))

    sentiment_moyen = round(sum(sentiments) / max(len(sentiments), 1), 3)
    longueur_moyenne = round(sum(longueurs) / max(len(longueurs), 1), 2)

    # 3. Probabilité LLM (textes très courts et répétitifs = signe de bot)
    llm_probability = round(min(repetition_rate * 0.6 + (1 - min(longueur_moyenne / 20, 1)) * 0.4, 1.0), 3)

    # 4. Score sémantique global
    score = round(min(repetition_rate * 0.5 + llm_probability * 0.5, 1.0), 3)

    return {
        "profil_id": profil_uuid,
        "nb_textes": len(textes),
        "nb_uniques": nb_uniques,
        "repetition_rate": round(repetition_rate, 3),
        "sentiment_moyen": sentiment_moyen,
        "longueur_moyenne_mots": longueur_moyenne,
        "llm_probability": llm_probability,
        "score_semantique": score
    }

@app.get("/")
def root():
    return {"message": "Sem Analyzer opérationnel"}
