import wand.display
import cv2 as cv
import numpy as np
from wand.image import Image
from app.aws import move_to_s3
from app import app
import os

def save_thumbnail(imagename, frame_width, frame_height):
    '''
    save thumbnail image (aspect ratio preserved) to thumbnails/image_name

    params:
    image_name (str): file name of the image in ./images
    frame_width, frame_height (int): width and height of specified frame

    return:
    '''

    with wand.image.Image(filename=os.path.join(app.root_path, 'images/', imagename)) as img:
        img.strip()
        img.sample(int(img.width / 5), int(img.height / 5))
        img.transform(resize='{}x{}>'.format(frame_width, frame_height))

        key = 'thumbnails/' + imagename

        img.save(filename=os.path.join(app.root_path, key))
        move_to_s3(key)


def draw_face_rectangle(image_name):
    '''
    save face detected image to faces/image_name

    params:
    image_name (str): file name of the image in ./images

    return:
    bool: True if at least one face was detected
    '''

    face_cascade = cv.CascadeClassifier(os.path.join(app.root_path,'data/haarcascade_frontalface_default.xml'))
    img = cv.imread(os.path.join(app.root_path,'images/', image_name))
    gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)

    if len(faces) == 0:
        return False

    for (x, y, w, h) in faces:
        cv.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)

    key = 'faces/' + image_name
    cv.imwrite(os.path.join(app.root_path, key), img)
    move_to_s3(key)

    return True

# if __name__ == '__main__':
#     # example usage:
#     save_thumbnail('duck.png', 160, 120)
#     draw_face_rectangle('trump.jpg')
