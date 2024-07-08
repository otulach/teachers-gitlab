import logging

import teachers_gitlab.main as tg

def test_protect_tag_without_response(mock_gitlab):
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
            'id': 1,
            'name': 'tag1'
        },
    )
    
    mock_gitlab.on_api_post(
        'projects/452/protected_tags',
        request_json={
            'name': 'tag1',
            'create_access_level':'developers-can-create'
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
        'developers-can-create'
    )
      
    