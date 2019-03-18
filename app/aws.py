import boto3
from datetime import datetime, timedelta
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

elb = boto3.client('elbv2', aws_access_key_id='AKIAIBS34MHIN5U5W24A',
                   aws_secret_access_key='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',
                   region_name='us-east-1')


def upload_file_to_s3(id, type, file, filename):
    s3.Bucket('ece1779a2group123bucket').upload_fileobj(file, str(id) + '/' + type + '/' + filename)


def get_elb_groupArn():
    for group in elb.describe_target_groups()['TargetGroups']:
        if group['TargetGroupName'] == '1779':
            return group['TargetGroupArn']


def get_instances_list():
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

    result = {'x': [], 'y': []}

    for d in cpu['Datapoints']:
        result['x'].insert(0, d['Timestamp'].astimezone(tz=pytz.timezone('US/Eastern')).strftime("%H:%M:%S"))
        result['y'].insert(0, (d['Average']))

    return result
