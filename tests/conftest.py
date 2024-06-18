
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
    logging.getLogger('DUMPER').error("URL not mocked: %s %s", req.method, req.url)
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
        self.responses.registered()[-1]._calls.add_call(None)
        self.responses.registered()[-2]._calls.add_call(None)

    def make_api_url_(self, suffix):
        return self.base_url + "api/v4/" + suffix

    def escape_path(self, path_with_namespace):
        import urllib.parse
        return urllib.parse.quote_plus(path_with_namespace)

    def quote_project_path_(self, path_with_namespace):
        import urllib.parse
        return urllib.parse.quote_plus(path_with_namespace)

    def get_python_gitlab(self):
        return gitlab.Gitlab(self.base_url, oauth_token="mock_token")

    def register_project(self, numerical_id, path_with_namespace, altering_responses=[]):
        def get_and_register_again(original_self, my_url, req, remaining_responses):
            self.logger.error("PROJECT: %s %s", req.method, req.url)

            if remaining_responses:
                extras = remaining_responses[0]
                remaining_responses = remaining_responses[1:]
            else:
                extras = {}

            base_info = {
                "path_with_namespace": path_with_namespace,
                "empty_repo": False,
                "id": numerical_id,
            }
            body = json.dumps({**base_info, **extras})

            original_self.responses.add_callback(
                responses.GET,
                my_url,
                callback=lambda x: get_and_register_again(original_self, my_url, x, remaining_responses)
            )

            headers = {}
            return (200, headers, body)

        self.logger.info("Registered project %s %s", numerical_id, path_with_namespace)
        for project_url in [self.make_api_url_("projects/" + self.quote_project_path_(path_with_namespace)), self.make_api_url_(f"projects/{numerical_id}")]:
            self.logger.info(" -> %s", project_url)
            self.responses.add_callback(
                responses.GET,
                project_url,
                callback=lambda x: get_and_register_again(self, project_url, x, altering_responses),
                content_type="application/json",
            )


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

    def logging_callback_200(self, req, body):
        self.logger.info("URL matched: %s %s", req.method, req.url)
        return (200, {}, body)

    def api_get(self, url, response_json, helper=False, *args, **kwargs):
        full_url = self.base_url + "api/v4/" + url

        kwargs['json'] = response_json

        if not helper:
            return self.responses.get(full_url, *args, **kwargs)

        for _ in [0, 1, 2, 3, 4, 5]:
            result = self.responses.get(full_url, *args, **kwargs)
            result._calls.add_call(None)


    def api_post(self, url, request_json, response_json, *args, **kwargs):
        full_url = self.base_url + "api/v4/" + url

        kwargs['body'] = json.dumps(response_json)
        kwargs['match'] = [
            responses.matchers.json_params_matcher(request_json)
        ]
        kwargs['content_type'] = 'application/json'

        return self.responses.post(
            full_url,
            *args,
            **kwargs,
        )


@pytest.fixture
def mocked_responses():
    with responses.RequestsMock(assert_all_requests_are_fired=True) as rsps:
        yield rsps

@pytest.fixture
def mock_gitlab(mocked_responses):
    """
    Using this fixture means you cannot have @responses.activate
    on your test method.
    """
    res = MockedGitLabApi(mocked_responses)
    yield res


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
