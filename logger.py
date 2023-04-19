import yaml
from logging import config, getLogger

log_config = 'config.yaml'
config.dictConfig(yaml.load(open(log_config).read(), Loader=yaml.SafeLoader))
logger = getLogger('develop')

