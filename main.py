from fastapi import FastAPI
from routers import sauna_ranking

app = FastAPI()

# サウナランキング関連のルーターを登録
app.include_router(sauna_ranking.router) 