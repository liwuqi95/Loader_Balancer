from os import sys, path
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from app.aws import get_average_cpu_load, create_instances, remove_instances, get_Network_Request
from app.db import get_db

import time


def auto_scaling():
    try:
        cursor = get_db().cursor(dictionary=True)
        cursor.execute(
            'SELECT id, growing_threshold, shrinking_threshold, expend_ratio, shrink_ratio'
            ' FROM settings s')

        setting = cursor.fetchone()
        get_db().commit()

        growing_threshold = setting['growing_threshold']
        shrinking_threshold = setting['shrinking_threshold']
        expend_ratio = setting['expend_ratio']
        shrink_ratio = setting['shrink_ratio']

        print(
            'LOGGING==Start Auto Scaling== growing threshold = ' + str(
                growing_threshold) + ' shrinking threshold = ' + str(
                shrinking_threshold) + ' expend_ratio = ' + str(expend_ratio) + ' shrink_ratio ' + str(shrink_ratio))

        average, count = get_average_cpu_load()
        print('LOGGING Current Count is ' + str(count) + ' Average is ' + str(round(average)))

        if average > growing_threshold:
            print('LOGGING need to expend by ratio ' + str(expend_ratio))
            create_instances(round(count * (expend_ratio - 1)))
        elif average < shrinking_threshold and count > 1:
            print('LOGGING need to shrink by ratio ' + str(shrink_ratio))
            remove_instances(round(count * (1 - 1 / shrink_ratio)))

        print('LOGGING==Finish Auto Scaling')
    except:
        print('LOGGING==Error')


while True:
    auto_scaling()
    time.sleep(60)
