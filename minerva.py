import argparse, configparser
import sys, logging
from minervalib.importer import MinervaImporter
from minervalib.client import MinervaClient
from minervalib.s3 import S3Uploader
from minervalib.fileutils import FileUtils

def check_arguments(args):
    exit = False
    for arg in args:
        if arg[0] is None:
            exit = True
            print("Argument missing:", arg[1])

    if exit:
        sys.exit(1)

parser = argparse.ArgumentParser(description='Minerva CLI')

parser.add_argument('command', type=str,
                    help='Command - available values: [import]')
parser.add_argument('--config', type=str,
                    help='Config file')
parser.add_argument('--dir', type=str,
                    help='Import directory')
parser.add_argument('--username', type=str,
                    help='Username')
parser.add_argument('--password', type=str,
                    help='Password')
parser.add_argument('--endpoint', type=str,
                    help='Minerva endpoint')
parser.add_argument('--region', type=str,
                    help='AWS region')
parser.add_argument('--repository', type=str,
                    help='Repository name')
parser.add_argument('--userpool', type=str,
                    help='Cognito UserPoolId')
parser.add_argument('--client_id', type=str,
                    help='Cognito ClientId')
parser.add_argument('--debug', action='store_const', const=True, help='Debug logging on')

args = parser.parse_args()

root = logging.getLogger()
logging_level = logging.DEBUG if args.debug else logging.INFO
FORMAT = '%(asctime)-15s %(message)s'
logging.basicConfig(stream=sys.stdout, level=logging_level, format=FORMAT)

config = args.config
dir = args.dir
username = args.username
password = args.password
endpoint = args.endpoint
repository = args.repository
region = args.region
userpool = args.userpool
client_id = args.client_id

if config is not None:
    print("Using config file: ", config)
    cp = configparser.ConfigParser()
    cp.read(config)
    username = cp.get('Minerva', 'Username')
    password = cp.get('Minerva', 'Password')
    endpoint = cp.get('Minerva', 'Endpoint')
    userpool = cp.get('Minerva', 'CognitoUserPoolId')
    client_id = cp.get('Minerva', 'CognitoClient')
    region = cp.get('Minerva', 'Region')

check_arguments([(username, "Username"), (password, "Password"), (endpoint, "Endpoint"), (region, "Region"), (userpool, "CognitoUserPoolId"), (client_id, "CognitoClient")])

logging.debug("Username %s Password %s Endpoint %s", username, password, endpoint)
client = MinervaClient(endpoint=endpoint, region=region, userpool=userpool, cognito_client_id=client_id)
client.authenticate(username, password)

if args.command == 'import':
    importer = MinervaImporter(client, uploader=S3Uploader(region="us-east-1"))
    files = FileUtils.list_files(dir, filefilter=[".tif", ".rcpnl"])
    importer.import_files(files=files, repository=repository)

sys.stdout.flush()