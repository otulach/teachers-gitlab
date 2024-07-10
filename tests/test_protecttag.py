import logging

import teachers_gitlab.main as tg
import gitlab

def test_protect_tag(mock_gitlab):
    entries = [
        {'login': 'alpha'},
    ]

    mock_gitlab.register_project(452, 'student/alpha')

    mock_gitlab.on_api_get(
        'projects/452/protected_tags/tag1',
        response_404=True,
    )

    mock_gitlab.on_api_post(
        'projects/452/protected_tags',
        request_json={
            'name': 'tag1',
            'create_access_level': 'devel'
            },
        response_json={
        }
    )

    mock_gitlab.report_unknown()

    tg.action_protect_tag(
        mock_gitlab.get_python_gitlab(),
        logging.getLogger("protecttag"),
        tg.ActionEntries(entries),
        'student/{login}',
        'tag1',
        'devel'
    )

def test_protect_tag(mock_gitlab):
    entries = [
        {'login': 'alpha'},
    ]

    mock_gitlab.register_project(452, 'student/alpha')

    mock_gitlab.on_api_get(
        'projects/452/protected_tags/tag1',
        response_json={
             'name': 'tag1',
             'create_access_levels': [
                 {
                     'id': 1,
                     'access_level': 30,
                     'access_level_description': 'Developers'
                 }
             ],
         },
    )

    mock_gitlab.report_unknown()

    tg.action_protect_tag(
        mock_gitlab.get_python_gitlab(),
        logging.getLogger("protecttag"),
        tg.ActionEntries(entries),
        'student/{login}',
        'tag1',
        gitlab.const.AccessLevel.DEVELOPER
    )

def test_protect_tag_access(mock_gitlab):
    entries = [
        {'login': 'alpha'},
    ]

    mock_gitlab.register_project(452, 'student/alpha')

    mock_gitlab.on_api_get(
        'projects/452/protected_tags/tag1',
        response_json={
             'name': 'tag1',
             'create_access_levels': [
                 {
                     'id': 1,
                     'access_level': 30,
                     'access_level_description': 'Maintainers'
                 }
             ],
         },
    )

    mock_gitlab.on_api_delete(
        'projects/452/protected_tags/tag1',
    )

    mock_gitlab.on_api_post(
        'projects/452/protected_tags',
        request_json={
            "name": "tag1",
            "create_access_level": 40
            },
        response_json={
        }
    )

    mock_gitlab.report_unknown()

    tg.action_protect_tag(
        mock_gitlab.get_python_gitlab(),
        logging.getLogger("protecttag"),
        tg.ActionEntries(entries),
        'student/{login}',
        'tag1',
        gitlab.const.AccessLevel.MAINTAINER
    )
