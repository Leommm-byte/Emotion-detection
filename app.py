import cv2
import numpy as np
import tensorflow as tf
import asyncio
import websockets
import json, io
import os

face_classifier = cv2.CascadeClassifier(r'haarcascade_frontalface_default.xml')

# Load TFLite model and allocate tensors
interpreter = tf.lite.Interpreter(model_path="model.tflite")
interpreter.allocate_tensors()

emotion_labels = ['Angry','Disgust','Fear','Happy','Neutral', 'Sad', 'Surprise']

# Get input and output tensors
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

async def websocket_handler(websocket, path):
    try:
        async for message in websocket:
            response = recognize_face(message)
            await websocket.send(json.dumps(response))
    except Exception as e:
        print(f"WebSocket Error: {str(e)}")

def recognize_face(message):
    try:
        frame = cv2.imdecode(np.frombuffer(message, np.uint8), -1)
        labels = []
        gray = cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
        faces = face_classifier.detectMultiScale(gray)

        for (x,y,w,h) in faces:
            roi_gray = gray[y:y+h,x:x+w]
            roi_gray = cv2.resize(roi_gray,(48,48),interpolation=cv2.INTER_AREA)

            if np.sum([roi_gray])!=0:
                roi = roi_gray.astype('float')/255.0
                roi = np.expand_dims(roi, axis=0)
                roi = np.expand_dims(roi, axis=-1)  # Add an extra dimension for the grayscale channel

                # Point the data to be used for testing and run the interpreter
                interpreter.set_tensor(input_details[0]['index'], roi.astype(np.float32))
                interpreter.invoke()

                # Obtain results and map them to the classes
                predictions = interpreter.get_tensor(output_details[0]['index'])
                label = emotion_labels[predictions.argmax()]
                return {"status": True, "message": label}
            else:
                return {"status": False, "message": "No Face Detected"}
    except Exception as e:
        return {"status": False, "message": str(e)}

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(
        websockets.serve(websocket_handler, "0.0.0.0", os.environ.get("PORT", 5000), max_size=10**7)
    )
    loop.run_forever()