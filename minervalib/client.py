import boto3
import logging
import requests
import json
from requests import Request

class MinervaClient:
    def __init__(self, endpoint, region, userpool, cognito_client_id):
        self.endpoint = endpoint
        self.region = region
        self.cognito_client_id = cognito_client_id
        self.id_token = None
        self.token_type = None
        self.refresh_token = None
        self.session = None

    def authenticate(self, username, password):
        logging.info("Logging in as %s", username)
        client = boto3.client('cognito-idp')
        response = client.initiate_auth(
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': username,
                'PASSWORD': password
            },
            ClientId=self.cognito_client_id
        )
        self.id_token = response["AuthenticationResult"]["IdToken"]
        self.token_type = response["AuthenticationResult"]["TokenType"]
        self.refresh_token = response["AuthenticationResult"]["RefreshToken"]
        logging.debug("Authenticated successfully")

    def request(self, method, path, body=None, parameters=None):
        if self.session is None:
            self.session = requests.Session()

        self.session.headers.update({
            "Authorization": self.token_type + " " + self.id_token,
            "Content-Type": "application/json"
        })
        url = self.endpoint + path

        if body is not None:
            body = json.dumps(body)

        response = self.session.request(method=method, url=url, data=body, params=parameters)

        if response.status_code >= 400:
            logging.error(response.text)

        response.raise_for_status()
        logging.debug(response)
        return response.json()

    def list_repositories(self):
        return self.request('GET', '/repository')

    def create_repository(self, name, raw_storage="Destroy"):
        body = {
            "name": name,
            "raw_storage": raw_storage
        }
        return self.request('POST', '/repository', body)

    def create_import(self, name, repository_uuid):
        body = {
            "name": name,
            "repository_uuid": repository_uuid
        }
        return self.request('POST', '/import', body)

    def get_import_credentials(self, import_uuid):
        return self.request('GET', '/import/' + import_uuid + '/credentials')

    def mark_import_complete(self, import_uuid):
        body = {
            "complete": True
        }
        return self.request('PUT', '/import/' + import_uuid, body)

    def list_filesets_in_import(self, import_uuid):
        return self.request('GET', '/import/' + import_uuid + '/filesets')

    def list_images_in_fileset(self, fileset_uuid):
        return self.request('GET', '/fileset/' + fileset_uuid + '/images')

    def get_image_dimensions(self, image_uuid):
        return self.request('GET', '/image/' + image_uuid + '/dimensions')



