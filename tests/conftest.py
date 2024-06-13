
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

def dumping_callback(req):
    logging.getLogger('UNKNOWN').error("URL not mocked: %s %s", req.method, req.url)
    return (404, {}, json.dumps({"error": "not implemented"}))


class MockedGitLabApi:
    def __init__(self, rsps):
        self.base_url = "http://localhost/"
        rsps.start()

        self.responses = rsps
        self.logger = logging.getLogger("mocked-api")

    def report_unknown(self):
        self.responses.add_callback(
            responses.GET,
            re.compile("http://localhost/api/v4/.*"),
            callback=dumping_callback,
        )
        self.responses.add_callback(
            responses.POST,
            re.compile("http://localhost/api/v4/.*"),
            callback=dumping_callback,
        )

    def get_python_gitlab(self):
        return gitlab.Gitlab(self.base_url, oauth_token="mock_token")

    def add_project(self, numerical_id, path_with_namespace):
        import urllib.parse

        def get_project_info(req):
            self.logger.info("PROJECT: %s %s", req.method, req.url)
            body = json.dumps({
                "path_with_namespace": path_with_namespace,
                "empty_repo": False,
                "id": numerical_id,
            })
            headers = {}
            return (201, headers, body)

        # FIXME: for some calls it is okay that they are called multiple-times
        for _ in [1, 2, 3, 4, 5, 6]:
            self.responses.add_callback(
                responses.GET,
                "http://localhost/api/v4/projects/" + urllib.parse.quote_plus(path_with_namespace),
                callback=get_project_info,
                content_type="application/json",
            )
        self.responses.add_callback(
            responses.GET,
            "http://localhost/api/v4/projects/" + str(numerical_id),
            callback=get_project_info,
            content_type="application/json",
        )

    def on_api_get(self, url, *args, **kwargs):
        return self.responses.get(self.base_url + "api/v4/" + url, *args, **kwargs)

    def on_api_post(self, url, *args, **kwargs):
        return self.responses.post(self.base_url + "api/v4/" + url, *args, **kwargs)

@pytest.fixture
def mocked_responses():
    with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        yield rsps

@pytest.fixture
def mock_gitlab(mocked_responses):
    """
    Using this fixture means you cannot have @responses.activate
    on your test method.
    """
    res = MockedGitLabApi(mocked_responses)
    logging.getLogger("fixture").info("Before yield!")
    yield res
    logging.getLogger("fixture").info("Terminates")



def mock_retries(n=None,
    interval=2,
    timeout=None,
    message="Operation timed-out (too many retries)"
):
    if (n is None) and (timeout is None):
        raise Exception("Specify either n or timeout for retries")

    if (n is not None) and (timeout is not None):
        interval = timeout / n

    if timeout is None:
        timeout = n * interval
    remaining = timeout
    n = 0
    while remaining > 0:
        remaining = remaining - interval
        n = n + 1
        yield n
        time.sleep(0)
    raise Exception(message)

@pytest.fixture(autouse=True)
def quick_retries(mocker):
    mocker.patch('matfyz.gitlab.utils.retries', mock_retries)
