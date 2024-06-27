
import logging

import teachers_gitlab.main

def test_unprotect_branch(mock_gitlab):
    entries = [
        {'login': 'able', 'group': 'one'},
        {'login': 'baker', 'group': 'two'},
    ]

    # This project does not have the branch protected, hence
    # we return 404 about it and we do not expect a DELETE request
    mock_gitlab.register_project(101, 'course/one-able')
    mock_gitlab.on_api_get(
        'projects/101/protected_branches/devel',
        response_404=True,
    )

    # The second project still has the branch under protection
    # so we need to provide details and we expect the protection to be
    # lifted via a DELETE request
    mock_gitlab.register_project(102, 'course/two-baker')
    mock_gitlab.on_api_get(
        'projects/102/protected_branches/devel',
        response_json={
            'id': 1,
            'name': 'devel',
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
        'projects/102/protected_branches/devel',
    )

    # Perform the unprotection
    mock_gitlab.report_unknown()

    teachers_gitlab.main.action_unprotect_branch(
        mock_gitlab.get_python_gitlab(),
        logging.getLogger("unprotect"),
        teachers_gitlab.main.ActionEntries(entries),
        'course/{group}-{login}',
        'devel'
    )


def test_unprotect_branch_with_complex_name(mock_gitlab):
    entries = [
        {'login': 'alpha'},
    ]

    mock_gitlab.register_project(20, 'forks/alpha')

    mock_gitlab.on_api_get(
        'projects/20/protected_branches/' + mock_gitlab.escape_path_in_url('feature/*'),
        response_json={
            'id': 1,
            'name': 'feature/*',
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
        'projects/20/protected_branches/' + mock_gitlab.escape_path_in_url('feature/*')
    )

    mock_gitlab.report_unknown()

    teachers_gitlab.main.action_unprotect_branch(
        mock_gitlab.get_python_gitlab(),
        logging.getLogger("unprotect"),
        teachers_gitlab.main.ActionEntries(entries),
        'forks/{login}',
        'feature/*'
    )

