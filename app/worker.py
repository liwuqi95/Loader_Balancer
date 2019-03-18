from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, send_from_directory
)

from flask import jsonify

from app.aws import get_CPU_Utilization, get_instances_list, create_instances, remove_instances

bp = Blueprint('worker', __name__)


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
    data = get_CPU_Utilization(id, 60, 1800)

    return jsonify(data)


@bp.route('/worker/setting')
def setting():
    return render_template('worker/setting.html')


@bp.route('/worker/remove_data')
def remove_data():
    return redirect(url_for('worker.workers'))
