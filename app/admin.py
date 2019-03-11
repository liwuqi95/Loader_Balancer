from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, send_from_directory
)
from werkzeug.exceptions import abort

from app.auth import login_required
from app.db import get_db

import os
import boto3
from datetime import datetime

cloudwatch = boto3.resource('cloudwatch',
                            aws_access_key_id='AKIAIBS34MHIN5U5W24A',
                            aws_secret_access_key='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',
                            region_name='us-east-1')

bp = Blueprint('admin', __name__)


@bp.route('/admin/workers')
def workers():
    """List workers"""

    metric = cloudwatch.Metric('AWS/EC2', 'CPUUtilization')

    print(metric.get_statistics(StartTime=datetime(2019, 3, 11),
                                EndTime=datetime(2019, 3, 12),
                                Period=3600,
                                Statistics=['Average'],
                                Unit='Seconds'))

    return render_template('admin/workers.html')
