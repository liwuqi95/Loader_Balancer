from app.aws import get_average_cpu_load, create_instances, remove_instances
import time


growing_threshold = 80
shrinking_threshold = 40

expend_ratio = 2
shrink_ratio = 4


def auto_scaling():
    average, count = get_average_cpu_load()

    print('LOGGING==Start Auto Scaling==Current Count is ' + str(count) + ' Average is ' + str(round(average)))

    if average > growing_threshold:
        print('LOGGING need to expend by ratio ' + str(expend_ratio))
        create_instances(round(count * (expend_ratio - 1)))
    elif average < shrinking_threshold and count > 1:
        print('LOGGING need to shrink by ratio ' + str(shrink_ratio))
        remove_instances(round(count * (1 - average / shrink_ratio)))

    print('LOGGING==Finish Auto Scaling')



while True:
    auto_scaling()
    time.sleep(2)