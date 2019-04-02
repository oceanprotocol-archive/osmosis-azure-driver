#  Copyright 2018 Ocean Protocol Foundation
#  SPDX-License-Identifier: Apache-2.0

from collections import namedtuple

azure_parameters = namedtuple('Azure', ['account', 'file_type', 'container_or_share_name', 'path', 'file'])


def _parse_url(url):
    account = url[8:].split('/')[0].split('.')[0]
    file_type = url[8:].split('/')[0].split('.')[1]
    # TODO Modify to manage directory trees.
    container_or_share_name = url[8:].split('/')[1]
    path = None if url[8:].split('/')[2] == url[8:].split('/')[-1] else url[8:].split('/')[2]
    file = url[8:].split('/')[-1]
    # if account != self.account:
    #     self.logger.error('This url has a wrong account.')
    #     raise OsmosisError

    return azure_parameters(account, file_type, container_or_share_name, path, file)
