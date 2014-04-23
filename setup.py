#!/usr/bin/env python
# -*- coding: utf-8 -*-
 
from setuptools import setup, find_packages
 
setup(
    name='ldapom-model',
    version='0.0.1',
    packages=find_packages(),
    author="Guillaume Subiron",
    author_email="maethor+pip@subiron.org",
    description="Base class to manage models with ldapom.",
    long_description=open('README.md').read(),
    install_requires=['ldapom==0.11.0'],
    include_package_data=True,
    url='http://github.com/maethor/ldapom-model',
    classifiers=[
        "Programming Language :: Python",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3.3",
    ],
    license="WTFPL",
)
