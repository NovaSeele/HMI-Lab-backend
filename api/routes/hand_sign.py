from typing import List
import os
import cv2
import numpy as np

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Request, Query, WebSocket, WebSocketDisconnect
from fastapi.security import OAuth2PasswordRequestForm


from dependency.hand_sign import open_camera

router = APIRouter()

@router.websocket("/ws/open-camera")
async def websocket_open_camera(websocket: WebSocket):
    await websocket.accept()
    try:
        async for detected_characters in open_camera():
            await websocket.send_text(detected_characters)
    except WebSocketDisconnect:
        print("Client disconnected")

@router.get("/test")
async def test():
    return {"message": "Hello, World!"}




