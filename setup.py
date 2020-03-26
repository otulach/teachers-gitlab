#!/usr/bin/env python3

# SPDX-License-Identifier: Apache-2.0
# Copyright 2020 Charles University

from setuptools import setup

def get_readme():
    with open('README.md') as f:
        return f.read()

setup(
    name='matfyz-teachers-gitlab',
    version='0.1',
    description='CLI for mass actions on GitLab',
    long_description=get_readme(),
    classifiers=[
      'Programming Language :: Python :: 3.7',
    ],
    keywords='teaching gitlab',
    url='https://gitlab.mff.cuni.cz/teaching/utils/teachers-gitlab/',
    install_requires=[
        'python-gitlab'
    ],
    include_package_data=True,
    zip_safe=False,
    packages=[
        'matfyz.gitlab',
    ],
    entry_points={
        'console_scripts': [
            'teachers_gitlab=matfyz.gitlab.teachers_gitlab:main',
        ],
    },
)
