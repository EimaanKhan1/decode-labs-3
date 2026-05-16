import os
import sys
import time
from typing import Dict, List

import boto3
from botocore.exceptions import ClientError, NoCredentialsError

TABLE_NAME = os.environ.get('DYNAMODB_TABLE', 'Interns')
REGION = os.environ.get('AWS_REGION', 'us-east-1')
ENDPOINT_URL = os.environ.get('DYNAMODB_ENDPOINT_URL')

DUMMY_ITEMS: List[Dict[str, str]] = [
    {'Email': 'alice@example.com', 'Name': 'Alice Johnson', 'Role': 'Data Engineer'},
    {'Email': 'bob@example.com', 'Name': 'Bob Singh', 'Role': 'Cloud Architect'},
    {'Email': 'carol@example.com', 'Name': 'Carol Lee', 'Role': 'Database Analyst'},
]


def get_dynamodb_resource():
    kwargs = {'region_name': REGION}
    if ENDPOINT_URL:
        kwargs['endpoint_url'] = ENDPOINT_URL
    return boto3.resource('dynamodb', **kwargs)


def get_dynamodb_client():
    kwargs = {'region_name': REGION}
    if ENDPOINT_URL:
        kwargs['endpoint_url'] = ENDPOINT_URL
    return boto3.client('dynamodb', **kwargs)


def create_table():
    dynamodb = get_dynamodb_resource()
    try:
        table = dynamodb.create_table(
            TableName=TABLE_NAME,
            AttributeDefinitions=[
                {'AttributeName': 'Email', 'AttributeType': 'S'},
            ],
            KeySchema=[
                {'AttributeName': 'Email', 'KeyType': 'HASH'},
            ],
            BillingMode='PAY_PER_REQUEST',
            Tags=[
                {'Key': 'Project', 'Value': 'CloudComputingProject3'},
                {'Key': 'Owner', 'Value': 'DecodeLabs'},
            ],
        )
        print(f'Creating table {TABLE_NAME}...')
        table.wait_until_exists()
        print('Table created successfully.')
        return table
    except ClientError as error:
        if error.response['Error']['Code'] == 'ResourceInUseException':
            print(f'Table {TABLE_NAME} already exists.')
            return dynamodb.Table(TABLE_NAME)
        raise


def list_tables():
    client = get_dynamodb_client()
    response = client.list_tables()
    print('Existing DynamoDB tables:', response.get('TableNames', []))


def insert_dummy_records():
    table = get_dynamodb_resource().Table(TABLE_NAME)
    print(f'Inserting {len(DUMMY_ITEMS)} dummy Interns records...')
    for item in DUMMY_ITEMS:
        table.put_item(Item=item)
    print('Dummy records inserted.')


def scan_table():
    table = get_dynamodb_resource().Table(TABLE_NAME)
    response = table.scan()
    items = response.get('Items', [])
    print(f'Total records in {TABLE_NAME}: {len(items)}')
    for item in items:
        print(item)
    return items


def delete_table():
    table = get_dynamodb_resource().Table(TABLE_NAME)
    table.delete()
    print(f'Deleting table {TABLE_NAME}...')
    waiter = get_dynamodb_client().get_waiter('table_not_exists')
    waiter.wait(TableName=TABLE_NAME)
    print('Table deleted.')


def parse_args():
    import argparse

    parser = argparse.ArgumentParser(description='Cloud Computing Project 3: DynamoDB Interns table')
    parser.add_argument('--create', action='store_true', help='Create the DynamoDB table')
    parser.add_argument('--insert', action='store_true', help='Insert dummy records')
    parser.add_argument('--scan', action='store_true', help='Scan and print table contents')
    parser.add_argument('--delete', action='store_true', help='Delete the DynamoDB table')
    parser.add_argument('--list', action='store_true', help='List DynamoDB tables')
    return parser.parse_args()


if __name__ == '__main__':
    try:
        args = parse_args()
        if not any([args.create, args.insert, args.scan, args.delete, args.list]):
            print('No action selected. Running create, insert, and scan by default.')
            args.create = args.insert = args.scan = True

        if args.list:
            list_tables()
        if args.create:
            create_table()
        if args.insert:
            insert_dummy_records()
        if args.scan:
            scan_table()
        if args.delete:
            delete_table()

    except NoCredentialsError:
        print('AWS credentials not found. Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY or use a configured AWS profile.')
        sys.exit(1)
    except ClientError as error:
        print('AWS ClientError:', error)
        sys.exit(1)
    except Exception as exc:
        print('Unexpected error:', exc)
        sys.exit(1)
