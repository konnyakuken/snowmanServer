from fastapi import FastAPI, Request

from linebot import WebhookParser
from linebot.models import TextMessage
from aiolinebot import AioLineBotApi

import os
from dotenv import load_dotenv

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

@app.post("/messaging_api/handle_request")
async def request():
    return "ok"

@app.post("/callback")
async def handle_request(request: Request):
    # リクエストをパースしてイベントを取得（署名の検証あり）
    events = handler.parse(
        (await request.body()).decode("utf-8"),
        request.headers.get("X-Line-Signature", ""))

    # 各イベントを処理
    for ev in events:
        await line_bot_api.reply_message_async(
            ev.reply_token,
            TextMessage(text=f"オウム返し: {ev.message.text}"))
    # LINEサーバへHTTP応答を返す
    return "ok"