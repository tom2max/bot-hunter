CREATE TABLE IF NOT EXISTS profil_social (
    id UUID PRIMARY KEY,
    username VARCHAR(100),
    nb_followers INTEGER,
    date_creation DATE,
    is_verified BOOLEAN,
    source VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS publication (
    id UUID PRIMARY KEY,
    profil_id UUID REFERENCES profil_social(id),
    contenu TEXT,
    timestamp TIMESTAMP,
    likes INTEGER,
    retweets INTEGER
);

CREATE TABLE IF NOT EXISTS rapport_analyse (
    id UUID PRIMARY KEY,
    profil_id UUID REFERENCES profil_social(id),
    score_freq FLOAT,
    score_sem FLOAT,
    score_global FLOAT,
    label VARCHAR(10) CHECK (label IN ('BOT','SUSPECT','HUMAIN')),
    date_analyse TIMESTAMP DEFAULT NOW()
);
