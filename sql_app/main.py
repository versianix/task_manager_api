from typing import Annotated
from datetime import timedelta, datetime

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from passlib.context import CryptContext
from . import crud, models, schemas
from .database import SessionLocal, engine


SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
models.Base.metadata.create_all(bind=engine)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI()


## Dependency

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



## JWT Security

# Compares the inputed password with the hashed password
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


# Hashes the string (password)
def get_password_hash(password):
    return pwd_context.hash(password)


# Gets the user from the database and returns it's hashed password
def get_user_hashed(db, username: str):
    if db.query(models.User).filter(models.User.username == username).first():
        user_dict = db.query(models.User).filter(models.User.username == username).first().__dict__
        print(user_dict)
        return schemas.UserInDB(**user_dict)


# Authenticates the user by comparing the inputed password with the hashed password
def authenticate_user(db, username: str, password: str):
    user = get_user_hashed(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


# Creates the access token
def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# Gets the current user from the token
def get_current_user(token: Annotated[str, Depends(oauth2_scheme)],
                           db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = schemas.TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user_hashed(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


# Gets the current active user
def get_current_active_user(
    current_user: Annotated[schemas.User, Depends(get_current_user)]
):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user



## Endpoints

# Login endpoint (Creates token)
@app.post("/token", response_model=schemas.Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db)
):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


# Read the current user's items (Needs token)
@app.get("/users/me/items/")
async def read_own_items(
    current_user: Annotated[schemas.User, Depends(get_current_active_user)],
    db: Session = Depends(get_db)
):
    return crud.get_user_items(db, current_user.id)


# Create a new user (Doesn't need token)
@app.post("/users/", response_model=schemas.User)
async def create_user(
    user: schemas.UserCreate, db: Session = Depends(get_db)
):
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered. Plase use a different one.")
    return crud.create_user(db=db, user=user)


# Create a new item for current user (Needs token)
@app.post("/users/{user_id}/items/", response_model=schemas.Item)
async def create_item_for_user(
    current_user: Annotated[schemas.User, Depends(get_current_active_user)],
    item: schemas.ItemCreate, db: Session = Depends(get_db)
):
    return crud.create_user_item(db=db, item=item, user_id=current_user.id)


# Delete a item for current user (Needs token)
@app.delete("/users/{user_id}/items/delete", response_model=schemas.Item)
async def delete_user_item(
    current_user: Annotated[schemas.User, Depends(get_current_active_user)], item_id: str, db: Session = Depends(get_db)
):
    return crud.delete_user_item(db=db, user_id=current_user.id, item_id=item_id)


# Finishes the unfinished task (Needs token)
@app.put("/users/{user_id}/items/finish", response_model=schemas.Item)
async def finish_user_item(
    current_user: Annotated[schemas.User, Depends(get_current_active_user)],
    item_id: int, db: Session = Depends(get_db)
):
    return crud.finish_user_item(db=db, user_id=current_user.id, item_id=item_id)


# List all items in the database (Needs token)
@app.get("/items/", response_model=list[schemas.Item])
async def read_all_items(
    current_user: Annotated[schemas.User, Depends(get_current_active_user)],
    db: Session = Depends(get_db)
):
    items = crud.read_all_items(db)
    return items