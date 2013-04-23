#!/usr/bin/env python
import os
import re

from setuptools import setup, find_packages


version = re.compile(r'VERSION\s*=\s*\((.*?)\)')


def get_package_version():
    "returns package version without importing it"
    base = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(base, "tcelery/__init__.py")) as initf:
        for line in initf:
            m = version.match(line.strip())
            if not m:
                continue
            return ".".join(m.groups()[0].split(", "))


setup(
    name='tornado-celery',
    version=get_package_version(),
    description='Celery integration with Tornado',
    long_description=open('README.rst').read(),
    author='Mher Movsisyan',
    author_email='mher.movsisyan@gmail.com',
    url='https://github.com/mher/tornado-celery',
    license='BSD',
    packages=find_packages(),
    install_requires=['celery', 'tornado', 'pika'],
    entry_points={
        'console_scripts': [
            'tcelery = tcelery.__main__:main',
        ]
    },
)
