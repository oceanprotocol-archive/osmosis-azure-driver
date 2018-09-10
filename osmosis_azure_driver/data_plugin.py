import os
import logging
from collections import namedtuple
from datetime import datetime, timedelta
from azure.storage.blob import BlobPermissions
from azure.storage.blob import BlockBlobService
from azure.common.cloud import get_cli_active_cloud
from azure.mgmt.storage import StorageManagementClient
from azure.mgmt.resource import ResourceManagementClient
from azure.common.credentials import get_azure_cli_credentials
from osmosis_driver_interface.exceptions import OsmosisError
from osmosis_driver_interface.data_plugin import AbstractPlugin

azure_parameters = namedtuple('Azure', ['account', 'container', 'blob'])


class Plugin(AbstractPlugin):

    def __init__(self, resource_group_name=None, config=None):
        """Initialize a :class:`~.Plugin`.
        """
        self.logger = logging.getLogger('Plugin')
        logging.basicConfig(level=logging.INFO)
        try:
            subscription_id = os.environ.get(
                'AZURE_SUBSCRIPTION_ID',
                self._get_azure_cli_credentials()['subscription_id'])
            credentials = self._get_azure_cli_credentials()['credentials']
            # Create a Resource Management client
            self.resource_client = ResourceManagementClient(credentials, subscription_id)
            self.storage_client = StorageManagementClient(credentials, subscription_id)
        except Exception:
            logging.error('Credentials were not valid or were not found.')
            raise OsmosisError

        self.resource_group_name = resource_group_name  # OceanProtocol

    def type(self):
        """str: the type of this plugin (``'Azure'``)"""
        return "Azure"

    def upload(self, local_file, remote_file):
        """
        :param local_file:
        :param remote_file:
        :return:
        """
        return self.copy(local_file, remote_file)

    def download(self, remote_file, local_file):
        """
        :param remote_file:
        :param local_file:
        :return:
        """
        return self.copy(remote_file, local_file)

    def list(self, container, account=None):
        key = self.storage_client.storage_accounts.list_keys(self.resource_group_name, account).keys[0].value
        bs = BlockBlobService(account_name=account, account_key=key)
        container_list = []
        for i in bs.list_blobs(container).items:
            container_list.append(i.name)
        return container_list

    def generate_url(self, remote_file):
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
        if 'blob.core.windows.net' not in remote_file:
            self.logger.error("Source or destination must be a azure storage url (format "
                              "https://myaccount.blob.core.windows.net/mycontainer/myblob")
            raise OsmosisError
        parse_url = _parse_url(remote_file)
        key = self.storage_client.storage_accounts.list_keys(self.resource_group_name, parse_url.account).keys[0].value
        bs = BlockBlobService(account_name=parse_url.account, account_key=key)
        return bs.delete_blob(parse_url.container, parse_url.blob)

    def copy(self, source_path, dest_path, account=None, group_name=None):
        """Copy file from a path to another path.
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

    def _get_azure_cli_credentials(self):
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
