import base64
import json
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from starlette.requests import Request

from ._common import auth_basic, auth_bearer, get_user_db
from ..._shared import filesystem as fs
from ..._utils import json2dict, MAX_USERNAME_LEN
from ...davult import schemas, models
from ...davult.crud.user import UserDB


router = APIRouter()


@router.get('/create')
def user_create(user_db: Annotated[UserDB, Depends(get_user_db)], credentials: Annotated[tuple[str, str], Depends(auth_basic)]):
    username, password = credentials

    try:
        user = user_db.create_user(schemas.UserCreate(username=username, password=password))
    except ValueError:
        raise HTTPException(status_code=413, detail=f"username is too long (>{MAX_USERNAME_LEN})")
    except RuntimeError:
        raise HTTPException(status_code=409, detail="username already exists")
    fs.create_userspace(user.id)

    return {'error': {'valid': True}}


@router.get('/properties')
def user_properties(user: Annotated[models.User, Depends(auth_bearer)]):
    return {**json2dict(user.properties), 'valid': True, 'statusCode': 200}


@router.post('/properties/update')
async def user_properties_update(request: Request, user_db: Annotated[UserDB, Depends(get_user_db)], user: Annotated[models.User, Depends(auth_bearer)]):
    try:
        properties = json.JSONDecoder().decode((await request.body()).decode('utf-8'))
    except json.JSONDecodeError:
        raise HTTPException(status_code=422)

    user_db.update_user_properties(user, properties)


@router.get('/delete')
def user_delete(user_db: Annotated[UserDB, Depends(get_user_db)], user: Annotated[models.User, Depends(auth_bearer)]):
    user_db.delete_user(user)
    fs.delete_userspace(user.id)


@router.get('/rename')
def user_rename(user_db: Annotated[UserDB, Depends(get_user_db)], user: Annotated[models.User, Depends(auth_bearer)], newname: str):
    newname = base64.b64decode(newname).decode('utf-8')
    try:
        user_db.rename_user(user, newname)
    except ValueError:
        raise HTTPException(status_code=413, detail=f"username is too long (>{MAX_USERNAME_LEN})")


@router.get('/changepswd')
def user_changepswd(user_db: Annotated[UserDB, Depends(get_user_db)], credentials: Annotated[tuple[str, str], Depends(auth_basic)], new: str):
    new = base64.b64decode(new).decode('utf-8')
    username, password = credentials

    try:
        user = user_db.find_user(username)
    except LookupError:
        raise HTTPException(status_code=404)

    if not user_db.validate_credentials(user, password):
        raise HTTPException(status_code=403)

    user_db.set_user_password(user_db.find_user(username), new)
