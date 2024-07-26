import logging

import teachers_gitlab.main as tg

def test_remove_member(mock_gitlab):
    entries = [
        {'login': 'alpha'},
    ]

    mock_gitlab.register_project(42, 'student/alpha', members =
    [
    {
        "id": 2157753,
        "username": "vhotspur",
        "name": "Vojtech Horky",
        "state": "active",
        "locked": False,
        "avatar_url": "https://secure.gravatar.com/avatar/a665e2f3f12801aa19e3166b5f1c58cce72f9d0b883db03228186d140d9812d8?s=80&d=identicon",
        "web_url": "https://gitlab.com/vhotspur",
        "access_level": 50,
        "created_at": "2021-09-20T10:35:31.505Z",
        "expires_at": None,
        "membership_state": "active"
    },
    {
        "id": 13907798,
        "username": "kliberf",
        "name": "Filip Kliber",
        "state": "active",
        "locked": False,
        "avatar_url": "https://secure.gravatar.com/avatar/9df758edf8df791bf80d534126d36f8af3e3ddfbbfa76df21be3b626bfe0f713?s=80&d=identicon",
        "web_url": "https://gitlab.com/kliberf",
        "access_level": 30,
        "created_at": "2023-03-06T13:14:09.163Z",
        "created_by": {
            "id": 2157753,
            "username": "vhotspur",
            "name": "Vojtech Horky",
            "state": "active",
            "locked": False,
            "avatar_url": "https://secure.gravatar.com/avatar/a665e2f3f12801aa19e3166b5f1c58cce72f9d0b883db03228186d140d9812d8?s=80&d=identicon",
            "web_url": "https://gitlab.com/vhotspur"
        },
        "expires_at": None,
        "membership_state": "active"
    },
    {
        "id": 834534,
        "username": "ceresek",
        "name": "Petr Tuma",
        "state": "active",
        "locked": False,
        "avatar_url": "https://gitlab.com/uploads/-/system/user/avatar/834534/avatar.png",
        "web_url": "https://gitlab.com/ceresek",
        "access_level": 50,
        "created_at": "2023-03-06T13:15:09.270Z",
        "created_by": {
            "id": 2157753,
            "username": "vhotspur",
            "name": "Vojtech Horky",
            "state": "active",
            "locked": False,
            "avatar_url": "https://secure.gravatar.com/avatar/a665e2f3f12801aa19e3166b5f1c58cce72f9d0b883db03228186d140d9812d8?s=80&d=identicon",
            "web_url": "https://gitlab.com/vhotspur"
        },
        "expires_at": None,
        "membership_state": "active"
    },
    {
        "id": 2157875,
        "username": "lbulej",
        "name": "Lubom\u00edr Bulej",
        "state": "active",
        "locked": False,
        "avatar_url": "https://secure.gravatar.com/avatar/ae72fcbee980eac250941d300e550df9e34bbc828f1253057f24088536f63b87?s=80&d=identicon",
        "web_url": "https://gitlab.com/lbulej",
        "access_level": 50,
        "created_at": "2023-03-06T13:15:09.323Z",
        "created_by": {
            "id": 2157753,
            "username": "vhotspur",
            "name": "Vojtech Horky",
            "state": "active",
            "locked": False,
            "avatar_url": "https://secure.gravatar.com/avatar/a665e2f3f12801aa19e3166b5f1c58cce72f9d0b883db03228186d140d9812d8?s=80&d=identicon",
            "web_url": "https://gitlab.com/vhotspur"
        },
        "expires_at": None,
        "membership_state": "active"
    }
])

    tg.action_remove_member(
        mock_gitlab.get_python_gitlab(),
        logging.getLogger("protecttag"),
        tg.ActionEntries(entries),
        1,
        True,
        'student/{login}',
    )
