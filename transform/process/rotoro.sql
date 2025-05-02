CREATE TABLE IF NOT EXISTS news_articles (
    id SERIAL PRIMARY KEY,
    link TEXT UNIQUE NOT NULL,
    content TEXT,
    published TIMESTAMP WITH TIME ZONE,
    sentiment VARCHAR(10),
    sentiment_score INT,
    summary TEXT,
    title TEXT,
    topic VARCHAR(100)
);
