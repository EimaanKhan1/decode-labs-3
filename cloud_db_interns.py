import argparse
import os
import subprocess
import sys

SCRIPTS = {
    'dynamodb': 'dynamodb_interns.py',
    'aws-rds': 'aws_rds_interns.py',
    'azure-sql': 'azure_sql_interns.py',
}

DEFAULT_ACTIONS = {
    'dynamodb': [],
    'aws-rds': [],
    'azure-sql': [],
}


def run_script(provider: str, extra_args=None):
    if provider not in SCRIPTS:
        raise ValueError(f'Unsupported provider: {provider}')

    script_path = os.path.join(os.path.dirname(__file__), SCRIPTS[provider])
    args = [sys.executable, script_path]
    if extra_args:
        args.extend(extra_args)
    print('Running:', ' '.join(args))
    result = subprocess.run(args)
    return result.returncode


def parse_args():
    parser = argparse.ArgumentParser(description='Unified Cloud DB Interns helper')
    parser.add_argument('--provider', choices=SCRIPTS.keys(), default='dynamodb', help='Choose the cloud provider implementation')
    parser.add_argument('--action', nargs='*', help='Arguments passed to the underlying provider script')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    provider = args.provider
    action_args = args.action or DEFAULT_ACTIONS[provider]
    exit_code = run_script(provider, action_args)
    sys.exit(exit_code)
