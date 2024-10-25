from pydantic import BaseModel
from typing import Optional, List


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class User(BaseModel):
    username: str
    email: str
    full_name: Optional[str] = None


class UserUpdateAvatar(User):
    avatar: Optional[str] = None    


class UserCreate(BaseModel):
    username: str
    email: str
    full_name: Optional[str] = None
    password: str

class UserInDB(User):
    password: str
    hashed_password: str
    avatar: Optional[str] = None
    history_hand_sign: Optional[List[str]] = []


class UserHistoryHandSign(BaseModel):
    hand_sign_text: str

class UserChangePassword(BaseModel):
    old_password: str
    new_password: str

# New model for response without password fields
class UserPublic(BaseModel):
    username: str
    email: str
    full_name: Optional[str] = None
    avatar: Optional[str] = None
    history_hand_sign: Optional[List[str]] = []




