# -*- coding: utf-8 -*-
__author__ = 'snailgirl'

"""
@author:snailgirl
@time: 18/11/16 下午3:25
"""
try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup, find_packages

setup(
    name='JiraBugStatistics',
    keywords='',
    version=1.0,
    packages=find_packages(),
    url='',
    license='MIT',
    author='snailgirl',
    author_email='test@test.com',
    description='',
    install_requires=[
        'jira',
        "configparser",
        "pyyaml"
    ]
)