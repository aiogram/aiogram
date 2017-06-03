from distutils.core import setup

from setuptools import PackageFinder

from aiogram import __version__ as version


def get_description():
    with open('README.rst', encoding='utf-8') as f:
        return f.read()


setup(
    name='aiogram',
    version=version,
    packages=PackageFinder.find(exclude=('tests', 'examples', 'docs',)),
    url='https://bitbucket.org/illemius/aiogram',
    license='MIT',
    author='Alex Root Junior',
    author_email='jroot.junior@gmail.com',
    description='Telegram bot API framework based on asyncio',
    long_description=get_description(),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Programming Language :: Python :: 3.6',
        'Environment :: Console',
        'Framework :: AsyncIO',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
        'License :: OSI Approved :: MIT License',
    ],
    install_requires=['aiohttp']
)
