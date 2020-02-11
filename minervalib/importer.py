import logging, time, sys
import os, random, string, re
import boto3
import concurrent
from concurrent.futures import ThreadPoolExecutor
from minervalib.client import MinervaClient
from .progress import ProgressPercentage
from .s3 import S3Uploader

class MinervaImporter:

    FILE_FILTER = [".tif", ".tiff", ".rcpnl"]

    def __init__(self, minerva_client: MinervaClient, uploader: S3Uploader, region=None):
        self.minerva_client = minerva_client
        self.uploader = uploader
        self.region = "us-east-1"
        if region is not None:
            self.region = region

    def import_files(self, files, repository=None):
        logging.info("Importing files from dir: %s", dir)
        #files = MinervaImporter._list_files(dir)

        res = self.minerva_client.list_repositories()
        existing_repository = list(filter(lambda x: x["name"] == repository, res["included"]["repositories"]))
        if len(existing_repository) == 0:
            res = self.minerva_client.create_repository(repository)
            repository_uuid = res["data"]["uuid"]
            logging.info("Created new repository, uuid: %s", repository_uuid)
        else:
            repository_uuid = existing_repository[0]["uuid"]
            logging.info("Using existing repository uuid: %s", repository_uuid)

        # Create a random name for import
        import_uuid = self._create_import(repository_uuid)
        # Get AWS credentials for S3 bucket for raw image
        credentials, bucket, prefix = self._get_credentials(import_uuid)
        logging.info("S3 bucket: %s prefix: %s", bucket, prefix)

        # Upload all files in parallel to S3
        self._upload_files(files, bucket, prefix, credentials)

        self.minerva_client.mark_import_complete(import_uuid)

        self._poll_import_progress(import_uuid)
        self._print_results(import_uuid)

    def _create_import(self, repository_uuid):
        import_name = 'I' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=9))
        res = self.minerva_client.create_import(import_name, repository_uuid)
        return res["data"]["uuid"]

    def _get_credentials(self, import_uuid):
        res = self.minerva_client.get_import_credentials(import_uuid)
        m = re.match(r"^s3://([A-z0-9\-]+)/([A-z0-9\-]+/)$", res["data"]["url"])
        bucket = m.group(1)
        prefix = m.group(2)
        credentials = res["data"]["credentials"]
        return credentials, bucket, prefix

    def _upload_files(self, files, bucket, prefix, credentials):
        progress = ProgressPercentage()
        with ThreadPoolExecutor() as executor:
            for file in files:
                extension = os.path.splitext(file)[1]
                filename = os.path.splitext(file)[0]
                key = prefix + '/' + extension + '/' + filename

                future = executor.submit(self.uploader.upload, file, bucket, key, credentials, progress)

    def _poll_import_progress(self, import_uuid):
        all_complete = False
        logging.info("\nWaiting for filesets...")
        while not all_complete:
            result = self.minerva_client.list_filesets_in_import(import_uuid)
            filesets = result["data"]
            if len(filesets) > 0:
                all_complete = True
                progresses = []
                for fileset in filesets:
                    all_complete = all_complete and fileset["complete"]
                    progress = fileset["progress"] if fileset["progress"] is not None else 0
                    progresses.append((fileset, progress))

                MinervaImporter._print_progress(progresses)

            if not all_complete:
                time.sleep(2)

    @staticmethod
    def _print_progress(progresses):
        if len(progresses) == 0:
            return

        sys.stdout.write("\rProcessing filesets: ")
        for p in progresses:
            fileset = p[0]
            progress = p[1]
            sys.stdout.write("{} {}%".format(fileset["name"], progress))

    def _print_results(self, import_uuid):
        logging.info("\n")
        result = self.minerva_client.list_filesets_in_import(import_uuid)
        for fileset in result["data"]:
            result = self.minerva_client.list_images_in_fileset(fileset["uuid"])
            for image in result["data"]:
                logging.info(image)
