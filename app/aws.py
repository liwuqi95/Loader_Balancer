import boto3
from datetime import datetime, timedelta
import os
from app import app

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

if __name__ == "__main__":
    pass
    info = rds.describe_db_instances(DBInstanceIdentifier='cloud')
    print(info['DBInstances'][0]['Endpoint'])