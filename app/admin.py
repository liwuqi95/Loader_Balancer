from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, send_from_directory
)
from werkzeug.exceptions import abort

from app.auth import login_required
from app.db import get_db

import os
from flask import jsonify

from app.aws import get_CPU_Utilization, get_instances_list

bp = Blueprint('admin', __name__)


@bp.route('/admin')
def workers():
    """List workers"""
    instances = get_instances_list()

    return render_template('admin/workers.html', instances=instances, cpu_data=cpu_data)


@bp.route('/admin/cpu_data/<string:id>')
def cpu_data(id):
    data = get_CPU_Utilization(id)

    result = {'x': [], 'y': []}

    for d in data:
        result['x'].append(d['Timestamp'].strftime("%H:%M:%S"))
        result['y'].append(d['Average'])

    return jsonify(result)
