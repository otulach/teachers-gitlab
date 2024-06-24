
import json
import logging
import re

import gitlab
import responses

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

    def escape_path_in_url(self, path_with_namespace):
        import urllib.parse
        return urllib.parse.quote_plus(path_with_namespace)

    def get_python_gitlab(self):
        return gitlab.Gitlab(self.base_url, oauth_token="mock_token")

    def on_api_get(self, url, response_json, helper=False, *args, **kwargs):
        full_url = self.make_api_url_(url)

        kwargs['json'] = response_json

        if not helper:
            return self.responses.get(full_url, *args, **kwargs)

        for _ in [0, 1, 2, 3, 4, 5]:
            result = self.responses.get(full_url, *args, **kwargs)
            result._calls.add_call(None)


    def on_api_post(self, url, request_json, response_json, *args, **kwargs):
        kwargs['body'] = json.dumps(response_json)
        kwargs['match'] = [
            responses.matchers.json_params_matcher(request_json)
        ]
        kwargs['content_type'] = 'application/json'

        return self.responses.post(
            self.make_api_url_(url),
            *args,
            **kwargs,
        )
