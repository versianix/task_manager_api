from pydantic import BaseModel


# Items

class ItemBase(BaseModel):
    title: str
    description: str | None = None


class ItemCreate(ItemBase):
    pass


class Item(ItemBase):
    title: str | None = None
    description: str | None = None

    class Config:
        orm_mode = True


# Users

class UserBase(BaseModel):
    username: str
    email: str


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int
    username: str
    email: str | None = None
    is_active: bool | None = None

    class Config:
        orm_mode = True


class UserInDB(User):
    hashed_password: str


# Tokens

class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None