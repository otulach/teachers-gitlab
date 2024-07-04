import logging

import teachers_gitlab.main as tg

def test_create_tag(mock_gitlab):
    entries = [
        {'login': 'alpha'},
    ]
    
    mock_gitlab.register_project(452, 'student/alpha')
    
    mock_gitlab.on_api_post(
        'projects/452/repository/tags',
        request_json={
            'ref': '', 
            'tag_name': 'tag1'
            },
        response_json={
        }
    )

    mock_gitlab.report_unknown()

    tg.action_create_tag(
        mock_gitlab.get_python_gitlab(),
        logging.getLogger("createtag"),
        tg.ActionEntries(entries),
        'student/{login}',
        'tag1',
        '',
        ''
    )
    
def test_create_existing_tag(mock_gitlab):
    entries = [
        {'login': 'alpha'},
    ]
    
    mock_gitlab.register_project(452, 'student/alpha')
    
    mock_gitlab.on_api_post(
        'projects/452/repository/tags',
        request_json={
            'ref': 'double', 
            'tag_name': 'tag2'
            },
        response_json={
            "message": "already exists"
        }
    )

    mock_gitlab.report_unknown()

    tg.action_create_tag(
        mock_gitlab.get_python_gitlab(),
        logging.getLogger("createtag"),
        tg.ActionEntries(entries),
        'student/{login}',
        'tag2',
        'double',
        ''
    )   
