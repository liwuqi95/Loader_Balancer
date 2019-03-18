from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, send_from_directory
)

from datetime import datetime, timedelta
from flask import jsonify
from app.db import get_db
from app.aws import get_CPU_Utilization, get_instances_list, create_instances, remove_instances

bp = Blueprint('worker', __name__)
from app.db import init_db


@bp.before_app_request
def request_count():
    cursor = get_db().cursor(dictionary=True)

    time = datetime.now().strftime('%Y-%m-%d %H-%M-00')

    cursor.execute(
        'SELECT id, ip, request_count '
        ' FROM requests '
        ' WHERE requests.created = %s '
        ' ORDER BY created DESC', (time,)
    )

    r = cursor.fetchone()
    if r is None:
        cursor.execute('INSERT INTO requests ( ip, created, request_count) VALUES (%s, %s, %s )',
                       (request.host, time, 0))
        print('inserted')
    else:
        cursor.execute(
            'UPDATE requests SET request_count = %s WHERE id = %s ',
            (r['request_count'] + 1, r['id']))

    get_db().commit()

@bp.route('/workers')
def workers():
    """List workers"""
    instances = get_instances_list()

    return render_template('worker/index.html', instances=instances, cpu_data=cpu_data)


@bp.route('/worker/<string:id>')
def show(id):
    return render_template('worker/show.html')


@bp.route('/worker/create_instance')
def create_instance():
    create_instances(1)
    return jsonify('success')


@bp.route('/worker/remove_instance')
def remove_instance():
    remove_instances(1)
    return jsonify('success')


@bp.route('/worker/cpu_data/<string:id>')
def cpu_data(id):
    instance, data = get_CPU_Utilization(id, 600, 18000)

    cursor = get_db().cursor(dictionary=True)

    cursor.execute(
        'SELECT request_count, created '
        ' FROM requests WHERE ip = %s AND created > %s ',
        (instance.public_ip_address, (datetime.now() - timedelta(minutes=30)).strftime('%Y-%m-%d %H-%M-00')))

    requests = cursor.fetchall()

    result = {}

    for request in requests:
        result[request['created'].strftime("%H:%M:%S")] = request['request_count']

    for label in data['x']:
        if label in result:
            data['z'].append(result[label])
        else:
            data['z'].append(0)

    return jsonify(data)


@bp.route('/worker/setting', methods=('GET', 'POST'))
def setting():
    if request.method == 'POST':
        growing_threshold = float(request.form['growing_threshold'])
        shrinking_threshold = float(request.form['shrinking_threshold'])
        expend_ratio = float(request.form['expend_ratio'])
        shrink_ratio = float(request.form['shrink_ratio'])
        cursor = get_db().cursor()

        cursor.execute(
            'UPDATE settings SET growing_threshold = %s, shrinking_threshold = %s, expend_ratio = %s , shrink_ratio = %s WHERE id = 1 ',
            (growing_threshold, shrinking_threshold, expend_ratio, shrink_ratio))
        get_db().commit()

    cursor = get_db().cursor(dictionary=True)
    cursor.execute(
        'SELECT id, growing_threshold, shrinking_threshold, expend_ratio, shrink_ratio'
        ' FROM settings s')

    setting = cursor.fetchone()

    return render_template('worker/setting.html', setting=setting)


@bp.route('/worker/remove_data')
def remove_data():
    init_db()
    return redirect(url_for('worker.workers'))
