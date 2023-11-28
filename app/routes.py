from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi import UploadFile
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import aiofiles
import ujson
import os

from app import auth, models, schemas, security, functions
from app.db import get_db
from app.models import User
from chatbot.functions import generate_responses, generate_openai_from_response


router = APIRouter()


@router.post("/register/", response_model=schemas.UserInDBBase)
async def register(user_in: schemas.UserIn, db: Session = Depends(get_db)):
    db_user = auth.get_user(db, username=user_in.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    db_user = db.query(models.User).filter(models.User.email == user_in.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = security.get_password_hash(user_in.password)
    db_user = models.User(
        **user_in.dict(exclude={"password"}), hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user




@router.post("/token", response_model=schemas.Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    user = auth.get_user(db, username=form_data.username)
    if not user or not security.pwd_context.verify(
        form_data.password, user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/uploadbook/")
async def create_upload_file(file: UploadFile | None = None, subject: str):
    if not file:
        return {"message": "No upload file sent"}
    else:
        book_content = await file.read()
        # TODO add code to save it in sql table
        return {"filename": file.filename}


@router.post("/conversation/")
async def read_conversation(
    query: str,
   
    db: Session = Depends(get_db),
):
    # TODO Add subject/model checking and redirection

    response = generate_responses(query=query)
    return generate_openai_from_response(response)

router.post("/passage_similarity_search/")
async def read_conversation(
    query: str,
    db: Session = Depends(get_db),
):
    # TODO Add subject/model checking and redirection

    response = generate_responses(query=query)
    return generate_openai_from_response(response)