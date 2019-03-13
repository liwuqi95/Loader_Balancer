import boto3
from datetime import datetime, timedelta

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


def upload_file_to_s3(id, type, file, filename):
    s3.Bucket('ece1779a2group123bucket').upload_fileobj(file, str(id) + '/' + type + '/' + filename)


def get_instances_list():
    instances = ec2.instances.all()

    return instances


def get_CPU_Utilization(instance_id):
    metric_name = 'CPUUtilization'
    namespace = 'AWS/EC2'
    statistic = 'Average'
    cpu = cloudwatch.get_metric_statistics(
        Period=1 * 60,
        StartTime=datetime.utcnow() - timedelta(seconds=60 * 60),
        EndTime=datetime.utcnow() - timedelta(seconds=0 * 60),
        MetricName=metric_name,
        Namespace=namespace,
        Statistics=[statistic],
        Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}]
    )

    return cpu['Datapoints']
