from osmosis_driver_interface.osmosis import Osmosis
from osmosis_azure_driver.data_plugin import _parse_url
import os

# osmo = Osmosis('./tests/osmosis.ini').data_plugin()
#
#
# def test_copy_file():
#     assert osmo.type() == 'Azure'

# To run this test you need to login with your credentials through az login
# def test_list():
#     pl = Plugin(resource_group_name='OceanProtocol')
#     pl.upload('./LICENSE', 'https://testocnfiles.blob.core.windows.net/ocn-hackaton/license')
#     pl.download('https://testocnfiles.blob.core.windows.net/ocn-hackaton/license', 'license')
#     assert open('license').read() == open('./LICENSE').read()
#     print(pl.list('ocn-hackaton','testocnfiles'))
#     pl.delete('https://testocnfiles.blob.core.windows.net/ocn-hackaton/license')
#     os.remove('license')


def test_split_url():
    url = 'https://testocnfiles.blob.core.windows.net/mycontainer/myblob'
    parse_url = _parse_url(url)
    assert parse_url.account == 'testocnfiles'
    assert parse_url.container == 'mycontainer'
    assert parse_url.blob == 'myblob'
