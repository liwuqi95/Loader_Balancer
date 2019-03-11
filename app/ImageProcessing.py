import wand.display
import cv2 as cv
import numpy as np
from wand.image import Image
from app.aws import upload_file_to_s3


def save_thumbnail(id, file, image_name, frame_width, frame_height):
    '''
    save thumbnail image (aspect ratio preserved) to thumbnails/image_name

    params:
    image_name (str): file name of the image in ./images
    frame_width, frame_height (int): width and height of specified frame

    return:
    '''

    with wand.image.Image(file=file) as img:
        img.strip()
        img.sample(int(img.width / 5), int(img.height / 5))
        img.transform(resize='{}x{}>'.format(frame_width, frame_height))
        img.save(filename='app/thumbnails/' + image_name)
        upload_file_to_s3(id, 'thumbnails', file, image_name)


def draw_face_rectangle(id, img, image_name):
    '''
    save face detected image to faces/image_name

    params:
    image_name (str): file name of the image in ./images

    return:
    bool: True if at least one face was detected
    '''

    face_cascade = cv.CascadeClassifier('app/data/haarcascade_frontalface_default.xml')
    gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)

    if len(faces) == 0:
        return False

    for (x, y, w, h) in faces:
        cv.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)

    upload_file_to_s3(id, 'face', img, image_name)
    return True

# if __name__ == '__main__':
#     # example usage:
#     save_thumbnail('duck.png', 160, 120)
#     draw_face_rectangle('trump.jpg')
