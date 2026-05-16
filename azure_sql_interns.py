import argparse
import os
import sys

import pyodbc

TABLE_NAME = 'Interns'
DUMMY_ITEMS = [
    {'Email': 'alice@example.com', 'Name': 'Alice Johnson', 'Role': 'Data Engineer'},
    {'Email': 'bob@example.com', 'Name': 'Bob Singh', 'Role': 'Cloud Architect'},
    {'Email': 'carol@example.com', 'Name': 'Carol Lee', 'Role': 'Database Analyst'},
]

DRIVER = os.environ.get('AZURE_SQL_DRIVER', '{ODBC Driver 18 for SQL Server}')
SERVER = os.environ.get('AZURE_SQL_SERVER', 'your_server.database.windows.net')
DATABASE = os.environ.get('AZURE_SQL_DATABASE', 'internsdb')
USERNAME = os.environ.get('AZURE_SQL_USERNAME', 'azureuser')
PASSWORD = os.environ.get('AZURE_SQL_PASSWORD', 'ChangeMe123!')
ENCRYPT = os.environ.get('AZURE_SQL_ENCRYPT', 'yes')
TRUST_SERVER_CERTIFICATE = os.environ.get('AZURE_SQL_TRUST_SERVER_CERTIFICATE', 'no')


def get_connection():
    conn_str = (
        f'DRIVER={DRIVER};SERVER={SERVER};DATABASE={DATABASE};UID={USERNAME};PWD={PASSWORD};'
        f'Encrypt={ENCRYPT};TrustServerCertificate={TRUST_SERVER_CERTIFICATE};Connection Timeout=30;'
    )
    return pyodbc.connect(conn_str)


def create_table():
    sql = f"""
    IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='{TABLE_NAME}' AND xtype='U')
    CREATE TABLE {TABLE_NAME} (
        Email NVARCHAR(256) PRIMARY KEY,
        Name NVARCHAR(256) NOT NULL,
        Role NVARCHAR(256) NOT NULL
    )
    """
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql)
            conn.commit()
    print(f'Table {TABLE_NAME} created or verified.')


def insert_dummy_records():
    with get_connection() as conn:
        with conn.cursor() as cursor:
            for item in DUMMY_ITEMS:
                cursor.execute(
                    f"MERGE INTO {TABLE_NAME} AS target USING (SELECT ? AS Email, ? AS Name, ? AS Role) AS source "
                    "ON target.Email = source.Email "
                    "WHEN MATCHED THEN UPDATE SET Name = source.Name, Role = source.Role "
                    "WHEN NOT MATCHED THEN INSERT (Email, Name, Role) VALUES (source.Email, source.Name, source.Role);",
                    item['Email'], item['Name'], item['Role'],
                )
            conn.commit()
    print(f'Inserted or updated {len(DUMMY_ITEMS)} dummy records.')


def scan_table():
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(f'SELECT Email, Name, Role FROM {TABLE_NAME} ORDER BY Email')
            rows = cursor.fetchall()
            print(f'Found {len(rows)} rows in {TABLE_NAME}:')
            for row in rows:
                print({'Email': row.Email, 'Name': row.Name, 'Role': row.Role})


def drop_table():
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(f'DROP TABLE IF EXISTS {TABLE_NAME}')
            conn.commit()
    print(f'Table {TABLE_NAME} dropped.')


def parse_args():
    parser = argparse.ArgumentParser(description='Azure SQL Interns project helper')
    parser.add_argument('--create-table', action='store_true', help='Create the Interns table')
    parser.add_argument('--insert', action='store_true', help='Insert dummy records')
    parser.add_argument('--scan', action='store_true', help='Scan the Interns table')
    parser.add_argument('--drop-table', action='store_true', help='Drop the Interns table')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    if not any(vars(args).values()):
        print('No action selected; running create-table, insert, and scan by default.')
        args.create_table = args.insert = args.scan = True

    try:
        if args.create_table:
            create_table()
        if args.insert:
            insert_dummy_records()
        if args.scan:
            scan_table()
        if args.drop_table:
            drop_table()
    except pyodbc.Error as exc:
        print('pyodbc error:', exc)
        sys.exit(1)
    except Exception as exc:
        print('Unexpected error:', exc)
        sys.exit(1)
