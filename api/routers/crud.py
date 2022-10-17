#from sqlalchemy.orm.session import Session
from sqlalchemy.ext.asyncio import AsyncSession

import api.schemas as photo_schema
import api.models.photo as photo_model





async def create_photo(
    db: AsyncSession, photo_create: photo_schema.CreatePhoto
) -> photo_model.Photo:
    photo =  photo_model.Photo(**photo_create.dict())
    db.add(photo)
    await db.commit()
    await db.refresh(photo)
    return photo