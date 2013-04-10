__version__ = "0.6"


def version_hook(config):
    config['metadata']['version'] = __version__
