#!/usr/bin/env python
import os
import sys
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

install_requires = ['celery', 'tornado']
dependency_links = []

if sys.version_info[0] >= 3:
    dependency_links.append(
        'https://github.com/renshawbay/pika-python3/archive/python3.zip#egg=pika-python3'
    )
    install_requires.append('pika-python3')
else:
    install_requires.append('pika')

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
    install_requires=install_requires,
    dependency_links=dependency_links,
    entry_points={
        'console_scripts': [
            'tcelery = tcelery.__main__:main',
        ]
    },
)
