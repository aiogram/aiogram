#!/usr/bin/env python3

import string
from distutils.core import setup

from setuptools import PackageFinder

from aiogram import __version__ as version

ALLOWED_SYMBOLS = string.ascii_letters + string.digits + '_-'


def get_description():
    """
    Read full description from 'README.rst'

    :return: description
    :rtype: str
    """
    with open('README.rst', encoding='utf-8') as f:
        return f.read()


def get_requirements():
    """
    Read requirements from 'requirements txt'

    :return: requirements
    :rtype: list
    """
    requirements = []
    with open('requirements.txt', 'r') as file:
        for line in file.readlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            requirements.append(line)

    return requirements


setup(
    name='aiogram',
    version=version,
    packages=PackageFinder.find(exclude=('tests', 'examples', 'docs',)),
    url='https://bitbucket.org/illemius/aiogram',
    license='MIT',
    author='Alex Root Junior',
    author_email='jroot.junior@gmail.com',
    description='Is are pretty simple and fully asynchronously library for Telegram Bot API',
    long_description=get_description(),
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Programming Language :: Python :: 3.6',
        'Environment :: Console',
        'Framework :: AsyncIO',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
        'License :: OSI Approved :: MIT License',
    ],
    install_requires=get_requirements()
)
