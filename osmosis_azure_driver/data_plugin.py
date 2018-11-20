import os
import logging
from datetime import datetime, timedelta
from azure.storage.blob import BlobPermissions
from azure.storage.blob import BlockBlobService
from azure.storage.file import FileService
from azure.common.cloud import get_cli_active_cloud
from azure.mgmt.storage import StorageManagementClient
from azure.mgmt.resource import ResourceManagementClient
from azure.common.credentials import get_azure_cli_credentials, ServicePrincipalCredentials
from osmosis_driver_interface.exceptions import OsmosisError
from osmosis_driver_interface.data_plugin import AbstractPlugin
from osmosis_azure_driver.utils import _parse_url
from osmosis_azure_driver.config import Config

class Plugin(AbstractPlugin):

    def __init__(self, config=None):
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
        # self.resource_group_name = config.get('osmosis', 'azure.resource_group')  # OceanProtocol
        self.config=Config(config)
        self.resource_group_name = self.config.resource_group_name  # OceanProtocol

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

    def list(self, container_or_share_name, container=None, account=None):
        """List the blobs/files inside a container/share_name.
         Args:
             container_or_share_name(str): Name of the container/share_name where we want to list the blobs/files.
             container(bool): flag to know it you are listing files or blobs.
             account(str): The name of the storage account.
        """
        key = self.storage_client.storage_accounts.list_keys(self.resource_group_name, account).keys[0].value
        if container:
            bs = BlockBlobService(account_name=account, account_key=key)
            container_list = []
            for i in bs.list_blobs(container_or_share_name).items:
                container_list.append(i.name)
            return container_list
        elif not container:
            fs = FileService(account_name=account, account_key=key)
            container_list = []
            for i in fs.list_directories_and_files(container_or_share_name).items:
                container_list.append(i.name)
            return container_list
        else:
            raise ValueError("You have to pass a value for container param")

    def generate_url(self, remote_file):
        """Sign a remote file to distribute. The azure url format is https://myaccount.blob.core.windows.net/mycontainer/myblob.
         Args:
             remote_file(str): The blob that we want to sign.
        """
        parse_url = _parse_url(remote_file)
        key = self.storage_client.storage_accounts.list_keys(self.resource_group_name, parse_url.account).keys[0].value
        if parse_url.file_type == 'blob':
            bs = BlockBlobService(account_name=parse_url.account, account_key=key)

            sas_token = bs.generate_blob_shared_access_signature(parse_url.container_or_share_name,
                                                                 parse_url.file,
                                                                 permission=BlobPermissions.READ,
                                                                 expiry=datetime.utcnow() + timedelta(hours=24),
                                                                 )
            source_blob_url = bs.make_blob_url(container_name=parse_url.container_or_share_name,
                                               blob_name=parse_url.file,
                                               sas_token=sas_token)
            return source_blob_url
        elif parse_url.file_type == 'file':
            fs = FileService(account_name=parse_url.account, account_key=key)
            sas_token = fs.generate_file_shared_access_signature(share_name=parse_url.container_or_share_name,
                                                                 directory_name=parse_url.path,
                                                                 file_name=parse_url.file,
                                                                 permission=BlobPermissions.READ,
                                                                 expiry=datetime.utcnow() + timedelta(hours=24),
                                                                 )
            source_file_url = fs.make_file_url(share_name=parse_url.container_or_share_name,
                                               directory_name=parse_url.path,
                                               file_name=parse_url.file,
                                               sas_token=sas_token)
            return source_file_url
        else:
            raise ValueError("This azure storage type is not valid. It should be blob or file.")

    def delete(self, remote_file):
        """Delete file from the cloud. The azure url format is https://myaccount.blob.core.windows.net/mycontainer/myblob.
         Args:
             remote_file(str): The path of the file to be deleted.
         Raises:
             :exc:`~..OsmosisError`: if the file is not uploaded correctly.
        """
        if 'core.windows.net' not in remote_file:
            self.logger.error("Source or destination must be a azure storage url (format "
                              "https://myaccount.blob.core.windows.net/mycontainer/myblob")
            raise OsmosisError
        parse_url = _parse_url(remote_file)
        key = self.storage_client.storage_accounts.list_keys(self.resource_group_name, parse_url.account).keys[0].value
        if parse_url.file_type == 'blob':
            bs = BlockBlobService(account_name=parse_url.account, account_key=key)
            return bs.delete_blob(parse_url.container_or_share_name, parse_url.file)
        elif parse_url.file_type == 'file':
            fs = FileService(account_name=parse_url.account, account_key=key)
            return fs.delete_file(parse_url.container_or_share_name, parse_url.path, parse_url.file)
        else:
            raise ValueError("This azure storage type is not valid. It should be blob or file.")

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
            if parse_url.file_type == 'blob':
                bs = BlockBlobService(account_name=parse_url.account, account_key=key)
                return bs.get_blob_to_path(parse_url.container_or_share_name, parse_url.file, dest_path)
            elif parse_url.file_type == 'file':
                fs = FileService(account_name=parse_url.account, account_key=key)
                return fs.get_file_to_path(parse_url.container_or_share_name, parse_url.path, parse_url.file, dest_path)
            else:
                raise ValueError("This azure storage type is not valid. It should be blob or file.")
        else:
            parse_url = _parse_url(dest_path)
            key = self.storage_client.storage_accounts.list_keys(self.resource_group_name, parse_url.account).keys[
                0].value
            if parse_url.file_type == 'blob':
                bs = BlockBlobService(account_name=parse_url.account, account_key=key)
                return bs.create_blob_from_path(parse_url.container_or_share_name, parse_url.file, source_path)
            elif parse_url.file_type == 'file':
                fs = FileService(account_name=parse_url.account, account_key=key)
                return fs.create_file_from_path(parse_url.container_or_share_name, parse_url.path, parse_url.file,
                                                source_path)
            else:
                raise ValueError("This azure storage type is not valid. It should be blob or file.")

    def create_directory(self, remote_folder, container=None):
        if container:
            return self.create_container(remote_folder)
        elif not container:
            return self.create_share_name()
        else:
            raise ValueError("You have to pass a value for container param")

    def create_container(self, remote_folder):
        parse_url = _parse_url(remote_folder)
        key = self.storage_client.storage_accounts.list_keys(self.resource_group_name, parse_url.account).keys[0].value
        bs = BlockBlobService(account_name=parse_url.account, account_key=key)
        return bs.create_container(container_name=remote_folder)

    def create_share_name(self, remote_folder):
        parse_url = _parse_url(remote_folder)
        key = self.storage_client.storage_accounts.list_keys(self.resource_group_name, parse_url.account).keys[0].value
        fs = FileService(account_name=parse_url.account, account_key=key)
        return fs.create_directory(share_name=parse_url.container_or_share_name, directory_name=parse_url.path)

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
