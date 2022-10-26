#from sqlalchemy.orm.session import Session
from tokenize import String
from sqlalchemy.ext.asyncio import AsyncSession

import api.schemas as photo_schema
import api.models.photo as photo_model

from typing import List, Tuple
from sqlalchemy import select
from sqlalchemy.engine import Result

from sqlalchemy.exc import NoResultFound

from fastapi import FastAPI, Request, Depends,File,UploadFile
import shutil
import os

async def create_photo(
    db: AsyncSession, photo_create: photo_schema.CreatePhoto
) -> photo_model.Photo:
    photo =  photo_model.Photo(**photo_create.dict())
    db.add(photo)
    await db.commit()
    await db.refresh(photo)
    return photo


async def save_URL(data:str,db: AsyncSession):

    photo =  photo_model.Photo(URL=data)
    db.add(photo)
    await db.commit()
    await db.refresh(photo)
    return photo.id

def view_photo(upload_file: UploadFile = File(...)):
    path = f'./files/{upload_file.filename}'
    with open(path, 'w+b') as buffer:
        shutil.copyfileobj(upload_file.file, buffer)
    return {
        'filename': path,
        'type': upload_file.content_type
    }

def file_count():
    dir = './files'
    count_file = 0
    #ディレクトリの中身分ループする
    for file_name in os.listdir(dir):
        #ファイルもしくはディレクトリのパスを取得
        file_path = os.path.join(dir,file_name)
        #ファイルであるか判定
        if os.path.isfile(file_path):
            count_file +=1
    return int(count_file)


async def get_photo(db: AsyncSession) -> List[Tuple[int, str]]:
    result = await (db.execute(select(photo_model.Photo.id,photo_model.Photo.URL,).order_by(photo_model.Photo.id.desc())))
    return result.all()

#カウント
async def count_photo(db: AsyncSession) -> List[Tuple[int, str]]:
    #降順で取得
    result = await (db.execute(select(photo_model.Photo.id,).order_by(photo_model.Photo.id.desc())))
    sum = result.first()
    if str(sum) != "None":
        sum = sum.id
        return sum
    else:
        return "0"

async def check_task(db: AsyncSession,photo_id) ->Tuple[int, str]:
    #selectで渡す範囲を選択
    result = await (db.execute(select(photo_model.Photo.URL,).filter(photo_model.Photo.id == photo_id)))
    #空ではない時、intへ変換
    for row in result:
        result = str(row[0])

    if isinstance(result,str) == True:
        return result
    else:
        return "None"
    