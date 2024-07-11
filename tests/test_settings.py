import logging

import teachers_gitlab.main as tg
import gitlab

def test_project_settings(mock_gitlab):
    entries = [
        {'login': 'alpha'},
    ]

    mock_gitlab.register_project(42, 'student/alpha', mr_default_target_self='self')

    tg.action_project_settings(
        mock_gitlab.get_python_gitlab(),
        logging.getLogger("settings"),
        tg.ActionEntries(entries),
        True,
        'student/{login}',
        'self',
        'The best project'
    )

def test_project_settings_with_none(mock_gitlab):
    entries = [
        {'login': 'beta'},
    ]

    mock_gitlab.register_project(38, 'student/beta', mr_default_target_self='self')

    tg.action_project_settings(
        mock_gitlab.get_python_gitlab(),
        logging.getLogger("settings"),
        tg.ActionEntries(entries),
        True,
        'student/{login}',
        None,
        'The best project'
    )
