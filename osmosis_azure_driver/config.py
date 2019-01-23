import os
from osmosis_driver_interface.utils import parse_config


class Config(object):
    def __init__(self, config=None):
        config = parse_config(config)
        if os.getenv('AZURE_RESOURCE_GROUP') is not None:
            self.resource_group_name = os.getenv('AZURE_RESOURCE_GROUP')
        elif config is not None and 'azure.resource_group' in config:
            self.resource_group_name = config['azure.resource_group']
        else:
            self.resource_group_name = 'OceanProtocol'
