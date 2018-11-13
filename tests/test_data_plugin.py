from osmosis_driver_interface.osmosis import Osmosis
from osmosis_azure_driver.data_plugin import Plugin
from osmosis_azure_driver.data_plugin import _parse_url
import os

osmo = Osmosis('./tests/osmosis.ini').data_plugin


def test_copy_file():
    assert osmo.type() == 'Azure'


# To run this test you need to login with your credentials through az login
def test_list():
    osmo.upload('./LICENSE', 'https://testocnfiles.blob.core.windows.net/ocn-hackaton/license_copy')
    osmo.download('https://testocnfiles.blob.core.windows.net/ocn-hackaton/license_copy', 'license_copy')
    assert open('license_copy').read() == open('./LICENSE').read()
    assert 'license_copy' in osmo.list('ocn-hackaton', True, 'testocnfiles')
    assert osmo.generate_url('https://testocnfiles.blob.core.windows.net/ocn-hackaton/license_copy')
    osmo.delete('https://testocnfiles.blob.core.windows.net/ocn-hackaton/license_copy')
    os.remove('license_copy')


def test_files_share():
    osmo.upload('./LICENSE', 'https://testocnfiles.file.core.windows.net/osmosis/license_copy')
    osmo.download('https://testocnfiles.file.core.windows.net/osmosis/license_copy', 'license_copy')
    assert open('license_copy').read() == open('./LICENSE').read()
    assert osmo.generate_url('https://testocnfiles.file.core.windows.net/osmosis/license_copy')
    assert 'license_copy' in osmo.list('osmosis', False, 'testocnfiles')
    osmo.delete('https://testocnfiles.file.core.windows.net/osmosis/license_copy')
    os.remove('license_copy')


def test_split_url():
    url = 'https://testocnfiles.blob.core.windows.net/mycontainer/myblob'
    parse_url = _parse_url(url)
    assert parse_url.account == 'testocnfiles'
    assert parse_url.container_or_share_name == 'mycontainer'
    assert parse_url.file == 'myblob'


def test_parse_file_url():
    url = 'https://testocnfiles.file.core.windows.net/compute/subfolder/data.txt'
    parse_url = _parse_url(url)
    assert parse_url.account == 'testocnfiles'
    assert parse_url.container_or_share_name == 'compute'
    assert parse_url.path == 'subfolder'
    assert parse_url.file == 'data.txt'
