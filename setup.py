import codecs
import re
from os import path
from setuptools import setup, find_packages


def read(*parts):
    return codecs.open(path.join(path.dirname(__file__), *parts)).read()


def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


setup(
    name='django-queued-storage',
    version=find_version("queued_storage", "__init__.py"),
    description='Provides a proxy for Django storage backends that allows you '
                'to upload files locally and eventually serve them remotely',
    long_description=read('README.rst'),
    author='Sean Brant, Josh VanderLinden',
    author_email='codekoala@gmail.com',
    maintainer='Jannis Leidel',
    maintainer_email='jannis@leidel.info',
    url='http://django-queued-storage.rtfd.org',
    packages=find_packages(),
    license='BSD',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.5',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Utilities',
    ],
    install_requires=[
        'django-celery >= 2.3.3, < 3.0',
        'django-appconf >= 0.4',
    ],
    zip_safe=False,
)
