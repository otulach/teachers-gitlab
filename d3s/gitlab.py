"""
Helper GitLab functions.
"""

import http
import os
import pathlib
import subprocess
import gitlab

def get_canonical_project(glb, project):
    if isinstance(project, (int, str)):
        return glb.projects.get(project)
    if isinstance(project, gitlab.v4.objects.Project):
        return project
    raise Exception("Unexpected object type.")


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

def get_commit_before_deadline(glb, project, deadline, branch):
    project = get_canonical_project(glb, project)
    commits = project.commits.list(ref_name=branch, until=deadline)
    if not commits:
        raise Exception("No matching commit found.")
    else:
        return commits[0]

def clone_or_fetch(glb, project, local_path):
    if os.path.isdir(os.path.join(local_path, '.git')):
        rc = subprocess.call(['git', 'fetch'], cwd=local_path)
        if rc != 0:
            raise Exception("git fetch failed")
        return

    if os.path.isdir(local_path):
        if os.path.listdir(local_path):
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
