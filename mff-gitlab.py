#!/usr/bin/env python3

import argparse
import csv
import locale
import sys
import d3s.gitlab as dg
import gitlab
import http
import os

def load_users(path):
    with open(path) as f:
        data = csv.DictReader(f)
        return list(data)

def as_gitlab_users(gl, users, login_column):
    for user in users:
        user_login = user.get(login_column)
        user_obj = gl.users.list(username=user_login)[0]
        user_obj.row = user
        yield user_obj

def action_fork(gl, config):
    users = load_users(config.csv_users)
    
    from_project = dg.get_canonical_project(gl, config.fork_from)
    
    for user in as_gitlab_users(gl, users, config.csv_users_login_column):
        to_full_path = config.fork_to.format(**user.row)
        to_namespace = os.path.dirname(to_full_path)
        to_name = os.path.basename(to_full_path)
        
        print("Forking {} to {}/{} for user {}".format(from_project.path_with_namespace, to_namespace, to_name, user.username))
        to_project = dg.fork_project_idempotent(gl, from_project, to_namespace, to_name)
        
        if config.fork_hide_relationship:
            dg.remove_fork_relationship(gl, to_project)


def action_unprotect_branch(gl, config):
    users = load_users(config.csv_users)
    
    for user in as_gitlab_users(gl, users, config.csv_users_login_column):
        project_path = config.project_path.format(**user.row)
        project = dg.get_canonical_project(gl, project_path)
        
        branch = project.branches.get(config.project_branch)
        print("Unprotecting branch {} on {}".format(branch.name, project.path_with_namespace))
        branch.unprotect()

def action_add_member(gl, config):
    users = load_users(config.csv_users)
        
    if config.access_level == 'devel':
        level = gitlab.DEVELOPER_ACCESS
    else:
        raise Exception("Unsupported access level.")
    
    for user in as_gitlab_users(gl, users, config.csv_users_login_column):
        project_path = config.project_path.format(**user.row)
        project = dg.get_canonical_project(gl, project_path)

        try:
            print("Adding {} to {}".format(user.username, project.path_with_namespace))
            project.members.create({
                'user_id' : user.id,
                'access_level' : level,
            })
        except gitlab.GitlabCreateError as e:
            if e.response_code == http.HTTPStatus.CONFLICT:
                pass
            else:
                print(" -> error: {}".format(e))

def main(argv):
    locale.setlocale(locale.LC_ALL, '')

    args_common = argparse.ArgumentParser(add_help=False)
    args_common.add_argument('--debug',
                             default=False,
                             dest='debug',
                             action='store_true',
                             help='Print debugging messages.')
    args_common.add_argument('--config-file',
                             default=None,
                             dest='gitlab_config_file',
                             help='GitLab configuration file.')
    args_common.add_argument('--instance',
                             default=None,
                             dest='gitlab_instance',
                             help='Which GitLab instance to choose.')
    
    args = argparse.ArgumentParser(description='MFF GitLab Wrapper')
    args.set_defaults(action='help')
    args_sub = args.add_subparsers(help='Select what to do')

    args_help = args_sub.add_parser('help', help='Show this help.')
    args_help.set_defaults(action='help')

    args_fork = args_sub.add_parser('fork',
                                    help='Fork one repo multiple times.',
                                    parents=[args_common])
    args_fork.set_defaults(action='fork')
    args_fork.add_argument('--users',
                           required=True,
                           dest='csv_users',
                           metavar='LIST.csv',
                           help='CSV with users.')
    args_fork.add_argument('--login-column',
                           dest='csv_users_login_column',
                           default='login',
                           metavar='COLUMN_NAME',
                           help='Column name with login information')
    args_fork.add_argument('--from',
                           required=True,
                           dest='fork_from',
                           metavar='REPO_PATH',
                           help='Parent repository path.')
    args_fork.add_argument('--to',
                           required=True,
                           dest='fork_to',
                           metavar='REPO_PATH_WITH_FORMAT',
                           help='Target repository path, including formatting characters from CSV columns.')
    args_fork.add_argument('--hide-fork',
                           default=False,
                           dest='fork_hide_relationship',
                           action='store_true',
                           help='Hide fork relationship.')

    args_unprotect = args_sub.add_parser('unprotect',
                                         help='Unprotect branch on multiple projects.',
                                         parents=[args_common])
    args_unprotect.set_defaults(action='unprotect')
    args_unprotect.add_argument('--users',
                                required=True,
                                dest='csv_users',
                                metavar='LIST.csv',
                                help='CSV with users.')
    args_unprotect.add_argument('--login-column',
                                dest='csv_users_login_column',
                                default='login',
                                metavar='COLUMN_NAME',
                                help='Column name with login information')
    args_unprotect.add_argument('--project',
                                required=True,
                                dest='project_path',
                                metavar='PROJECT_PATH_WITH_FORMAT',
                                help='Project path, including formatting characters from CSV columns.')
    args_unprotect.add_argument('--branch',
                                required=True,
                                dest='project_branch',
                                metavar='GIT_BRANCH',
                                help='Git branch name to unprotect')

    args_add_member = args_sub.add_parser('add-member',
                                          help='Add member on multiple projects.',
                                          parents=[args_common])
    args_add_member.set_defaults(action='add-member')
    args_add_member.add_argument('--users',
                                 required=True,
                                 dest='csv_users',
                                 metavar='LIST.csv',
                                 help='CSV with users.')
    args_add_member.add_argument('--login-column',
                                 dest='csv_users_login_column',
                                 default='login',
                                 metavar='COLUMN_NAME',
                                 help='Column name with login information')
    args_add_member.add_argument('--project',
                                 required=True,
                                 dest='project_path',
                                 metavar='PROJECT_PATH_WITH_FORMAT',
                                 help='Project path, including formatting characters from CSV columns.')
    args_add_member.add_argument('--access-level',
                                 required=True,
                                 dest='access_level',
                                 metavar='LEVEL',
                                 help='Currently only "devel" is recognized.')

    if len(argv) < 1:
        class HelpConfig(object):
            def __init__(self):
                self.action = 'help'
        config = HelpConfig()
    else:
        config = args.parse_args(argv)

    if config.action == 'help':
        args.print_help()
        return

    if config.gitlab_config_file:
        config.gitlab_config_file = [ config.gitlab_config_file ]
    else:
        config.gitlab_config_file = [ '/etc/python-gitlab.cfg', '~/.python-gitlab.cfg' ]

    gl = gitlab.Gitlab.from_config(config.gitlab_instance, config.gitlab_config_file)
    
    if config.action == 'fork':
        action_fork(gl, config)
    elif config.action == 'unprotect':
        action_unprotect_branch(gl, config)
    elif config.action == 'add-member':
        action_add_member(gl, config)
    else:
        raise Exception("Unknown action.")

if __name__ == '__main__':
    main(sys.argv[1:])
