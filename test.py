import boto3
from botocore.exceptions import ClientError

secret_name = "OPENAI_API_KEY"
region_name = "ap-southeast-2"
secret = None

try:
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    get_secret_value_response = client.get_secret_value(
        SecretId=secret_name
    )
    
    secret = get_secret_value_response['SecretString']
except Exception as e:
    print(None)

print(secret)