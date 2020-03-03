"""
Helper GitLab functions.
"""

import http
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
