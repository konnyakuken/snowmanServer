from fastapi import FastAPI, Request, Depends

from sqlalchemy.ext.asyncio import AsyncSession

from api.routers import crud
from api.db import get_db

import api.schemas as Photo_schema


from linebot import WebhookParser
from linebot.models import TextMessage
from aiolinebot import AioLineBotApi

import os
from dotenv import load_dotenv

from typing import List, Tuple

# .envファイルの内容を読み込見込む
load_dotenv()

accessToken= os.environ["CHANNEL_ACCESS_TOKEN"] # 環境変数の値をAPに代入
secretToken= os.environ["CHANNEL_SECRET"]
#各インスタンスの生成
line_bot_api = AioLineBotApi(accessToken)
handler = WebhookParser(secretToken)

app = FastAPI()

@app.get("/")
async def hello():
    return {"message" : "Hello,World"}

#DB追加
@app.post('/photo',response_model=Photo_schema.CreatePhoto)
async def save_Photo(
    photo_body: Photo_schema.ItemBase, db: AsyncSession = Depends(get_db)):
    return await crud.create_photo(db, photo_body)
    #create_article(db, article)

#全権取得
@app.get("/photo", response_model=List[Photo_schema.CreatePhoto])
async def list_photos(db: AsyncSession = Depends(get_db)):
    return await crud.get_photo(db)

@app.get("/check/{photo_id}")
async def get_photo(photo_id: int,db: AsyncSession = Depends(get_db)):
    return await crud.check_task(db,photo_id)

#lineApi
@app.post("/callback")
async def handle_request(request: Request,db: AsyncSession = Depends(get_db)):
    # リクエストをパースしてイベントを取得（署名の検証あり）
    events = handler.parse(
        (await request.body()).decode("utf-8"),
        request.headers.get("X-Line-Signature", ""))
    
    # 各イベントを処理
    for ev in events:
        #もしチャットが整数ならDB検索
        if (ev.message.text).isdecimal() == True:
            reply_text= await crud.check_task(db,ev.message.text)
            if reply_text == "None":
                reply_text = "この数字は見つからなかったよ"
        else:
            reply_text="数字を入力してね！"
        await line_bot_api.reply_message_async(
            ev.reply_token,
            TextMessage(text=f"{reply_text}"))
    # LINEサーバへHTTP応答を返す
    return "ok"