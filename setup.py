import os
import codecs
from setuptools import setup


def read(*parts):
    filename = os.path.join(os.path.dirname(__file__), *parts)
    with codecs.open(filename, encoding='utf-8') as fp:
        return fp.read()


setup(
    name="django-queued-storage",
    use_scm_version=True,
    setup_requires=['setuptools_scm'],
    url='https://github.com/jazzband/django-queued-storage',
    license='BSD',
    description="Queued remote storage for Django.",
    long_description=read('README.rst'),
    author='Jannis Leidel',
    author_email='jannis@leidel.info',
    packages=['queued_storage'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Topic :: Utilities',
    ],
    install_requires=[
        'six>=1.10.0',
        'django-celery>=3.1,<3.2',
        'django-appconf >= 0.4',
    ],
    zip_safe=False,
)
