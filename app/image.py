from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, send_from_directory
)
from werkzeug.exceptions import abort

import os
from app.auth import login_required
from app.db import get_db
from app.aws import move_to_s3
from app import app
from app.ImageProcessing import save_thumbnail, draw_face_rectangle

bp = Blueprint('image', __name__)
url_prefix = 'https://s3.amazonaws.com/ece1779a2group123bucket/'

def get_url(type, image):
    key = '/' + str(image["id"]) + '.' + image["name"].rsplit('.', 1)[1]
    return url_prefix + type + key

@bp.route('/')
@login_required
def index():
    """Show all the images, most recent first."""
    cursor = get_db().cursor(dictionary=True)

    cursor.execute(
        'SELECT p.id as id, name, created, user_id, username'
        ' FROM images p JOIN users u ON p.user_id = u.id'
        ' WHERE p.user_id = %s '
        ' ORDER BY created DESC', (g.user['id'],)
    )

    images = cursor.fetchall()
    for image in images:
        image['thumb'] = get_url('thumbnails', image)
    return render_template('image/index.html', images=images)

@bp.route('/image/<int:id>')
@login_required
def show(id):
    """Show image details by given id"""
    cursor = get_db().cursor(dictionary=True)

    cursor.execute(
        'SELECT p.id, name, user_id, created'
        ' FROM images p'
        ' WHERE p.id = %s',
        (id,))

    image = cursor.fetchone()

    if image is None:
        abort(404, "Image doesn't exist.".format(id))

    if image['user_id'] != g.user['id']:
        abort(403)
    
    return render_template('image/show.html', image=image, image_url=get_url('images', image), face_url=get_url('faces', image))


##TODO add more image types
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'jp2', 'bmp', 'ppm', 'pgm', 'pbm', 'tiff'])


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    """Create a new image for the current user."""
    if request.method == 'POST':
        error = None

        if 'file' not in request.files:
            error = 'You cannot upload empty file.'
        elif request.files['file'].filename == '':
            error = "Your file name is not valid."
        elif not allowed_file(request.files['file'].filename):
            error = "Your File format is not correct."
        elif '\'' in request.files['file'].filename or '\"' in request.files['file'].filename:
            error = "Invalid file name."
        else:
            file = request.files['file']
            filename = file.filename
            cursor = get_db().cursor()
            cursor.execute('INSERT INTO images ( name, user_id) VALUES (%s, %s)', (filename, g.user['id']))
            id = cursor.lastrowid

            filename = str(id) + '.' + filename.rsplit('.', 1)[1].lower()
            file.save(os.path.join(app.root_path, 'images/', filename))

            try:
                save_thumbnail(filename, 200, 200)
                draw_face_rectangle(filename)
                move_to_s3('images/' + filename)
                get_db().commit()
                return redirect(url_for('image.show', id=id))

            except:
                get_db().rollback()
                error = "Error creating image."
                os.remove(os.path.join(app.root_path, 'images/', filename))

        if error is not None:
            flash(error)

    return render_template('image/create.html')
