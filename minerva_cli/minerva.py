#!/usr/bin/env python

"""
Minerva Command Line Client
"""
import argparse, configparser
import sys, logging, os
import pathlib
from uuid import UUID

from . import __version__
from minerva_cli.util.configurer import Configurer
from minerva_lib.importing import MinervaImporter
from minerva_lib.exporting import MinervaExporter
from minerva_lib.client import MinervaClient, InvalidUsernameOrPassword, InvalidCognitoClientId
from minerva_lib.util.s3 import S3Uploader
from minerva_lib.util.fileutils import FileUtils
from tqdm import tqdm
import tabulate

BATCH_IMPORT_FILE_FILTER = [".tif", ".rcpnl", ".dv"]
LOCAL_IMPORT_FILE_FILTER = [".tif"]
TILE_PATTERN = "C\\d+-T\\d+-Z\\d+-L\\d+-Y\\d+-X\\d+\\.png"

logger = logging.getLogger("minerva")
logging_level = logging.DEBUG if "--debug" in sys.argv else logging.WARNING
minerva_logging_level = logging.DEBUG if "--debug" in sys.argv else logging.INFO
FORMAT = '%(asctime)-15s %(levelname)-8s - %(message)s'
logging.basicConfig(stream=sys.stdout, level=logging_level, format=FORMAT)
logging.getLogger('minerva').setLevel(minerva_logging_level)

if "--dryrun" in sys.argv:
    logger.info("DRY RUN")

class Configuration:
    def __init__(self, repository=None, directory=None, file=None, archive=None, image_name=None, image_uuid=None, output=None, save_pyramid=False, dryrun=False, local_import=False, export_format="zarr", region="us-east-1"):
        self.repository = repository
        self.directory = directory
        self.file = file
        self.archive = archive
        self.image_name = image_name
        self.image_uuid = image_uuid
        self.output = output
        self.save_pyramid = save_pyramid
        self.dryrun = dryrun
        self.local_import = local_import
        self.export_format = export_format
        self.region = region

def check_required_arguments(args):
    exit = False
    for arg in args:
        if not arg[0]:
            exit = True
            print("Missing variable:", arg[1])

    if exit:
        sys.exit(1)

def parse_arguments():
    epilog = """
Examples:
Import whole directory: minerva import -r REPOSITORY_NAME -d /directory
Import single file: \tminerva import -r REPOSITORY_NAME -f /path/file
(When importing only OME-TIFFs, --local flag can be used to optimize the process)
Export image: \t\tminerva export --id IMAGE_UUID
List repositories: \tminerva repositories
List images: \t\tminerva images -r REPOSITORY_NAME
Show import status: \tminerva status
Configure Minerva CLI:\tminerva configure
    """
    parser = argparse.ArgumentParser(prog="minerva",
                                     description='Minerva Command Line Interface ' + __version__,
                                     epilog=epilog,
                                     formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument('command', choices=["import", "export", "repositories", "status", "configure", "images"], type=str,
                        help='[import=Import images, export=Export image, repositories=List repositories, images=List images, status=Show import status, configure=Configure]')
    parser.add_argument('--config', type=str,
                        help='Config file')
    parser.add_argument('--dir', '-d', type=str,
                        help='Import directory')
    parser.add_argument('--file', '-f', type=str,
                        help='Import file', default='')
    parser.add_argument('--endpoint', type=str,
                        help='Minerva endpoint')
    parser.add_argument('--region', type=str,
                        help='AWS region')
    parser.add_argument('--repository', '-r', type=str,
                        help='Repository name')
    parser.add_argument('--client_id', type=str,
                        help='Cognito ClientId')
    parser.add_argument('--id', type=str,
                        help='Image uuid (for export)')
    parser.add_argument('--output', '-o', type=str,
                        help='Output path (for export)')
    parser.add_argument('--format', choices=["zarr", "tif", "tiff"],
                        help='Export format')
    parser.add_argument('--pyramid', '-p', dest='pyramid', action='store_true',
                        help='Save pyramid (for export)')
    parser.add_argument('--imagename', '-n', type=str, help='Image name (direct import)')
    parser.add_argument('--local', '-l', action='store_const', const=True, help='Use local import', default=False)
    parser.add_argument('--archive', action='store_const', const=True, help='Archive original images', default=False)
    parser.add_argument('--debug', action='store_const', const=True, help='Debug logging on')
    parser.add_argument('--dryrun', action='store_const', const=True, help='Dry run', default=False)

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
        logger.error("Incorrect username or password.")
        sys.exit(1)
    except InvalidCognitoClientId as e:
        logger.error("Check the value for CognitoClient!")
        sys.exit(1)
    return client

def execute_command(command, client, cfg):
    command = command.lower()
    if command == 'import':
        return _import(cfg, client)

    elif command == 'repositories':
        logger.info("Listing repositories:")
        result = client.list_repositories()
        repositories = result["included"]["repositories"]
        for repo in repositories:
            for grant in result["data"]:
                if grant["repository_uuid"] == repo["uuid"]:
                    repo["permission"] = grant["permission"]

        print(tabulate.tabulate(repositories, headers="keys"))

    elif command == 'images':
        logger.info("Listing images:")
        if not cfg.repository:
            logger.error("Need to pass repository with -r repository_name")
            return -1
        res = client.list_repositories()
        existing_repository = list(filter(lambda x: x["name"] == cfg.repository, res["included"]["repositories"]))
        if not existing_repository or len(existing_repository) == 0:
            logger.error("Repository %s not found", cfg.repository)
            return -1
        repository_uuid = existing_repository[0]["uuid"]
        result = client.list_images_in_repository(repository_uuid)
        print(tabulate.tabulate(result["data"], headers="keys"))

    elif command == 'status':
        logger.info("Showing import status:")
        result = client.list_incomplete_imports()
        if len(result["data"]) == 0:
            logger.info("No imports are processing currently.")
        else:
            logger.info("Following filesets are currently processing:")
            print(tabulate.tabulate(result["included"]["filesets"], headers="keys"))

    elif command == 'export':
        return export(cfg, client)

    elif command == 'configure':
        configurer = Configurer()
        configurer.interactive_config()

    return 0

def _get_files(file_or_directory: str, filefilter=None):
    files = []
    if file_or_directory != '' and os.path.isdir(file_or_directory):
        files += (FileUtils.list_files(file_or_directory, filefilter=filefilter))
    else:
        files.append(file_or_directory)
    return files

def _import(cfg, client):
    if not cfg.file and not cfg.directory:
        logger.error("Define either a directory with -d or file with -f to import.")
        return -1

    FileUtils.validate_name(cfg.repository, "Repository")

    file_or_directory = cfg.directory if len(cfg.file) == 0 else cfg.file
    filefilter = LOCAL_IMPORT_FILE_FILTER if cfg.local_import else BATCH_IMPORT_FILE_FILTER
    files = _get_files(file_or_directory, filefilter=filefilter)
    if len(files) == 0:
        logger.error("No files found.")
        return -1

    if cfg.local_import:
        logger.info("Processing images locally.")
        return _local_import(cfg, client, files)
    else:
        logger.info("Images are sent to cloud for processing.")
        return _batch_import(cfg, client, files)

def _batch_import(cfg, client, files):
    """
    Batch import uploads the original image files into S3 raw bucket,
    and starts an AWS Batch Job to process the images.
    """
    check_required_arguments([cfg.repository, "Repository"])

    if cfg.directory:
        logger.info("Importing files from directory: %s", cfg.directory)
    else:
        logger.info("Importing file: %s", cfg.file)

    importer = MinervaImporter(client, uploader=S3Uploader(region=cfg.region), dryrun=cfg.dryrun)

    import_uuid = importer.import_files(files=files, repository=cfg.repository)
    importer.poll_import_progress(import_uuid)
    print_results(client, import_uuid)
    return 0

def _local_import(cfg, client, files):
    """
    Local import process the images on local machine,
    after which the tiles are uploaded into S3 tile bucket.
    """
    check_required_arguments([(cfg.repository, "Repository")])

    importer = MinervaImporter(client, uploader=S3Uploader(region=cfg.region), dryrun=cfg.dryrun)

    status_code = 0
    for file in files:
        if not os.path.exists(file):
            logger.warning("File does not exist: %s", file)
            return -1

        if not os.path.basename(file).endswith(".ome.tif"):
            logger.warning("Only OME-TIFFs can be imported with local import.")
            logger.warning("Skipping file %s", file)
            continue

        logger.info("Importing file %s", file)
        with tqdm(unit="tiles") as pbar:
            def show_progress(processed, total):
                pbar.total = total
                pbar.update(1)

            try:
                importer.import_ome_tiff(file, repository=cfg.repository, progress_callback=show_progress)
            except Exception as e:
                status_code = -1
                raise e

    return status_code

def export(cfg, client):
    """
    Export downloads all the tiles from S3 tile bucket, and reconstructs an OME-TIFF file with metadata.
    """
    exporter = MinervaExporter(cfg.region)

    if cfg.image_uuid is None:
        logger.error("Image uuid has to be specified with argument --id")
        return -1
    logger.info("Exporting image uuid: %s (pyramid=%s)", cfg.image_uuid, cfg.save_pyramid)
    try:
        uuid_obj = UUID(cfg.image_uuid, version=4)
        with tqdm(unit="tiles") as pbar:
            def show_progress(processed, total):
                pbar.total = total
                pbar.update(1)

            output = exporter.export_image(client, str(uuid_obj), cfg.output, save_pyramid=cfg.save_pyramid, progress_callback=show_progress, format=cfg.export_format)

        logger.info("Image saved as %s", output)

    except ValueError:
        logger.error("%s is not a valid UUID", cfg.image_uuid)
        return -1
    except Exception as e:
        logger.error(e)
        return -1

    return 0

def main():
    args = parse_arguments()
    if args.command == "configure":
        return execute_command(args.command, None, None)

    config = args.config
    # Load .minerva from home directory by default, if no other config-file was specified by user
    if config is None:
        config = os.path.join(pathlib.Path.home(), ".minerva")

    if not os.path.isfile(config):
        logger.error("Configuration file not found: %s", config)
        logger.info("Run \"minerva configure\"")
        return -1

    username = None
    password = None
    endpoint = None
    client_id = None
    region = None

    if config is not None:
        logger.info("Reading config file: %s", config)
        cp = configparser.ConfigParser()
        cp.read(config)
        username = cp.get('Minerva', 'MINERVA_USERNAME', fallback=None)
        password = cp.get('Minerva', 'MINERVA_PASSWORD', fallback=None)
        endpoint = cp.get('Minerva', 'MINERVA_ENDPOINT', fallback=None)
        client_id = cp.get('Minerva', 'MINERVA_CLIENT_ID', fallback=None)
        region = cp.get('Minerva', 'MINERVA_REGION', fallback=None)
    else:
        logger.warning("No config file found.")

    username = os.environ.get('MINERVA_USERNAME', username)
    password = os.environ.get('MINERVA_PASSWORD', password)
    endpoint = os.environ.get('MINERVA_ENDPOINT', endpoint)
    client_id = os.environ.get('MINERVA_CLIENT_ID', client_id)
    region = os.environ.get('MINERVA_REGION', region)

    endpoint = args.endpoint or endpoint
    region = args.region or region
    client_id = args.client_id or client_id

    check_required_arguments(
        [(username, "MINERVA_USERNAME"), (password, "MINERVA_PASSWORD"), (endpoint, "MINERVA_ENDPOINT"), (region, "MINERVA_REGION"),
         (client_id, "MINERVA_CLIENT_ID")])

    client = create_minerva_client(endpoint=endpoint, region=region, client_id=client_id, username=username, password=password)
    configuration = Configuration(repository=args.repository,
                                  directory=args.dir,
                                  file=args.file,
                                  archive=args.archive,
                                  image_name=args.imagename,
                                  image_uuid=args.id,
                                  output=args.output,
                                  save_pyramid=args.pyramid,
                                  dryrun=args.dryrun,
                                  local_import=args.local,
                                  export_format=args.format,
                                  region=region)
    status = execute_command(args.command, client, configuration)
    return status


if __name__ == "__main__":
    status = main()
    if status == 0:
        logger.info("Success")
    else:
        logger.error("There was an error.")
    sys.exit(status)
