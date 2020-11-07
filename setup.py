#!/usr/bin/env python3
import pathlib
import re
import sys

from setuptools import find_packages, setup

WORK_DIR = pathlib.Path(__file__).parent

# Check python version
MINIMAL_PY_VERSION = (3, 7)
if sys.version_info < MINIMAL_PY_VERSION:
    raise RuntimeError('aiogram works only with Python {}+'.format('.'.join(map(str, MINIMAL_PY_VERSION))))


def get_version():
    """
    Read version

    :return: str
    """
    txt = (WORK_DIR / 'aiogram' / '__init__.py').read_text('utf-8')
    try:
        return re.findall(r"^__version__ = '([^']+)'\r?$", txt, re.M)[0]
    except IndexError:
        raise RuntimeError('Unable to determine version.')


def get_description():
    """
    Read full description from 'README.rst'

    :return: description
    :rtype: str
    """
    with open('README.rst', 'r', encoding='utf-8') as f:
        return f.read()


setup(
    name='aiogram',
    version=get_version(),
    packages=find_packages(exclude=('tests', 'tests.*', 'examples.*', 'docs',)),
    url='https://github.com/aiogram/aiogram',
    license='MIT',
    author='Alex Root Junior',
    requires_python='>=3.7',
    author_email='jroot.junior@gmail.com',
    description='Is a pretty simple and fully asynchronous framework for Telegram Bot API',
    long_description=get_description(),
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Framework :: AsyncIO',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
    ],
    install_requires=[
        'aiohttp>=3.7.2,<4.0.0',
        'Babel>=2.8.0',
        'certifi>=2020.6.20',
    ],
    extras_require={
        'proxy': [
            'aiohttp-socks>=0.3.4,<0.4.0',
        ],
        'fast': [
            'uvloop>=0.14.0,<0.15.0',
            'ujson>=1.35',
        ],
    },
    include_package_data=False,
)
