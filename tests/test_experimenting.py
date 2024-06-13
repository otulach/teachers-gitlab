
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


def test_fork_incomplete(mock_gitlab):
    mock_gitlab.add_project(15, "base/repo")
    mock_gitlab.add_project(16, "student/a")
    mock_gitlab.add_project(17, "student/b")

    mock_gitlab.on_api_post("projects/15/fork", json={"id": 16}, status=200)
    mock_gitlab.on_api_post("projects/15/fork", json={"id": 17}, status=200)

    mock_gitlab.report_unknown()

    tg.action_fork(
        mock_gitlab.get_python_gitlab(),
        logging.getLogger("fork"),
        MockEntries([{'login': 'a'}, {'login': 'b'}]),
        'login',
        'base/repo',
        'student/{login}',
        False,
        True
    )
