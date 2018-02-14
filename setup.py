#!/usr/bin/env python3

from distutils.core import setup

from pip.req import parse_requirements
from setuptools import PackageFinder

from aiogram import Stage, VERSION


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
    packages=PackageFinder.find(exclude=('tests', 'tests.*', 'examples.*', 'docs',)),
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
