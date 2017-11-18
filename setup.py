#!/usr/bin/env python3

from distutils.core import setup

from setuptools import PackageFinder

from aiogram import VERSION


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
    version=VERSION.version,
    packages=PackageFinder.find(exclude=('tests', 'examples', 'docs',)),
    url='https://github.com/aiogram/aiogram',
    license='MIT',
    author='Alex Root Junior',
    author_email='jroot.junior@gmail.com',
    description='Is are pretty simple and fully asynchronously library for Telegram Bot API',
    long_description=get_description(),
    classifiers=[
        VERSION.pypi_development_status,  # Automated change classifier by build stage
        'Programming Language :: Python :: 3.6',
        'Environment :: Console',
        'Framework :: AsyncIO',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
        'License :: OSI Approved :: MIT License',
    ],
    install_requires=get_requirements()
)
