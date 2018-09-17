import os
import logging
from collections import namedtuple
from datetime import datetime, timedelta
from azure.storage.blob import BlobPermissions
from azure.storage.blob import BlockBlobService
from azure.common.cloud import get_cli_active_cloud
from azure.mgmt.storage import StorageManagementClient
from azure.mgmt.resource import ResourceManagementClient
from azure.common.credentials import get_azure_cli_credentials, ServicePrincipalCredentials
from osmosis_driver_interface.exceptions import OsmosisError
from osmosis_driver_interface.data_plugin import AbstractPlugin

azure_parameters = namedtuple('Azure', ['account', 'container', 'blob'])


class Plugin(AbstractPlugin):

    def __init__(self, config=None, resource_group_name=None):
        """Initialize a :class:`~.Plugin`.
        """
        self.logger = logging.getLogger('Plugin')
        logging.basicConfig(level=logging.INFO)
        try:

            subscription_id = os.environ.get('AZURE_SUBSCRIPTION_ID')
            credentials = self._login_azure_app_token()
            # Create a Resource Management client
            self.resource_client = ResourceManagementClient(credentials, subscription_id)
            self.storage_client = StorageManagementClient(credentials, subscription_id)
        except Exception:
            logging.error('Credentials were not valid or were not found.')
            raise OsmosisError

        self.resource_group_name = resource_group_name  # OceanProtocol

    @staticmethod
    def _login_azure_app_token(client_id=None, client_secret=None, tenant_id=None):
        """
        Authenticate APP using token credentials:
        https://docs.microsoft.com/en-us/python/azure/python-sdk-azure-authenticate?view=azure-python
        :return: ~ServicePrincipalCredentials credentials
        """
        client_id = os.getenv('AZURE_CLIENT_ID') if not client_id else client_id
        client_secret = os.getenv('AZURE_CLIENT_SECRET') if not client_secret else client_secret
        tenant_id = os.getenv('AZURE_TENANT_ID') if not tenant_id else tenant_id
        credentials = ServicePrincipalCredentials(
            client_id=client_id,
            secret=client_secret,
            tenant=tenant_id,
        )
        return credentials

    def _login_azure_cli(self):
        """
        Authenticate APP using az cli interactive login:
        https://docs.microsoft.com/en-us/python/azure/python-sdk-azure-authenticate?view=azure-python
        :return: credentials
        """
        return self._get_azure_cli_credentials()['credentials']

    def type(self):
        """str: the type of this plugin (``'Azure'``)"""
        return "Azure"

    def upload(self, local_file, remote_file):
        """Upload file to the cloud. The azure url format is https://myaccount.blob.core.windows.net/mycontainer/myblob.
         Args:
             local_file(str): The path of the file to be copied.
             remote_file(str): The destination path where the file is going to be allocated.
         Raises:
             :exc:`~..OsmosisError`: if the file is not uploaded correctly.
        """
        return self.copy(local_file, remote_file)

    def download(self, remote_file, local_file):
        """Download file from the cloud. The azure url format is https://myaccount.blob.core.windows.net/mycontainer/myblob.
         Args:
             remote_file(str): The path of the file to be copied.
             local_file(str): The destination path where the file is going to be allocated.
         Raises:
             :exc:`~..OsmosisError`: if the file is not downloaded correctly.
        """
        return self.copy(remote_file, local_file)

    def list(self, container, account=None):
        """List the blobs inside a container.
         Args:
             container(str): Name of the container where we want to list the blobs.
             account(str): The name of the storage account.
        """
        key = self.storage_client.storage_accounts.list_keys(self.resource_group_name, account).keys[0].value
        bs = BlockBlobService(account_name=account, account_key=key)
        container_list = []
        for i in bs.list_blobs(container).items:
            container_list.append(i.name)
        return container_list

    def generate_url(self, remote_file):
        """Sign a remote file to distribute. The azure url format is https://myaccount.blob.core.windows.net/mycontainer/myblob.
         Args:
             remote_file(str): The blob that we want to sign.
        """
        parse_url = _parse_url(remote_file)
        key = self.storage_client.storage_accounts.list_keys(self.resource_group_name, parse_url.account).keys[0].value
        bs = BlockBlobService(account_name=parse_url.account, account_key=key)

        sas_token = bs.generate_blob_shared_access_signature(parse_url.container,
                                                             parse_url.blob,
                                                             permission=BlobPermissions.READ,
                                                             expiry=datetime.utcnow() + timedelta(hours=24),
                                                             )
        source_blob_url = bs.make_blob_url(parse_url.container, parse_url.blob,
                                           sas_token=sas_token)
        return source_blob_url

    def delete(self, remote_file):
        """Delete file from the cloud. The azure url format is https://myaccount.blob.core.windows.net/mycontainer/myblob.
         Args:
             remote_file(str): The path of the file to be deleted.
         Raises:
             :exc:`~..OsmosisError`: if the file is not uploaded correctly.
        """
        if 'blob.core.windows.net' not in remote_file:
            self.logger.error("Source or destination must be a azure storage url (format "
                              "https://myaccount.blob.core.windows.net/mycontainer/myblob")
            raise OsmosisError
        parse_url = _parse_url(remote_file)
        key = self.storage_client.storage_accounts.list_keys(self.resource_group_name, parse_url.account).keys[0].value
        bs = BlockBlobService(account_name=parse_url.account, account_key=key)
        return bs.delete_blob(parse_url.container, parse_url.blob)

    def copy(self, source_path, dest_path, account=None, group_name=None):
        """Copy file from a path to another path. The azure url format is https://myaccount.blob.core.windows.net/mycontainer/myblob.
         Args:
             source_path(str): The path of the file to be copied.
             dest_path(str): The destination path where the file is going to be allocated.
         Raises:
             :exc:`~..OsmosisError`: if the file is not uploaded correctly.
        """
        if 'core.windows.net' not in source_path and 'core.windows.net' not in dest_path:
            self.logger.error("Source or destination must be a azure storage url (format "
                              "https://myaccount.blob.core.windows.net/mycontainer/myblob")
            raise OsmosisError

        # Check if source exists and can read
        if 'core.windows.net' in source_path:
            parse_url = _parse_url(source_path)
            key = self.storage_client.storage_accounts.list_keys(self.resource_group_name, parse_url.account).keys[
                0].value
            bs = BlockBlobService(account_name=parse_url.account, account_key=key)
            return bs.get_blob_to_path(parse_url.container, parse_url.blob, dest_path)
        else:
            parse_url = _parse_url(dest_path)
            key = self.storage_client.storage_accounts.list_keys(self.resource_group_name, parse_url.account).keys[
                0].value
            bs = BlockBlobService(account_name=parse_url.account, account_key=key)
            return bs.create_blob_from_path(parse_url.container, parse_url.blob, source_path)

    def create_directory(self, remote_folder):
        parse_url = _parse_url(remote_folder)
        key = self.storage_client.storage_accounts.list_keys(self.resource_group_name, parse_url.account).keys[0].value
        bs = BlockBlobService(account_name=parse_url.account, account_key=key)
        return bs.create_container(container_name=remote_folder)

    def retrieve_availability_proof(self):
        pass

    @staticmethod
    def _get_azure_cli_credentials():
        credentials, subscription_id = get_azure_cli_credentials()
        cloud_environment = get_cli_active_cloud()

        cli_credentials = {
            'credentials': credentials,
            'subscription_id': subscription_id,
            'cloud_environment': cloud_environment
        }
        return cli_credentials


def _parse_url(url):
    account = url[8:].split('/')[0].split('.')[0]
    container = url[8:].split('/')[1]
    blob = url[8:].split('/')[2]
    # if account != self.account:
    #     self.logger.error('This url has a wrong account.')
    #     raise OsmosisError

    return azure_parameters(account, container, blob)
