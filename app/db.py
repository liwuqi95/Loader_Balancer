import mysql.connector
import os
import click
from flask import current_app, g
from flask.cli import with_appcontext
from app.aws import clear_s3
from app import app

TABLES = {}

TABLES['users'] = (
    "CREATE TABLE `users` ("
    "  `id` int(11) NOT NULL AUTO_INCREMENT,"
    "  `username` varchar(255) NOT NULL,"
    "  `password` varchar(255) NOT NULL,"
    "  PRIMARY KEY (`id`),"
    " UNIQUE (username)"
    ")")

TABLES['images'] = (
    "CREATE TABLE `images` ("
    "  `id` int(11) NOT NULL AUTO_INCREMENT,"
    "  `user_id` int(11) NOT NULL,"
    "  `name` varchar(255) NOT NULL,"
    "   `created` DATETIME DEFAULT CURRENT_TIMESTAMP,"
    "  PRIMARY KEY (`id`), KEY `user_id` (`user_id`),"
    "  CONSTRAINT `image_usrfk_1` FOREIGN KEY (`user_id`) "
    "  REFERENCES `users` (`id`) ON DELETE CASCADE"
    ")")

TABLES['settings'] = (
    "CREATE TABLE `settings` ("
    "  `id` int(11) NOT NULL AUTO_INCREMENT,"
    "  `growing_threshold` float(11) NOT NULL,"
    "  `shrinking_threshold` float(11) NOT NULL,"
    "  `expend_ratio` float(11) NOT NULL,"
    "  `shrink_ratio` float(11) NOT NULL,"
    "  PRIMARY KEY (`id`)"
    ")")

DB = None


def get_db():
    """return current connection or create a new one"""
    global DB
    if DB is None:
        DB = mysql.connector.connect(user='root', password='ece1779pass',
                                     host='ece1779a2db.c15xmaymmeep.us-east-1.rds.amazonaws.com',
                                     port=3306,
                                     database='cloud')

    return DB


def close_db(e=None):
    """Close mysql db connection"""
    db = g.pop('db', None)

    if db is not None:
        db.close()


def init_db():
    """Perform init db Mysql operations"""
    cursor = get_db().cursor()

    cursor.execute("DROP TABLE IF EXISTS images;")
    cursor.execute("DROP TABLE IF EXISTS users;")
    cursor.execute("DROP TABLE IF EXISTS settings;")

    for table_name in TABLES:
        cursor.execute(TABLES[table_name])

    cursor.execute(
        "INSERT INTO settings (growing_threshold, shrinking_threshold, expend_ratio, shrink_ratio) VALUES (%s, %s, %s, %s)",
        (80, 40, 2, 4))

    get_db().commit()

    clear_s3()


@click.command('init-db')
@with_appcontext
def init_db_command():
    """Clear existing data and create new tables."""
    init_db()
    os.system('rm ' + os.path.join(app.root_path, 'images/*'))
    os.system('rm ' + os.path.join(app.root_path, 'faces/*'))
    os.system('rm ' + os.path.join(app.root_path, 'thumbnails/*'))

    click.echo('Initialized the database.')


def init_app(app):
    """Register database functions with the Flask app. This is called by
    the application factory.
    """
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
