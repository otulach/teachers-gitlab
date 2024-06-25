
import logging

import matfyz.gitlab.teachers_gitlab as tg

def test_unprotect_unprotected_branch(mock_gitlab):
    entries = [
        {'login': 'alpha'},
    ]

    mock_gitlab.register_project(21, 'student/alpha')

    mock_gitlab.on_api_get(
        'projects/21/protected_branches/feature',
        response_404=True,
    )

    mock_gitlab.report_unknown()

    tg.action_unprotect_branch(
        mock_gitlab.get_python_gitlab(),
        logging.getLogger("unprotect"),
        tg.ActionEntries(entries),
        'student/{login}',
        'feature'
    )


def test_unprotect_protected_branch(mock_gitlab):
    entries = [
        {'login': 'alpha'},
    ]

    mock_gitlab.register_project(20, 'forks/alpha')

    mock_gitlab.on_api_get(
        'projects/20/protected_branches/' + mock_gitlab.escape_path_in_url('protected/feature'),
        response_json={
            'id': 1,
            'name': 'protected/feature',
            'push_access_levels': [
                {
                    'id': 1,
                    'access_level': 30,
                    'access_level_description': "Developers + Maintainers",
                },
            ],
            'merge_access_levels': [],
            'allow_force_push': False,
        },
    )

    mock_gitlab.on_api_delete(
        'projects/20/protected_branches/' + mock_gitlab.escape_path_in_url('protected/feature')
    )

    mock_gitlab.report_unknown()

    tg.action_unprotect_branch(
        mock_gitlab.get_python_gitlab(),
        logging.getLogger("unprotect"),
        tg.ActionEntries(entries),
        'forks/{login}',
        'protected/feature'
    )

