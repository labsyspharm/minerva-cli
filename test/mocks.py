import boto3
import logging
import requests
import json
import time
from requests import Request
from minervalib.progress import ProgressPercentage

class MinervaMockClient:

    def __init__(self):
        self.repository_uuid = "4fa9e42c-3591-40e7-923a-6cbd24ba8260"
        self.import_uuid = "d362cb3d-7ea2-4301-be25-9b425cc868dc"
        pass

    def authenticate(self, username, password):
        logging.info("Logging in as %s", username)
        pass
        logging.debug("Authenticated successfully")

    def request(self, method, path, body=None, parameters=None):
        pass

    def list_repositories(self):
        return self._response([], {"repositories": []})

    def create_repository(self, name, raw_storage="Destroy"):
        return self._response({"uuid": self.repository_uuid})

    def create_import(self, name, repository_uuid):
        return self._response({"uuid": self.import_uuid})

    def get_import_credentials(self, import_uuid):
        return self._response({"url": "s3://minerva-env-cf-common-rawbucket-150oo74l2k58b/633de874-31a6-4a13-b09f-2928a8491b9a/",
                               "credentials": {
                                   "AccessKeyId": "FakeAccessKeyId",
                                   "SecretAccessKey": "FakeSecretAccessKey",
                                   "SessionToken": "FakeSessionToken",
                                   "Expiration": "2020-02-11T20:06:04+00:00"
                               }})

    def mark_import_complete(self, import_uuid):
        return self._response({})

    def list_filesets_in_import(self, import_uuid):
        return self._response([{"uuid": "776d35d5-d33e-4fc9-bb67-9b9696a29736", "name": "Fakename", "complete": True, "progress": 100}])

    def list_images_in_fileset(self, fileset_uuid):
        # TODO
        return self._response([])

    def get_image_dimensions(self, image_uuid):
        # TODO
        return self._response([])

    def _response(self, data, included={}):
        return {"data": data, "included": included}

class MockS3Uploader:
    def __init__(self):
        self.region = "us-earth-1"

    def upload(self, filepath, bucket, object_name, credentials, callback: ProgressPercentage):
        time.sleep(0.1)
