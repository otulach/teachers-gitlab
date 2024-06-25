
import logging

import matfyz.gitlab.teachers_gitlab as tg

def test_fork_one(mock_gitlab, mock_entries):
    mock_gitlab.register_project(42, 'base/repo')

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
        mock_entries.create([
            {'login': 'alpha'},
        ]),
        'login',
        'base/repo',
        'student/{login}',
        False,
        True
    )
