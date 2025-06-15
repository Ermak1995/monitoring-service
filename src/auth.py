import os
from datetime import datetime, timedelta

from dotenv import load_dotenv
from fastapi import HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.orm import Session

from models import User

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

# Для хеширования пароля
pwd_context = CryptContext(schemes=["bcrypt"])

# Получение токена
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


# Получение хеша пароля
def get_password_hash(password):
    return pwd_context.hash(password)


# Проверка пароля
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


# Аутентификация пользователя
def authenticate_user(db: Session, email: str, password: str):
    user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if user is None or not verify_password(password, User.password):
        return HTTPException(status_code=400, detail='Invalid user')
    return user


# Генерация токена
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# Получение текущего пользователя
def get_current_user(db: Session, token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
        return user
    except:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Не удалось проверить учетные данные",
            headers={"WWW-Authenticate": "Bearer"},
        )
