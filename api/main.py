from ast import Str
from email.mime import image
import numbers
from unittest import result
from fastapi import FastAPI, Request, Depends,File,UploadFile
import shutil
from sqlalchemy.ext.asyncio import AsyncSession
#別スクリプトのパス
from api.routers import crud
from api.db import get_db
import api.schemas as Photo_schema
#LineBot
from linebot import WebhookParser
from linebot.models import TextMessage,ImageSendMessage
from aiolinebot import AioLineBotApi
#.env
import os
from dotenv import load_dotenv

from typing import List, Tuple
#画像処理
import io
from PIL import Image
#pythonからhtmlに表示
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

import cloudinary
import cloudinary.uploader

import json

# .envファイルの内容を読み込見込む
load_dotenv()
accessToken= os.environ["CHANNEL_ACCESS_TOKEN"] # 環境変数の値をAPに代入
secretToken= os.environ["CHANNEL_SECRET"]
#各インスタンスの生成
line_bot_api = AioLineBotApi(accessToken)
handler = WebhookParser(secretToken)
templates = Jinja2Templates(directory='web')
app = FastAPI()

#静的ファイル（画像）を表示できるように設定
app.mount(
    '/files', 
    StaticFiles(directory="files"), 
    name='file'
)


cloudinary.config (
    cloud_name = os.environ['CLOUDINARY_NAME'],
    api_key = os.environ['CLOUDINARY_API_KEY'],
    api_secret = os.environ['CLOUDINARY_API_SECRET'],
)


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
@app.get("/all", response_model=List[Photo_schema.CreatePhoto])
async def get_uploadfile(db: AsyncSession = Depends(get_db)):
    return await crud.get_photo(db)

@app.get("/count")
async def photo_count(db: AsyncSession = Depends(get_db)):
    return await crud.count_photo(db)

#写真保存
@app.post("/save/photo")
def list_photos(upload_file: UploadFile = File(...)):
    return crud.view_photo(upload_file)

# bytes = File()とphoto_body: Photo_schema.ItemBaseを同時に宣言するとうまくいかない
#バイナリ(Unity)での画像受け取り
@app.post("/Unity/save")
async def create_file(file: bytes = File(),db: AsyncSession = Depends(get_db)):
    image = Image.open(io.BytesIO(file))
    number = await crud.count_photo(db)
    number = str(int(number)+1)
    zero = 4 - len(str(number))
    saveName = zero*"0" + str(number) + ".png" 
    image.save((os.path.join("./files/", saveName)))
    #cloudinaryへ送信
    res = cloudinary.uploader.upload(file = os.path.join("./files/", saveName),folder = "IVRC/", public_id=str(number))
    #DBへURLを保存
    number = await crud.save_URL(res["secure_url"],db)
    return (zero*"0" + str(number))


#画像の表示
@app.get("/photo/{id}", response_class=HTMLResponse)
def get_product(id: str, request: Request):
    filePath = '../files/' + id + '.png' 
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "filepath": filePath
        }
    )



#1件検索
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
    isText = False
    # 各イベントを処理
    for ev in events:
        #もしチャットが整数ならDB検索
        if (ev.message.text).isdecimal() == True:
            if len(str(ev.message.text)) == 4:
                result= await crud.check_task(db,ev.message.text)
                
                if  result != "None":
                    # 画像の送信
                    image_message = ImageSendMessage(
                        original_content_url=result,
                        preview_image_url=result,
                    )
                else:
                    isText = True
                    reply_text = "この数字は見つからなかったよ"
            else:
                isText = True
                reply_text="会場でもらった4桁の数字を入力してね！"
            
        else:
            isText = True
            reply_text="会場でもらった4桁の数字を入力してね！"

        if isText == True:
            await line_bot_api.reply_message_async(
                ev.reply_token,
                TextMessage(text=f"{reply_text}")
                )
        else:
            await line_bot_api.reply_message_async(
                ev.reply_token,
                [TextMessage(text=f"今日はきてくれてありがとう！！"),
                image_message]
                )
    # LINEサーバへHTTP応答を返す
    return "ok"


