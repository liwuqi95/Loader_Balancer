import boto3
from datetime import datetime, timedelta
import os
from app import app
import pytz

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

def upload_file_to_s3(id, type, file, filename):
    s3.Bucket('ece1779a2group123bucket').upload_fileobj(file, str(id) + '/' + type + '/' + filename)

def upload(key):
    print('uploading ' + key)
    bucket.upload_file(os.path.join(app.root_path, key), key)

def download(key):
    try:
        bucket.download_file(key, os.path.join(app.root_path, key))
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "404":
            print("The object does not exist.")
        else:
            raise

def list_objects():
    res = cl.list_objects(Bucket='ece1779a2group123bucket')
    if 'Contents' not in res.keys(): return None
    return [{'Key': obj['Key']} for obj in res['Contents']]

def clear():
    objects = list_objects()
    if objects is not None:
        bucket.delete_objects(Delete={'Objects' : objects})

def get_elb_groupArn():
    for group in elb.describe_target_groups()['TargetGroups']:
        if group['TargetGroupName'] == '1779':
            return group['TargetGroupArn']


def get_instances_list():
    instances = ec2.instances.all()
    return instances

def get_CPU_Utilization(instance_id):
    groupArn = get_elb_groupArn()

    instances = []

    for target in elb.describe_target_health(TargetGroupArn=groupArn)['TargetHealthDescriptions']:
        instances.append(target['Target']['Id'])

    return instances


def get_average_cpu_load():
    instances = get_instances_list()

    sum = 0

    for instance in instances:
        data = get_CPU_Utilization(instance, 60, 119)
        if 'y' in data and len(data['y']) > 0:
            sum += data['y'][0]

    return sum / len(instances), len(instances)


def create_instances(n):
    instances = ec2.create_instances(ImageId='ami-0cb01fcf9cf16705c', InstanceType='t2.small', MinCount=n, MaxCount=n)

    for instance in ec2.instances.filter(InstanceIds=list(map(lambda ins: ins.id, instances))):
        instance.wait_until_running()
        print('Created Instance ' + instance.id)

    l = list(map(lambda x: {'Id': x.id, 'Port': 5000, }, instances))
    groupArn = get_elb_groupArn()
    elb.register_targets(TargetGroupArn=groupArn, Targets=l)


def remove_instances(n):
    instances = get_instances_list()
    for instance in ec2.instances.filter(InstanceIds=instances[:n]):
        instance.terminate()
        print('Removed Instance ' + instance.id)


def get_CPU_Utilization(instance, period, seconds):
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

    return cpu['Datapoints']

if __name__ == "__main__":
    pass
