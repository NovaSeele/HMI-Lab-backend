from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from fastapi.security import OAuth2PasswordRequestForm

import cloudinary
import cloudinary.uploader

from dependency.user import get_password_hash, create_access_token, verify_password
from models.user import authenticate_user, get_current_user, get_user_collection
from schemas.user import User, UserInDB, Token, UserCreate, UserUpdateAvatar, UserChangePassword, UserPublic

router = APIRouter()

# Configuration       
cloudinary.config( 
    cloud_name = "dxovnpypb", 
    api_key = "163478744136852", 
    api_secret = "sjuU6l-A4wTGCHxwcYZ5HecB0xg", # Click 'View API Keys' above to copy your API secret
    secure=True
) 

UPLOAD_DIR = "public/avatars/"

@router.post("/upload-avatar", response_model=UserUpdateAvatar)
async def upload_avatar(avatar: UploadFile = File(...), current_user: UserInDB = Depends(get_current_user)):
    user_collection = await get_user_collection()

    # Upload the avatar file to Cloudinary
    upload_result = cloudinary.uploader.upload(avatar.file, public_id=f"{current_user.username}_avatar")

    # Get the URL of the uploaded avatar
    avatar_url = upload_result.get("secure_url")

    # Update user's avatar URL in the database
    await user_collection.update_one(
        {"username": current_user.username}, {"$set": {"avatar": avatar_url}}
    )

    # Fetch updated user details
    updated_user = await user_collection.find_one({"username": current_user.username})

    return updated_user


# Register a new user
@router.post("/register", response_model=UserCreate)
async def register_user(user: UserCreate):
    
    user_collection = await get_user_collection()
    
    # Check if the user already existed by username or email
    existing_user = await user_collection.find_one(
        {"$or": [{"username": user.username}, {"email": user.email}]})
    if existing_user:
        raise HTTPException(
            status_code=400, detail="Username already registered")
        
    hashed_password = get_password_hash(user.password)  # Use the password field
    user_dict = user.model_dump()
    user_dict['hashed_password'] = hashed_password
    
    # Insert the user into the database
    result = await user_collection.insert_one(user_dict)
    
    if result.inserted_id:
        return user
    raise HTTPException(status_code=400, detail="Registration failed")
    

# Login and get an access token
@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    # Attempt to authenticate user by username or email
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username, email, or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


# Get the current user
@router.get("/users/me", response_model=UserPublic)
async def read_users_me(current_user: UserInDB = Depends(get_current_user)):
    # Create a UserPublic instance from the current_user
    user_public = UserPublic(
        username=current_user.username,
        email=current_user.email,
        full_name=current_user.full_name,
        avatar=current_user.avatar,
        history_hand_sign=current_user.history_hand_sign
    )
    return user_public


# Change the user's password
@router.put("/change-password", response_model=UserInDB)
async def change_password(
    user: UserChangePassword,
    current_user: UserInDB = Depends(get_current_user)
):
    user_collection = await get_user_collection()

    # If new password is the same as the old password
    if user.old_password == user.new_password:
        raise HTTPException(
            status_code=400, detail="New password cannot be the same as the old password")

    # Check if the old password is correct
    if not user.old_password == current_user.password:
        raise HTTPException(
            status_code=400, detail="Old password is incorrect")

    # Generate new hashed password
    new_hashed_password = get_password_hash(user.new_password)

    # Cập nhật mật khẩu trong cơ sở dữ liệu
    await user_collection.update_one(
        {"username": current_user.username},
        {"$set": {
            "hashed_password": new_hashed_password,
            "password": user.new_password
        }}
    )

    # Fetch updated user information
    updated_user = await user_collection.find_one({"username": current_user.username})

    return updated_user


@router.post("/history-hand-sign", response_model=UserInDB)
async def history_hand_sign(hand_sign_text: str = Query(...), current_user: UserInDB = Depends(get_current_user)):
    user_collection = await get_user_collection()
    
    # Fetch the current user's data
    user_data = await user_collection.find_one({"username": current_user.username})
    
    # Check if the hand sign text already exists in the user's history
    if hand_sign_text in user_data.get("history_hand_sign", []):
        raise HTTPException(
            status_code=400,
            detail="Hand sign text already exists in history."
        )
    
    # Push the new hand sign text into the user's history_hand_sign list
    await user_collection.update_one(
        {"username": current_user.username},
        {"$push": {"history_hand_sign": hand_sign_text}}
    )
    
    # Fetch updated user information
    updated_user = await user_collection.find_one({"username": current_user.username})
    
    return updated_user


@router.delete("/history-hand-sign", response_model=UserInDB)
async def delete_hand_sign(hand_sign_text: str = Query(...), current_user: UserInDB = Depends(get_current_user)):
    user_collection = await get_user_collection()
    
    # Remove the specified hand sign text from the user's history_hand_sign list
    await user_collection.update_one(
        {"username": current_user.username},
        {"$pull": {"history_hand_sign": hand_sign_text}}
    )
    
    # Fetch updated user information
    updated_user = await user_collection.find_one({"username": current_user.username})
    
    return updated_user




