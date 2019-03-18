import functools
from werkzeug.exceptions import abort

from flask import (
    Blueprint, flash, g, redirect, request, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from app.db import get_db
from app.ImageProcessing import save_thumbnail, draw_face_rectangle
import os
from app import app
from app.aws import move_to_s3

bp = Blueprint('api', __name__, url_prefix='/api')


@bp.route('/register', methods=['POST'])
def register():
    '''
    handle requests to api/register

    params:
    username and password

    return: ok if success, otherwise a error message will be returned with request content type
    '''
    username = request.form['username']
    password = request.form['password']

    cursor = get_db().cursor()
    error = None

   
    if not username:
        error = 'Username is required.'
    elif not password:
        error = 'Password is required.'
    elif '\'' in password or '\"' in password:
        error = 'Password cannot contain quotation marks.'
    elif '\'' in username or '\"' in username:
        error = 'Username cannot contain quotation marks.'
    else:
        cursor.execute(
            'SELECT id FROM users WHERE username = %s', (username,)
        )
        if cursor.fetchone() is not None:
            error = 'User {0} is already registered.'.format(username)

    if error is None:
        cursor.execute('INSERT INTO users (username, password) VALUES (%s, %s)',
                       (username, generate_password_hash(password)))
        get_db().commit()
        return 'ok\n'

    return abort(404, error)


##TODO add more image types
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'jp2', 'bmp', 'ppm', 'pgm', 'pbm', 'tiff'])


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@bp.route('/upload', methods=['POST'])
def upload():
    '''
    handle requests to api/upload

    params:
    username, password and the file content

    return: ok if success, otherwise a error message will be returned with request content type
    '''
    error = None
    username = request.form['username']
    password = request.form['password']
    cursor = get_db().cursor(dictionary=True)
    cursor.execute('SELECT * FROM users WHERE username = %s', (username,))

    user = cursor.fetchone()
    if user is None:
        error = 'User is not valid'
    elif not check_password_hash(user["password"], password):
        error = 'Incorrect password.'

    if error is not None:
        return abort(404, error)

    if 'file' not in request.files:
        error = 'You cannot upload empty file.'
    elif request.files['file'].filename == '':
        error = "Your file name is not valid."
    elif not allowed_file(request.files['file'].filename):
        error = "Your File format is not correct: {}".format(request.files['file'].filename)
    elif '\'' in request.files['file'].filename or '\"' in request.files['file'].filename:
        error = "Invalid file name."
    else:
        file = request.files['file']
        filename = file.filename
        cursor = get_db().cursor()
        cursor.execute('INSERT INTO images ( name, user_id) VALUES (%s, %s)', (filename, user['id']))
        id = cursor.lastrowid

        filename = str(id) + '.' + filename.rsplit('.', 1)[1].lower()
        file.save(os.path.join(app.root_path, 'images/', filename))

        try:
            save_thumbnail(filename, 200, 200)
            draw_face_rectangle(filename)
            move_to_s3('images/' + filename)
            get_db().commit()
            return 'ok\n'

        except:
            get_db().rollback()
            error = "Error creating image."
            os.remove(os.path.join(app.root_path, 'images/', filename))

    return abort(404, error)