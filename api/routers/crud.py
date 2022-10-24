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


def view_photo(upload_file: UploadFile = File(...)):
    path = f'./files/{upload_file.filename}'
    with open(path, 'w+b') as buffer:
        shutil.copyfileobj(upload_file.file, buffer)
    return {
        'filename': path,
        'type': upload_file.content_type
    }

async def get_photo(db: AsyncSession) -> List[Tuple[int, str]]:
    result = await (db.execute(select(photo_model.Photo.id,photo_model.Photo.title,)))
    return result.all()

async def check_task(db: AsyncSession,photo_id) ->Tuple[int, str]:
    #selectで渡す範囲を選択
    result = await (db.execute(select(photo_model.Photo.title,).filter(photo_model.Photo.id == photo_id)))
    #print(type(result))
    #空ではない時、intへ変換
    for row in result:
        result = str(row[0])

    if isinstance(result,str) == True:
        print(type(result))
        return result
    else:
        return "None"
    