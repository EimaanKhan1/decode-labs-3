# Cloud Computing Project 3 — Data Warehouse

This repository provides three alternative implementations for **Project 3** using managed cloud database technologies:

- `dynamodb_interns.py` — AWS DynamoDB NoSQL implementation
- `aws_rds_interns.py` — AWS RDS relational database implementation
- `azure_sql_interns.py` — Azure SQL Database connection and table setup

## Requirements implemented
- Provision a managed cloud database system.
- Create a table named `Interns`.
- Use columns/attributes: `Name`, `Role`, `Email`.
- Insert dummy records to test persistence.
- Connect to the database using a Python script.

## Files
- `Cloud Computing Project 3.pdf` — original project brief.
- `cloud_project_3_text.txt` — extracted PDF content from the project brief.
- `extract_pdf.ipynb` — notebook used to inspect and extract the lab requirements.
- `dynamodb_interns.py` — AWS DynamoDB script.
- `aws_rds_interns.py` — AWS RDS PostgreSQL script.
- `azure_sql_interns.py` — Azure SQL Database script.
- `requirements.txt` — Python dependencies.

## Setup
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure cloud credentials for the implementation you want to run.

### AWS DynamoDB
- Set `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and optionally `AWS_SESSION_TOKEN`
- Set `AWS_REGION`, for example `us-east-1`

### AWS RDS
- Set the same AWS credentials and region variables above.
- Optionally override the database connection settings:
  - `RDS_DB_IDENTIFIER`
  - `RDS_DB_NAME`
  - `RDS_MASTER_USERNAME`
  - `RDS_MASTER_PASSWORD`
  - `RDS_DB_INSTANCE_CLASS`
  - `RDS_ENGINE`

### Azure SQL
- Set Azure SQL environment variables:
  - `AZURE_SQL_SERVER`
  - `AZURE_SQL_DATABASE`
  - `AZURE_SQL_USERNAME`
  - `AZURE_SQL_PASSWORD`
  - `AZURE_SQL_DRIVER` (optional, defaults to `{ODBC Driver 18 for SQL Server}`)

## Usage
### DynamoDB
```bash
python dynamodb_interns.py
```
- `--list` to list tables
- `--delete` to remove the table
- `DYNAMODB_ENDPOINT_URL=http://localhost:8000 python dynamodb_interns.py` to use DynamoDB Local

### AWS RDS
```bash
python aws_rds_interns.py
```
- `--list` to list RDS instances
- `--create` to create the RDS instance
- `--setup-table` to create the `Interns` table
- `--insert` to insert dummy records
- `--scan` to query persisted rows
- `--delete` to delete the RDS instance

### Azure SQL
```bash
python azure_sql_interns.py
```
- `--create-table` to create the `Interns` table
- `--insert` to insert dummy records
- `--scan` to print persisted rows
- `--drop-table` to remove the table

### Unified wrapper script
```bash
python cloud_db_interns.py --provider aws-rds
```
Use `--provider dynamodb`, `--provider aws-rds`, or `--provider azure-sql` and pass any supported underlying script flags with `--action`.

## Azure CLI provisioning guide
If you want to provision Azure SQL Database using Azure CLI, follow these steps:

1. Login to Azure:
   ```bash
   az login
   ```
2. Create a resource group:
   ```bash
   az group create --name interns-rg --location eastus
   ```
3. Create an Azure SQL server:
   ```bash
   az sql server create --name interns-sql-server --resource-group interns-rg --location eastus --admin-user myadmin --admin-password 'ChangeMe123!'
   ```
4. Create an Azure SQL database:
   ```bash
   az sql db create --resource-group interns-rg --server interns-sql-server --name internsdb --service-objective S0
   ```
5. Configure firewall rules to allow your client IP:
   ```bash
   az sql server firewall-rule create --resource-group interns-rg --server interns-sql-server --name AllowMyIP --start-ip-address 0.0.0.0 --end-ip-address 255.255.255.255
   ```
6. Update environment variables and run the Azure SQL script:
   ```bash
   export AZURE_SQL_SERVER='tcp:interns-sql-server.database.windows.net'
   export AZURE_SQL_DATABASE='internsdb'
   export AZURE_SQL_USERNAME='myadmin'
   export AZURE_SQL_PASSWORD='ChangeMe123!'
   python azure_sql_interns.py
   ```

## Notes
- `dynamodb_interns.py` uses a NoSQL managed database design with `Email` as the partition key.
- `aws_rds_interns.py` uses AWS RDS for PostgreSQL and demonstrates provisioning, table creation, and persistence.
- `azure_sql_interns.py` connects to Azure SQL Database and creates/queries the `Interns` table.
- `cloud_db_interns.py` provides a unified wrapper to run the selected provider implementation.
- Use the extracted lab brief in `cloud_project_3_text.txt` to verify requirements and implementation steps.
