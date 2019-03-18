from os import sys, path

sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from app.aws import get_average_cpu_load, create_instances, remove_instances
import mysql.connector
import time


def auto_scaling(con):
    try:
        cursor = con.cursor(dictionary=True)
        cursor.execute(
            'SELECT id, growing_threshold, shrinking_threshold, expend_ratio, shrink_ratio'
            ' FROM settings s')

        setting = cursor.fetchone()
        con.commit()

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

        if count < 1:
            create_instances(1)
        elif average > growing_threshold:
            print('LOGGING need to expend by ratio ' + str(expend_ratio))
            create_instances(round(count * (expend_ratio - 1)))
        elif average < shrinking_threshold and count > 1:
            print('LOGGING need to shrink by ratio ' + str(shrink_ratio))
            c = round(count * (1 - 1 / shrink_ratio))

            if c >= count:
                c = count - 1 if count - 1 >= 0 else 0

            remove_instances(c)

        print('LOGGING==Finish Auto Scaling')

    except:
        print('LOGGING==Error')


con = mysql.connector.connect(user='root', password='ece1779pass',
                              # host='127.0.0.1',
                              host='ece1779a2db.c15xmaymmeep.us-east-1.rds.amazonaws.com',
                              port=3306,
                              database='cloud')

while True:
    auto_scaling(con)
    time.sleep(60)
