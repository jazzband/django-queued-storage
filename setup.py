import codecs
from os import path
from setuptools import setup, find_packages

read = lambda filepath: codecs.open(filepath, 'r', 'utf-8').read()

setup(
    name='django-queued-storage',
    version=":versiontools:queued_storage:",
    description='Provides a proxy for django file storage, that allows you '
                'to upload files locally and eventually serve them remotely',
    long_description=read(path.join(path.dirname(__file__), 'README.rst')),
    author='Sean Brant, Josh VanderLinden',
    author_email='codekoala@gmail.com',
    maintainer='Jannis Leidel',
    maintainer_email='jannis@leidel.info',
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
    setup_requires = [
        'versiontools >= 1.8',
    ],
    include_package_data=True,
    zip_safe=False,
)
