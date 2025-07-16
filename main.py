import asyncio
from datetime import datetime
import sqlite3
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

sentiments = {
    'positive': ['хорош', 'люблю'],
    'negative': ['плохо', 'ненавиж']
}

async def create_db():
    """
    Запрос на создание таблицы(будет выполняться каждый раз при запуске приложения)
    """
    conn = sqlite3.connect('mydatabase.db')
    cursor = conn.cursor()
    stmt =("CREATE TABLE IF NOT EXISTS reviews ("
                         "id INTEGER PRIMARY KEY AUTOINCREMENT,"
                         " text TEXT NOT NULL,"
                         " sentiment TEXT NOT NULL,"
                         " created_at TEXT NOT NUL"
                         "L);")
    cursor.execute(stmt)
    conn.commit()
    conn.close()

async def save_sentiment_in_db(sentiment: str, created_at: str, text: str):
    """
    Запрос на сохранение отзыва(Выполняется при POST-запросе
    """
    conn = sqlite3.connect('mydatabase.db')
    cursor = conn.cursor()
    stmt = (f"INSERT INTO reviews (text, sentiment, created_at)"
            f' VALUES ("{text}", "{sentiment}", "{created_at}")'
            f'RETURNING id, text, sentiment, created_at')
    value = cursor.execute(stmt)
    res = value.fetchone()
    conn.commit()
    conn.close()
    return res


async def get_reviews_by_filter(sentiment: str):
    """
    Запрос на получение отзывов по фильтру(выполняется при GET-запросе
    """
    conn = sqlite3.connect('mydatabase.db')
    cursor = conn.cursor()
    stmt = (f'SELECT id, text, sentiment, created_at'
            f' FROM reviews'
            f' WHERE sentiment="{sentiment}"')
    res = cursor.execute(stmt)
    result = res.fetchall()
    conn.close()
    return result

class Review(BaseModel):
    """
    Pydantic модель для сохранения отзыва
    """
    text: str

class ResponseModel(Review):
    """
    Pydantic модель для получения сохраненного отзыва
    """
    id: int
    sentiment: str
    created_at: str



app = FastAPI(on_startup=asyncio.run(create_db()))

@app.post('/reviews')
async def post_review(review: Review) -> ResponseModel:
    sentiment = 'neutral'
    for value in sentiments['positive']:
        if value in review.text:
            sentiment = 'positive'
            break
    else:
        for value in  sentiments['negative']:
            if value in review.text:
                sentiment = 'negative'
                break
    created_at = datetime.now().isoformat()
    res_tuple = await save_sentiment_in_db(sentiment, created_at, review.text)
    res = ResponseModel(**dict(zip(['id', 'text', 'sentiment', 'created_at'], res_tuple)))
    return res


@app.get('/reviews')
async def get_reviews(sentiment: str = 'negative'):
    if not sentiment in ('positive', 'negative', 'neutral'):
        raise HTTPException(status_code=404, detail='Not Found')
    res = await get_reviews_by_filter(sentiment)
    return res


if __name__ == "__main__":
    uvicorn.run(app)