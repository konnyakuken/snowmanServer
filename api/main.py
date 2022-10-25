from ast import Str
from email.mime import image
import numbers
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

#写真保存
@app.post("/save/photo")
def list_photos(db: AsyncSession = Depends(get_db),upload_file: UploadFile = File(...)):
    return crud.view_photo(upload_file)

#バイナリ(Unity)での画像受け取り
@app.post("/Unity/save")
def create_file(file: bytes = File()):
    image = Image.open(io.BytesIO(file))
    number = crud.file_count()
    zero = 4 - len(str(number))
    saveName = zero*"0" + str(number) + ".png" 
    image.save((os.path.join("./files/", saveName)))
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
            #reply_text= await crud.check_task(db,ev.message.text)
            #if reply_text == "None":
            #    isText = True
            #    reply_text = "この数字は見つからなかったよ"
            number = int(ev.message.text)
            imgSum = crud.file_count() - 1
            if  number <= imgSum:
                main_image_path = f"files/{ev.message.text}.png"
                preview_image_path = f"files/{ev.message.text}.png"
                print(main_image_path)

                # 画像の送信
                image_message = ImageSendMessage(
                    original_content_url=f"https://16b1-27-127-169-37.jp.ngrok.io/{main_image_path}",
                    preview_image_url=f"https://16b1-27-127-169-37.jp.ngrok.io/{preview_image_path}",
                )
            else:
                isText = True
                reply_text = "この数字は見つからなかったよ"
            
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


