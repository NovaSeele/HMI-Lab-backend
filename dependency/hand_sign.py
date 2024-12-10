import pickle
import cv2
import mediapipe as mp
import numpy as np
from fastapi import UploadFile
from fastapi.responses import JSONResponse
import warnings
import json
import asyncio
# Suppress specific deprecation warnings from protobuf
warnings.filterwarnings("ignore", category=UserWarning, module='google.protobuf.symbol_database')

# Load the model
model_dict = pickle.load(open('models/model_tu.p', 'rb'))
model = model_dict['model']

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(static_image_mode=True, min_detection_confidence=0.3)

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
hands = mp_hands.Hands(static_image_mode=True, min_detection_confidence=0.3)

labels_dict = {0: 'A', 1: 'B', 2: 'C', 3: 'D', 4: 'E', 5: 'F', 6: 'G', 7: 'H', 8: 'I', 9: 'J', 10: 'K', 11: 'L', 12: 'M', 13: 'N', 14: 'O', 15: 'P', 16: 'Q', 17: 'R', 18: 'S', 19: 'T', 20: 'U', 21: 'V', 22: 'W', 23: 'X', 24: 'Y', 25: 'Z', 26: '1', 27: '2', 28: '3', 29: '4', 30: '5', 31: '6', 32: '7', 33: '8', 34: '9', 35: '0', 36: ' ', 37: 'delete'}

def process_frame(frame, hands, model, labels_dict):
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(frame_rgb)

    detected_characters = ""

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_drawing.draw_landmarks(
                frame, hand_landmarks, mp_hands.HAND_CONNECTIONS,
                mp_drawing_styles.get_default_hand_landmarks_style(),
                mp_drawing_styles.get_default_hand_connections_style()
            )

            data_aux = []
            x_ = []
            y_ = []

            for i in range(len(hand_landmarks.landmark)):
                x = hand_landmarks.landmark[i].x
                y = hand_landmarks.landmark[i].y
                x_.append(x)
                y_.append(y)

            for i in range(len(hand_landmarks.landmark)):
                x = hand_landmarks.landmark[i].x
                y = hand_landmarks.landmark[i].y
                data_aux.append(x - min(x_))
                data_aux.append(y - min(y_))

            prediction = model.predict([np.asarray(data_aux)])
            predicted_character = labels_dict[int(prediction[0])]

            # Check for space and delete commands
            if predicted_character == ' ':
                detected_characters += ' '  # Add space
            elif predicted_character == 'delete':
                detected_characters = detected_characters[:-1]  # Remove last character
            else:
                detected_characters += predicted_character  # Add other characters

            H, W, _ = frame.shape
            x1 = int(min(x_) * W) - 10
            y1 = int(min(y_) * H) - 10
            x2 = int(max(x_) * W) - 10
            y2 = int(max(y_) * H) - 10

            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 0), 4)
            cv2.putText(frame, predicted_character, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 1.3, (0, 0, 0), 3, cv2.LINE_AA)

    return detected_characters

async def open_camera():
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: Could not open camera")
        return
    
    detected_characters = ""
    last_character = None  # Track the last detected character
    recording = False  # To track whether recording is enabled

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Error: Could not read frame")
                break

            # Check for Tab key press (0x09 is the ASCII value for Tab)
            key = cv2.waitKey(1) & 0xFF
            if key == 0x09:  # If Tab key is pressed, toggle recording
                recording = not recording
                print(f"Recording {'enabled' if recording else 'disabled'}")

            if recording:
                # Apply the prediction logic
                current_characters = process_frame(frame, hands, model, labels_dict)

                # Add characters to detected_characters only if they are different from the last one
                for char in current_characters:
                    if char != last_character:
                        detected_characters += char
                        last_character = char
                        yield detected_characters

            # Display the instruction text on the frame
            cv2.putText(frame, "Press Q to turn off the camera", (10, 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)
            cv2.putText(frame, "Press Tab to start/stop recording", (10, 60), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)

            cv2.imshow('Camera Test', frame)

            if key == ord('q'):  # Quit if Q is pressed
                yield "camera_closed"  # Send a message indicating the camera is closed
                break

            # Add a small sleep to prevent blocking
            await asyncio.sleep(0.01)
            
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        cap.release()
        cv2.destroyAllWindows()
