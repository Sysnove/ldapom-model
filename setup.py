#!/usr/bin/env python
# -*- coding: utf-8 -*-
 
import os
from setuptools import setup, find_packages

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()
 
setup(
    name='ldapom-model',
    version='0.1.0',
    packages=find_packages(),
    author="Guillaume Subiron",
    author_email="maethor+pip@subiron.org",
    description="Base class to manage models with ldapom.",
    long_description=read('README.md'),
    install_requires=['ldapom==0.12.0'],
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
