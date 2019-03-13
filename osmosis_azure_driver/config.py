#  Copyright 2018 Ocean Protocol Foundation
#  SPDX-License-Identifier: Apache-2.0

import os


class Config(object):
    def __init__(self, config=None):
        if os.getenv('AZURE_RESOURCE_GROUP') is not None:
            self.resource_group_name = os.getenv('AZURE_RESOURCE_GROUP')
        elif config is not None and 'azure.resource_group' in config:
            self.resource_group_name = config['azure.resource_group']
        else:
            self.resource_group_name = 'OceanProtocol'
