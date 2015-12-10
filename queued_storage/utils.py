import django
from django.core.exceptions import ImproperlyConfigured
from django.utils.importlib import import_module


def import_attribute(import_path=None, options=None):
    if import_path is None:
        raise ImproperlyConfigured("No import path was given.")
    try:
        dot = import_path.rindex('.')
    except ValueError:
        raise ImproperlyConfigured("%s isn't a module." % import_path)
    module, classname = import_path[:dot], import_path[dot + 1:]
    try:
        mod = import_module(module)
    except ImportError as e:
        raise ImproperlyConfigured('Error importing module %s: "%s"' %
                                   (module, e))
    try:
        return getattr(mod, classname)
    except AttributeError:
        raise ImproperlyConfigured(
            'Module "%s" does not define a "%s" class.' % (module, classname))


def django_version():
    return [int(x) for x in django.get_version().split('.')]
