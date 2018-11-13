from osmosis_driver_interface.utils import get_value


class Config(object):
    def __init__(self, config=None):
        self.resource_group_name = get_value('azure.resource_group', 'AZURE_RESOURCE_GROUP', 'OceanProtocol', config)
