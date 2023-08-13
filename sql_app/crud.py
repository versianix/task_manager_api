from sqlalchemy.orm import Session
from passlib.context import CryptContext
from . import models, schemas


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()


def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = pwd_context.hash(user.password)
    db_user = models.User(username=user.username, email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def create_user_item(db: Session, item: schemas.ItemCreate, user_id: int):
    db_item = models.Item(**item.model_dump(), owner_id=user_id)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


def get_user_items(db: Session, user_id: int):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    return user.items


def delete_user_item(db: Session, user_id: int, item_id: int):
    db.delete(db.query(models.Item).filter(models.Item.owner_id == user_id).filter(models.Item.id == item_id).first())
    db.commit()
    return 


def finish_user_item(db: Session, user_id: int, item_id: int):
    db_item = db.query(models.Item).filter(models.Item.owner_id == user_id).filter(models.Item.id == item_id).first()
    db_item.completed = True
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


def read_all_items(db: Session):
    return db.query(models.Item).all()