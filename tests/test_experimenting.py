
import logging
import re
import time

import pytest

import json

import gitlab
import responses
import requests
from responses import _recorder

import matfyz.gitlab.teachers_gitlab as tg

class MockEntries:
    def __init__(self, entries):
        self.entries = entries

    def as_gitlab_users(self, _glb, login_column):
        for entry in self.entries:
            yield entry, None

def test_fork_one(mock_gitlab):
    mock_gitlab.on_api_get(
        'projects/' + mock_gitlab.escape_path_in_url('base/repo'),
        response_json={
            'id': 42,
            'path_with_namespace': 'base/repo'
        },
        helper=True,
    )

    mock_gitlab.on_api_post(
        'projects/42/fork',
        request_json={
            'name': 'alpha',
            'namespace': 'student',
            'path': 'alpha'
        },
        response_json={
            'id': 17,
        }
    )

    mock_gitlab.on_api_get(
        'projects/17',
        response_json={
            'id': 17,
            'path_with_namespace': 'student/alpha',
            'empty_repo': True,
        },
    )
    mock_gitlab.on_api_get(
        'projects/' + mock_gitlab.escape_path_in_url('student/alpha'),
        response_json={
            'id': 17,
            'path_with_namespace': 'student/alpha',
            'empty_repo': True,
        },
    )
    mock_gitlab.on_api_get(
        'projects/' + mock_gitlab.escape_path_in_url('student/alpha'),
        response_json={
            'id': 17,
            'path_with_namespace': 'student/alpha',
            'empty_repo': False,
        },
    )

    mock_gitlab.report_unknown()

    tg.action_fork(
        mock_gitlab.get_python_gitlab(),
        logging.getLogger("fork"),
        MockEntries([{'login': 'alpha'}]),
        'login',
        'base/repo',
        'student/{login}',
        False,
        True
    )
