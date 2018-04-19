#!/usr/bin/env python3

import sys
from warnings import warn

from setuptools import find_packages, setup

try:
    from pip.req import parse_requirements
except ImportError:  # pip >= 10.0.0
    from pip._internal.req import parse_requirements

from aiogram import Stage, VERSION

MINIMAL_PY_VERSION = (3, 6)

if sys.version_info < MINIMAL_PY_VERSION:
    warn('aiogram works only with Python {}+'.format('.'.join(map(str, MINIMAL_PY_VERSION)), RuntimeWarning))


def get_description():
    """
    Read full description from 'README.rst'

    :return: description
    :rtype: str
    """
    with open('README.rst', 'r', encoding='utf-8') as f:
        return f.read()


def get_requirements():
    """
    Read requirements from 'requirements txt'

    :return: requirements
    :rtype: list
    """
    filename = 'requirements.txt'
    if VERSION.stage == Stage.DEV:
        filename = 'dev_' + filename

    install_reqs = parse_requirements(filename, session='hack')
    return [str(ir.req) for ir in install_reqs]


install_requires = get_requirements()

setup(
    name='aiogram',
    version=VERSION.version,
    packages=find_packages(exclude=('tests', 'tests.*', 'examples.*', 'docs',)),
    url='https://github.com/aiogram/aiogram',
    license='MIT',
    author='Alex Root Junior',
    author_email='jroot.junior@gmail.com',
    description='Is a pretty simple and fully asynchronous library for Telegram Bot API',
    long_description=get_description(),
    classifiers=[
        VERSION.pypi_development_status,  # Automated change classifier by build stage
        'Environment :: Console',
        'Framework :: AsyncIO',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.6',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
    ],
    install_requires=install_requires
)
