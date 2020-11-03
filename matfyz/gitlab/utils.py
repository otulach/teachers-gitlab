
# SPDX-License-Identifier: Apache-2.0
# Copyright 2020 Charles University

"""
Helper GitLab functions.
"""

import base64
import http
import os
import pathlib
import subprocess
import time
import gitlab


def get_canonical_project(glb, project):
    if isinstance(project, (int, str)):
        return glb.projects.get(project)
    if isinstance(project, gitlab.v4.objects.Project):
        return project
    raise Exception("Unexpected object type.")


def retries(n=None, interval=2, timeout=None, message="Operation timed-out (too many retries)"):
    """
    To be used in for-loops to try action multiple times.
    Throws exception on time-out.
    """

    if (n is None) and (timeout is None):
        raise Exception("Specify either n or timeout for retries")

    if timeout is None:
        timeout = n * interval
    remaining = timeout
    n = 0
    while remaining > 0:
        remaining = remaining - interval
        n = n + 1
        yield n
        time.sleep(interval)
    raise Exception(message)


def wait_for_project_to_be_forked(glb, project_path, timeout=None):
    project = get_canonical_project(glb, project_path)

    # In 10 minutes, even Torvalds' Linux repository is forked
    # on a not-that-fast instance :-)
    for i in retries(120, 5, timeout):
        if not project.empty_repo:
            return
        # Force refresh (why project.refresh() does not work?)
        project = get_canonical_project(glb, project.path_with_namespace)


def fork_project_idempotent(glb, parent, fork_namespace, fork_name):
    parent = get_canonical_project(glb, parent)

    try:
        fork_handle = parent.forks.create({
            'namespace' : fork_namespace,
            'path' : fork_name,
            'name' : fork_name,
        })
        fork_identity = fork_handle.id
    except gitlab.GitlabCreateError as exp:
        if exp.response_code == http.HTTPStatus.CONFLICT:
            fork_identity = "{}/{}".format(fork_namespace, fork_name)
        else:
            raise

    return get_canonical_project(glb, fork_identity)


def remove_fork_relationship(glb, project):
    project = get_canonical_project(glb, project)
    try:
        project.delete_fork_relation()
    except gitlab.GitlabDeleteError as exp:
        if exp.response_code == http.HTTPStatus.NOT_MODIFIED:
            pass
        else:
            raise


def put_file_overwriting(glb, project, branch, file_path, file_contents, commit_message):
    project = get_canonical_project(glb, project)
    commit_data = {
        'branch': branch,
        'commit_message': commit_message,
        'actions': [
            {
                'action': 'create',
                'file_path': file_path,
                'content': file_contents,
            },
        ],
    }
    try:
        return project.commits.create(commit_data)
    except gitlab.exceptions.GitlabCreateError as exp:
        if exp.response_code == http.HTTPStatus.BAD_REQUEST:
            commit_data['actions'][0]['action'] = 'update'
            return project.commits.create(commit_data)
        else:
            raise


def get_file_contents(glb, project, branch, file_path):
    project = get_canonical_project(glb, project)
    base_filename = os.path.basename(file_path)
    files = project.repository_tree(
        path=os.path.dirname(file_path),
        ref=branch,
        all=True,
        as_list=False
    )
    current_file = [f for f in files if f['name'] == base_filename]
    if not current_file:
        return None
    file_info = project.repository_blob(current_file[0]['id'])
    content = base64.b64decode(file_info['content'])
    return content


def get_commit_before_deadline(glb, project, deadline, branch, filter = lambda commit: True):
    project = get_canonical_project(glb, project)
    commits = project.commits.list(ref_name=branch, until=deadline)
    for commit in commits:
        if filter (commit):
            return (commit)
    raise Exception("No matching commit found.")


def clone_or_fetch(glb, project, local_path):
    if os.path.isdir(os.path.join(local_path, '.git')):
        rc = subprocess.call(['git', 'fetch'], cwd=local_path)
        if rc != 0:
            raise Exception("git fetch failed")
        return

    if os.path.isdir(local_path):
        if os.listdir(local_path):
            raise Exception("There is non-empty directory that is not Git!")

    pathlib.Path(local_path).mkdir(parents=True, exist_ok=True)

    project = get_canonical_project(glb, project)
    git_url = project.ssh_url_to_repo
    rc = subprocess.call(['git', 'clone', git_url, local_path])
    if rc != 0:
        raise Exception("git clone failed")


def reset_to_commit(local_path, commit):
    rc = subprocess.call(['git', 'reset', '--hard', commit], cwd=local_path)
    if rc != 0:
        raise Exception("git reset failed")
