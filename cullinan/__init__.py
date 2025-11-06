import logging

# Prevent "No handlers could be found" warnings when library is imported
# Applications should configure logging (console/file) at their entry point.
logging.getLogger('cullinan').addHandler(logging.NullHandler())

# 导出配置接口
from cullinan.config import configure, get_config, CullinanConfig

__all__ = ['configure', 'get_config', 'CullinanConfig']

