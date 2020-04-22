import argparse, configparser
import sys, logging, os

from minerva_lib.importing import MinervaImporter
from minerva_lib.client import MinervaClient, InvalidUsernameOrPassword, InvalidCognitoClientId
from minerva_lib.util.s3 import S3Uploader
from minerva_lib.util.fileutils import FileUtils
import tabulate

FILE_FILTER = [".tif", ".rcpnl", ".dv"]
TILE_PATTERN = "C\\d+-T\\d+-Z\\d+-L\\d+-Y\\d+-X\\d+\\.png"

root = logging.getLogger()
logging_level = logging.DEBUG if "--debug" in sys.argv else logging.INFO
FORMAT = '%(asctime)-15s %(message)s'
logging.basicConfig(stream=sys.stdout, level=logging_level, format=FORMAT)

class Configuration:
    def __init__(self, repository=None, directory=None, archive=None, image_name=None):
        self.repository = repository
        self.directory = directory
        self.archive = archive
        self.image_name = image_name

def check_required_arguments(args):
    exit = False
    for arg in args:
        if arg[0] is None:
            exit = True
            print("Argument missing:", arg[1])

    if exit:
        sys.exit(1)

def parse_arguments():
    epilog = """
Importing images: \tminerva import -r repository -d /directory
Importing tiles:  \tminerva direct -r repository -d /directory -n image_name
 - Tiles' filenames must be in format C0-T0-Z0-L0-Y0-X0.png
 - Image format must be 16-bit grayscale PNG
List repositories: \tminerva list
Show import status: \tminerva status
    """
    parser = argparse.ArgumentParser(prog="minerva",
                                     description='Minerva Command Line Interface v1.0',
                                     epilog=epilog,
                                     formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument('command', choices=["import", "direct", "list", "status"], type=str,
                        help='[import=Import images, Direct=Direct import, list=List repositories, status=Fileset status]')
    parser.add_argument('--config', type=str,
                        help='Config file')
    parser.add_argument('--dir', '-d', type=str,
                        help='Import directory', default='.')
    parser.add_argument('--username', type=str,
                        help='Username')
    parser.add_argument('--password', type=str,
                        help='Password')
    parser.add_argument('--endpoint', type=str,
                        help='Minerva endpoint')
    parser.add_argument('--region', type=str,
                        help='AWS region')
    parser.add_argument('--repository', '-r', type=str,
                        help='Repository name')
    parser.add_argument('--client_id', type=str,
                        help='Cognito ClientId')
    parser.add_argument('--imagename', '-n', type=str, help='Image name (direct import)')
    parser.add_argument('--archive', action='store_const', const=True, help='Archive original images', default=False)
    parser.add_argument('--debug', action='store_const', const=True, help='Debug logging on')

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    return parser.parse_args()

def print_results(client, import_uuid):
    print("\n")
    result = client.list_filesets_in_import(import_uuid)
    for fileset in result["data"]:
        result = client.list_images_in_fileset(fileset["uuid"])
        print(tabulate.tabulate(result["data"], headers="keys"))
        print("\n")

def create_minerva_client(endpoint, region, client_id, username, password):
    client = MinervaClient(endpoint=endpoint, region=region, cognito_client_id=client_id)
    try:
        client.authenticate(username, password)
    except InvalidUsernameOrPassword as e:
        logging.error("Incorrect username or password.")
        sys.exit(1)
    except InvalidCognitoClientId as e:
        logging.error("Check the value for CognitoClient!")
        sys.exit(1)
    return client

def execute_command(command, client, configuration):
    command = command.lower()
    if command == 'import':
        check_required_arguments([configuration.repository, "Repository"])
        FileUtils.validate_name(configuration.repository, "Repository")
        logging.info("Importing files from directory: %s", configuration.directory)
        importer = MinervaImporter(client, uploader=S3Uploader(region="us-east-1"))
        files = FileUtils.list_files(configuration.directory, filefilter=FILE_FILTER)
        if len(files) == 0:
            logging.info("No image files found in directory %s", configuration.directory)
            sys.exit(0)

        import_uuid = importer.import_files(files=files, repository=configuration.repository)
        importer.poll_import_progress(import_uuid)
        print_results(client, import_uuid)

    elif command == 'direct':
        check_required_arguments([configuration.repository, "Repository"])
        FileUtils.validate_name(configuration.repository, "Repository")
        logging.info("Direct import of files from directory: %s", configuration.directory)
        importer = MinervaImporter(client, uploader=S3Uploader(region="us-east-1"))
        files = FileUtils.list_files_regex(configuration.directory, pattern=TILE_PATTERN)
        if len(files) == 0:
            logging.info("No tiles found in directory %s", configuration.directory)
            sys.exit(0)

        metadata_file = os.path.join(configuration.directory, 'metadata.xml')
        if not os.path.exists(metadata_file):
            raise ValueError('No metadata.xml found in directory ' + configuration.directory)

        FileUtils.validate_tiles(files)
        pyramid_levels = FileUtils.get_pyramid_levels(files)
        image_uuid = importer.create_image(repository=configuration.repository, name=configuration.image_name, pyramid_levels=pyramid_levels)

        with open(metadata_file, 'r') as f:
            metadata = f.read()
            importer.direct_import_metadata(metadata, image_uuid)

        importer.direct_import_files(files, image_uuid=image_uuid, async_upload=True)
        importer.wait_upload()

        logging.info("Image uuid: %s", image_uuid)

    elif command == 'list':
        logging.info("Listing repositories:")
        result = client.list_repositories()
        repositories = result["included"]["repositories"]
        for repo in repositories:
            for grant in result["data"]:
                if grant["repository_uuid"] == repo["uuid"]:
                    repo["permission"] = grant["permission"]

        print(tabulate.tabulate(repositories, headers="keys"))

    elif command == 'status':
        result = client.list_incomplete_imports()
        if len(result["data"]) == 0:
            logging.info("No imports are processing currently.")
        else:
            logging.info("Following filesets are currently processing:")
            print(tabulate.tabulate(result["included"]["filesets"], headers="keys"))

def main():
    args = parse_arguments()
    config = args.config
    directory = args.dir
    archive = args.archive
    repository = args.repository
    image_name = args.imagename
    # Load minerva.config by default if no other config-file was specified by user
    if config is None and os.path.isfile("minerva.config"):
        config = "minerva.config"

    if config is not None:
        logging.info("Using config file: %s", config)
        cp = configparser.ConfigParser()
        cp.read(config)
        username = cp.get('Minerva', 'Username')
        password = cp.get('Minerva', 'Password')
        endpoint = cp.get('Minerva', 'Endpoint')
        client_id = cp.get('Minerva', 'CognitoClient')
        region = cp.get('Minerva', 'Region')

    username = args.username or username
    password = args.password or password
    endpoint = args.endpoint or endpoint
    region = args.region or region
    client_id = args.client_id or client_id

    check_required_arguments(
        [(username, "Username"), (password, "Password"), (endpoint, "Endpoint"), (region, "Region"),
         (client_id, "CognitoClient")])

    client = create_minerva_client(endpoint=endpoint, region=region, client_id=client_id, username=username, password=password)
    configuration = Configuration(repository=repository, directory=directory, archive=archive, image_name=image_name)
    execute_command(args.command, client, configuration)


if __name__ == "__main__":
    main()
