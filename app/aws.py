import boto3
from datetime import datetime, timedelta
import os
from app import app
import pytz
import time
s3 = boto3.resource('s3',
                    aws_access_key_id='AKIAIBS34MHIN5U5W24A',
                    aws_secret_access_key='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',
                    region_name='us-east-1')

ec2 = boto3.resource('ec2', aws_access_key_id='AKIAIBS34MHIN5U5W24A',
                     aws_secret_access_key='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',
                     region_name='us-east-1')

cloudwatch = boto3.client('cloudwatch', aws_access_key_id='AKIAIBS34MHIN5U5W24A',
                          aws_secret_access_key='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',
                          region_name='us-east-1')

cl = boto3.client('s3',
                  aws_access_key_id='AKIAIBS34MHIN5U5W24A',
                  aws_secret_access_key='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',
                  region_name='us-east-1')

rds = boto3.client('rds',
                   aws_access_key_id='AKIAIBS34MHIN5U5W24A',
                   aws_secret_access_key='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',
                   region_name='us-east-1')

bucket = s3.Bucket('ece1779a2group123bucket')

elb = boto3.client('elbv2', aws_access_key_id='AKIAIBS34MHIN5U5W24A',
                   aws_secret_access_key='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',
                   region_name='us-east-1')


def move_to_s3(key):
    """store image to s3"""
    path = os.path.join(app.root_path, key)
    bucket.upload_file(path, key)
    os.remove(path)
    print("Moved to s3")


def list_objects():
    """list all the s3 objects"""
    res = cl.list_objects(Bucket='ece1779a2group123bucket')
    if 'Contents' not in res.keys(): return None
    return [{'Key': obj['Key']} for obj in res['Contents']]


def clear_s3():
    """clear s3 """
    objects = list_objects()
    if objects is not None:
        bucket.delete_objects(Delete={'Objects': objects})


def get_elb_groupArn():
    """get elb group arn"""
    for group in elb.describe_target_groups()['TargetGroups']:
        if group['TargetGroupName'] == '1779':
            return group['TargetGroupArn']


def get_instances_list():
    """list all instances"""
    groupArn = get_elb_groupArn()

    instances = []

    for target in elb.describe_target_health(TargetGroupArn=groupArn)['TargetHealthDescriptions']:
        instances.append(target['Target']['Id'])

    return instances


def get_average_cpu_load():
    """get average cpu load"""
    instances = get_instances_list()

    sum = 0

    for instance in instances:
        i, data = get_CPU_Utilization(instance, 60, 119)
        if 'y' in data and len(data['y']) > 0:
            sum += data['y'][0]

    return sum / len(instances) if len(instances) > 0 else 1, len(instances)


def create_instances(n):
    """create n instances"""
    imageID = ''
    for img in ec2.images.filter(Owners=['106330839424']):
        imageID = img.id

    instances = ec2.create_instances(ImageId=imageID, InstanceType='t2.small',
                                     SecurityGroupIds=['sg-06f0dba2ff5b61362'], MinCount=n,
                                     MaxCount=n, Monitoring={'Enabled': True})

    for instance in ec2.instances.filter(InstanceIds=list(map(lambda ins: ins.id, instances))):
        print('Creating Instance ' + instance.id + ' with image ' + imageID)
        instance.wait_until_running()

    time.sleep(60)

    print('Instance created!')

    l = list(map(lambda x: {'Id': x.id, 'Port': 5000, }, instances))
    groupArn = get_elb_groupArn()
    elb.register_targets(TargetGroupArn=groupArn, Targets=l)


def remove_instances(n):
    """remove n instances"""
    instances = get_instances_list()
    for instance in instances[:n]:
        i = ec2.Instance(instance)
        print('Removing Instance ' + instance)
        i.terminate()


def get_CPU_Utilization(instance, period, seconds):
    """get cpu data for instance"""
    metric_name = 'CPUUtilization'

    cpu = cloudwatch.get_metric_statistics(
        Period=period,
        StartTime=datetime.utcnow() - timedelta(seconds=seconds),
        EndTime=datetime.utcnow(),
        MetricName=metric_name,
        Namespace='AWS/EC2',
        Statistics=['Average'],
        Dimensions=[{'Name': 'InstanceId', 'Value': instance}]
    )

    data = []

    for d in cpu['Datapoints']:
        data.append(d)

    result = {'x': [], 'y': [], 'z': []}

    data.sort(key=lambda x: x['Timestamp'])

    for d in data:
        result['x'].append(d['Timestamp'].astimezone(tz=pytz.timezone('US/Eastern')).strftime("%H:%M:00"))
        result['y'].append(d['Average'])

    instance = ec2.Instance(instance)

    return instance, result


if __name__ == "__main__":
    pass
