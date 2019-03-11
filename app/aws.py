import boto3

s3 = boto3.resource('s3',
                    aws_access_key_id='AKIAIBS34MHIN5U5W24A',
                    aws_secret_access_key='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',
                    region_name='us-east-1')


def upload_file_to_s3(id, type, file, filename):
    s3.Bucket('ece1779a2group123bucket').upload_fileobj(file, str(id) + '/' + type + '/' + filename)
