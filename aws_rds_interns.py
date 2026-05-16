import argparse
import os
import sys
import time

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

DB_IDENTIFIER = os.environ.get('RDS_DB_IDENTIFIER', 'interns-rds-db')
DB_NAME = os.environ.get('RDS_DB_NAME', 'internsdb')
DB_USERNAME = os.environ.get('RDS_MASTER_USERNAME', 'adminuser')
DB_PASSWORD = os.environ.get('RDS_MASTER_PASSWORD', 'ChangeMe123!')
DB_CLASS = os.environ.get('RDS_DB_INSTANCE_CLASS', 'db.t3.micro')
DB_ENGINE = os.environ.get('RDS_ENGINE', 'postgres')
DB_ALLOCATED_STORAGE = int(os.environ.get('RDS_ALLOCATED_STORAGE', '20'))
REGION = os.environ.get('AWS_REGION', 'us-east-1')
DEFAULT_PORT = 5432 if DB_ENGINE == 'postgres' else 3306
TABLE_NAME = 'Interns'
DUMMY_ITEMS = [
    {'Email': 'alice@example.com', 'Name': 'Alice Johnson', 'Role': 'Data Engineer'},
    {'Email': 'bob@example.com', 'Name': 'Bob Singh', 'Role': 'Cloud Architect'},
    {'Email': 'carol@example.com', 'Name': 'Carol Lee', 'Role': 'Database Analyst'},
]


def get_rds_client():
    return boto3.client('rds', region_name=REGION)


def get_db_endpoint(db_identifier: str):
    client = get_rds_client()
    response = client.describe_db_instances(DBInstanceIdentifier=db_identifier)
    db_instances = response['DBInstances']
    if not db_instances:
        raise RuntimeError('No RDS instance found')
    instance = db_instances[0]
    endpoint = instance['Endpoint']
    return endpoint['Address'], endpoint['Port']


def wait_for_available(db_identifier: str):
    client = get_rds_client()
    print('Waiting for RDS instance to become available...')
    waiter = client.get_waiter('db_instance_available')
    waiter.wait(DBInstanceIdentifier=db_identifier)
    print('RDS instance is available.')


def create_rds_instance(db_identifier: str):
    client = get_rds_client()
    try:
        print(f'Creating RDS instance {db_identifier}...')
        client.create_db_instance(
            DBInstanceIdentifier=db_identifier,
            AllocatedStorage=DB_ALLOCATED_STORAGE,
            DBInstanceClass=DB_CLASS,
            Engine=DB_ENGINE,
            MasterUsername=DB_USERNAME,
            MasterUserPassword=DB_PASSWORD,
            DBName=DB_NAME,
            PubliclyAccessible=True,
            StorageType='gp2',
            BackupRetentionPeriod=0,
            MultiAZ=False,
            AutoMinorVersionUpgrade=True,
        )
        wait_for_available(db_identifier)
        return get_db_endpoint(db_identifier)
    except ClientError as error:
        if error.response['Error']['Code'] == 'DBInstanceAlreadyExists':
            print(f'RDS instance {db_identifier} already exists.')
            wait_for_available(db_identifier)
            return get_db_endpoint(db_identifier)
        raise


def delete_rds_instance(db_identifier: str):
    client = get_rds_client()
    try:
        print(f'Deleting RDS instance {db_identifier}...')
        client.delete_db_instance(DBInstanceIdentifier=db_identifier, SkipFinalSnapshot=True)
        waiter = client.get_waiter('db_instance_deleted')
        waiter.wait(DBInstanceIdentifier=db_identifier)
        print('RDS instance deleted.')
    except ClientError as error:
        if error.response['Error']['Code'] == 'DBInstanceNotFound':
            print(f'RDS instance {db_identifier} does not exist.')
            return
        raise


def create_database_table(host: str, port: int):
    engine = create_engine(f'postgresql+psycopg2://{DB_USERNAME}:{DB_PASSWORD}@{host}:{port}/{DB_NAME}')
    ddl = f"""
    CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
        Email VARCHAR(256) PRIMARY KEY,
        Name VARCHAR(256) NOT NULL,
        Role VARCHAR(256) NOT NULL
    )
    """
    with engine.begin() as conn:
        conn.execute(text(ddl))
    print(f'Table {TABLE_NAME} created or verified.')


def insert_dummy_records(host: str, port: int):
    engine = create_engine(f'postgresql+psycopg2://{DB_USERNAME}:{DB_PASSWORD}@{host}:{port}/{DB_NAME}')
    insert_sql = text(
        f"INSERT INTO {TABLE_NAME} (Email, Name, Role) VALUES (:Email, :Name, :Role) "
        "ON CONFLICT (Email) DO UPDATE SET Name = EXCLUDED.Name, Role = EXCLUDED.Role"
    )
    with engine.begin() as conn:
        for item in DUMMY_ITEMS:
            conn.execute(insert_sql, **item)
    print(f'Inserted or updated {len(DUMMY_ITEMS)} dummy records.')


def scan_table(host: str, port: int):
    engine = create_engine(f'postgresql+psycopg2://{DB_USERNAME}:{DB_PASSWORD}@{host}:{port}/{DB_NAME}')
    with engine.connect() as conn:
        rows = conn.execute(text(f'SELECT Email, Name, Role FROM {TABLE_NAME} ORDER BY Email')).fetchall()
        print(f'Found {len(rows)} rows in {TABLE_NAME}:')
        for row in rows:
            print(dict(row))


def list_rds_instances():
    client = get_rds_client()
    response = client.describe_db_instances()
    for instance in response['DBInstances']:
        print(instance['DBInstanceIdentifier'], instance['DBInstanceStatus'])


def parse_args():
    parser = argparse.ArgumentParser(description='AWS RDS Interns project helper')
    parser.add_argument('--create', action='store_true', help='Create the RDS instance')
    parser.add_argument('--delete', action='store_true', help='Delete the RDS instance')
    parser.add_argument('--list', action='store_true', help='List RDS instances')
    parser.add_argument('--setup-table', action='store_true', help='Create the Interns table in the database')
    parser.add_argument('--insert', action='store_true', help='Insert dummy records into the Interns table')
    parser.add_argument('--scan', action='store_true', help='Scan and print the Interns table contents')
    parser.add_argument('--host', type=str, help='Use an existing RDS host endpoint instead of provisioning a new instance')
    parser.add_argument('--port', type=int, default=DEFAULT_PORT, help='Database port to use for connections')
    return parser.parse_args()


if __name__ == '__main__':
    try:
        args = parse_args()
        if not any(vars(args).values()):
            print('No arguments provided; defaulting to create, setup-table, insert, and scan.')
            args.create = args.setup_table = args.insert = args.scan = True

        host = args.host
        port = args.port
        if args.create:
            host, port = create_rds_instance(DB_IDENTIFIER)

        if args.list:
            list_rds_instances()

        if args.setup_table:
            if not host:
                host, port = get_db_endpoint(DB_IDENTIFIER)
            create_database_table(host, port)

        if args.insert:
            if not host:
                host, port = get_db_endpoint(DB_IDENTIFIER)
            insert_dummy_records(host, port)

        if args.scan:
            if not host:
                host, port = get_db_endpoint(DB_IDENTIFIER)
            scan_table(host, port)

        if args.delete:
            delete_rds_instance(DB_IDENTIFIER)

    except NoCredentialsError:
        print('AWS credentials are not configured. Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY or use a configured AWS profile.')
        sys.exit(1)
    except ClientError as error:
        print('AWS ClientError:', error)
        sys.exit(1)
    except SQLAlchemyError as error:
        print('SQLAlchemy error:', error)
        sys.exit(1)
    except Exception as exc:
        print('Unexpected error:', exc)
        sys.exit(1)
