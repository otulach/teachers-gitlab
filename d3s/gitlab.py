
import gitlab
import http

def get_canonical_project(gl, project):
    if isinstance (project, ( int, str )):
        return gl.projects.get (project)
    if isinstance (project, gitlab.v4.objects.Project):
        return project
    raise Exception("Unexpected object type.")

def fork_project_idempotent(gl, parent, fork_namespace, fork_name):
    parent = get_canonical_project(gl, parent)
    
    try:
        fork_handle = parent.forks.create({
            'namespace' : fork_namespace,
            'path' : fork_name,
            'name' : fork_name,
        })
        fork_identity = fork_handle.id
    except gitlab.GitlabCreateError as e:
        if e.response_code == http.HTTPStatus.CONFLICT:
            fork_identity = "{}/{}".format(fork_namespace, fork_name)
        else:
            raise

    return get_canonical_project(gl, fork_identity)

def remove_fork_relationship(gl, project):
    project = get_canonical_project(gl, project)
    try:
        project.delete_fork_relation()
    except gitlab.GitlabDeleteError as e:
        if e.response_code == http.HTTPStatus.NOT_MODIFIED:
            pass
        else:
            raise

