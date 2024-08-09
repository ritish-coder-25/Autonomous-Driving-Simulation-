import socketio
import eventlet
import numpy as np
from flask import Flask
from keras.models import load_model
import base64
from io import BytesIO
from PIL import Image
import cv2

sio = socketio.Server()

app = Flask(__name__)
speed_limit = 30

def img_preprocess(img):
    print("Original image shape:", img.shape)
    img = img[60:135, :, :]
    print("After cropping:", img.shape)
    img = cv2.cvtColor(img, cv2.COLOR_RGB2YUV)
    img = cv2.GaussianBlur(img, (3, 3), 0)
    img = cv2.resize(img, (200, 66))
    img = img / 255
    print("Final preprocessed image shape:", img.shape)
    return img

@sio.on('telemetry')
def telemetry(sid, data):
    print("Telemetry data received")
    speed = float(data['speed'])
    image = Image.open(BytesIO(base64.b64decode(data['image'])))
    image = np.asarray(image)
    image = img_preprocess(image)
    image = np.array([image])
    steering_angle = float(model.predict(image))
    print("Predicted steering angle:", steering_angle)
    throttle = 1.0 - speed/speed_limit
    print('{} {} {}'.format(steering_angle, throttle, speed))
    send_control(steering_angle, throttle)

@sio.on('connect')
def connect(sid, environ):
    print('Connected to simulator')
    send_control(0, 0)

def send_control(steering_angle, throttle):
    print(f'Sending control: steering_angle={steering_angle}, throttle={throttle}')
    sio.emit('steer', data={
        'steering_angle': steering_angle.__str__(),
        'throttle': throttle.__str__()
    })

if __name__ == '__main__':
    model = load_model('model/model.h5')
    app = socketio.Middleware(sio, app)
    eventlet.wsgi.server(eventlet.listen(('', 4567)), app)
