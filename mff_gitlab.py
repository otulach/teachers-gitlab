#!/usr/bin/env python3

import argparse
import csv
import locale
import sys
import http
import os
import gitlab
import d3s.gitlab as dg

def load_users(path):
    with open(path) as inp:
        data = csv.DictReader(inp)
        return list(data)

def as_gitlab_users(glb, users, login_column):
    for user in users:
        user_login = user.get(login_column)
        matching_users = glb.users.list(username=user_login)
        if len(matching_users) == 0:
            print("WARNING: user {} not found!".format(user_login))
            continue
        user_obj = matching_users[0]
        user_obj.row = user
        yield user_obj


def action_fork(glb, users, from_project, to_project_template, hide_fork):
    from_project = dg.get_canonical_project(glb, from_project)

    for user in users:
        to_full_path = to_project_template.format(**user.row)
        to_namespace = os.path.dirname(to_full_path)
        to_name = os.path.basename(to_full_path)

        print("Forking {} to {}/{} for user {}".format(from_project.path_with_namespace,
                                                       to_namespace, to_name,
                                                       user.username))
        to_project = dg.fork_project_idempotent(glb, from_project, to_namespace, to_name)

        if hide_fork:
            dg.remove_fork_relationship(glb, to_project)


def action_unprotect_branch(glb, users, project_template, branch_name):
    for user in users:
        project_path = project_template.format(**user.row)
        project = dg.get_canonical_project(glb, project_path)

        branch = project.branches.get(branch_name)
        print("Unprotecting branch {} on {}".format(branch.name, project.path_with_namespace))
        branch.unprotect()

def action_add_member(glb, users, project_template, access_level):
    if access_level == 'devel':
        level = gitlab.DEVELOPER_ACCESS
    else:
        raise Exception("Unsupported access level.")

    for user in users:
        project_path = project_template.format(**user.row)
        project = dg.get_canonical_project(glb, project_path)

        try:
            print("Adding {} to {}".format(user.username, project.path_with_namespace))
            project.members.create({
                'user_id' : user.id,
                'access_level' : level,
            })
        except gitlab.GitlabCreateError as exp:
            if exp.response_code == http.HTTPStatus.CONFLICT:
                pass
            else:
                print(" -> error: {}".format(exp))

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
                             action='append',
                             dest='gitlab_config_file',
                             help='GitLab configuration file.')
    args_common.add_argument('--instance',
                             default=None,
                             dest='gitlab_instance',
                             help='Which GitLab instance to choose.')

    args_users = argparse.ArgumentParser(add_help=False)
    args_users.add_argument('--users',
                            required=True,
                            dest='csv_users',
                            metavar='LIST.csv',
                            help='CSV with users.')
    args_users.add_argument('--login-column',
                            dest='csv_users_login_column',
                            default='login',
                            metavar='COLUMN_NAME',
                            help='Column name with login information')

    args = argparse.ArgumentParser(description='MFF GitLab Wrapper')
    args.set_defaults(action='help')
    args_sub = args.add_subparsers(help='Select what to do')

    args_help = args_sub.add_parser('help', help='Show this help.')
    args_help.set_defaults(action='help')

    args_fork = args_sub.add_parser('fork',
                                    help='Fork one repo multiple times.',
                                    parents=[args_common, args_users])
    args_fork.set_defaults(action='fork')
    args_fork.add_argument('--from',
                           required=True,
                           dest='fork_from',
                           metavar='REPO_PATH',
                           help='Parent repository path.')
    args_fork.add_argument('--to',
                           required=True,
                           dest='fork_to',
                           metavar='REPO_PATH_WITH_FORMAT',
                           help='Target repository path, including ' \
                                'formatting characters from CSV columns.')
    args_fork.add_argument('--hide-fork',
                           default=False,
                           dest='fork_hide_relationship',
                           action='store_true',
                           help='Hide fork relationship.')

    args_unprotect = args_sub.add_parser('unprotect',
                                         help='Unprotect branch on multiple projects.',
                                         parents=[args_common, args_users])
    args_unprotect.set_defaults(action='unprotect')
    args_unprotect.add_argument('--project',
                                required=True,
                                dest='project_path',
                                metavar='PROJECT_PATH_WITH_FORMAT',
                                help='Project path, including ' \
                                     'formatting characters from CSV columns.')
    args_unprotect.add_argument('--branch',
                                required=True,
                                dest='project_branch',
                                metavar='GIT_BRANCH',
                                help='Git branch name to unprotect')

    args_add_member = args_sub.add_parser('add-member',
                                          help='Add member on multiple projects.',
                                          parents=[args_common, args_users])
    args_add_member.set_defaults(action='add-member')
    args_add_member.add_argument('--project',
                                 required=True,
                                 dest='project_path',
                                 metavar='PROJECT_PATH_WITH_FORMAT',
                                 help='Project path, including ' \
                                      'formatting characters from CSV columns.')
    args_add_member.add_argument('--access-level',
                                 required=True,
                                 dest='access_level',
                                 metavar='LEVEL',
                                 help='Currently only "devel" is recognized.')

    if len(argv) < 1:
        # pylint: disable=too-few-public-methods
        class HelpConfig:
            def __init__(self):
                self.action = 'help'
        config = HelpConfig()
    else:
        config = args.parse_args(argv)

    if config.action == 'help':
        args.print_help()
        return

    glb = gitlab.Gitlab.from_config(config.gitlab_instance, config.gitlab_config_file)

    # These actions require that we prepare list of users
    if config.action in ['fork', 'unprotect', 'add-member']:
        users_csv = load_users(config.csv_users)
        users = as_gitlab_users(glb, users_csv, config.csv_users_login_column)

    if config.action == 'fork':
        action_fork(glb,
                    users,
                    config.fork_from,
                    config.fork_to,
                    config.fork_hide_relationship)
    elif config.action == 'unprotect':
        action_unprotect_branch(glb,
                                users,
                                config.project_path,
                                config.project_branch)
    elif config.action == 'add-member':
        action_add_member(glb,
                          users,
                          config.project_path,
                          config.access_level)
    else:
        raise Exception("Unknown action.")

if __name__ == '__main__':
    main(sys.argv[1:])
