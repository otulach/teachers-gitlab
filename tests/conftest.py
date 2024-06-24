
import responses
import pytest

import mocks_gitlab_api
import mocks_bits

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
    res = mocks_gitlab_api.MockedGitLabApi(mocked_responses)
    yield res

@pytest.fixture(autouse=True)
def quick_retries(mocker):
    mocker.patch('matfyz.gitlab.utils.retries', mocks_bits.mock_retries)
