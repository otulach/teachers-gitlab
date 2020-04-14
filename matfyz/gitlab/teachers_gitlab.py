#!/usr/bin/env python3

# SPDX-License-Identifier: Apache-2.0
# Copyright 2020 Charles University

import argparse
import csv
import locale
import sys
import http
import os
import pathlib
import time
import gitlab
import matfyz.gitlab.utils as mg

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

def action_accounts(users):
    for _ in users:
        pass

def action_fork(glb, users, from_project, to_project_template, hide_fork):
    from_project = mg.get_canonical_project(glb, from_project)

    for user in users:
        to_full_path = to_project_template.format(**user.row)
        to_namespace = os.path.dirname(to_full_path)
        to_name = os.path.basename(to_full_path)

        print("Forking {} to {}/{} for user {}".format(from_project.path_with_namespace,
                                                       to_namespace, to_name,
                                                       user.username))
        to_project = mg.fork_project_idempotent(glb, from_project, to_namespace, to_name)

        if hide_fork:
            mg.remove_fork_relationship(glb, to_project)


def action_unprotect_branch(glb, users, project_template, branch_name):
    for user in users:
        project_path = project_template.format(**user.row)
        project = mg.get_canonical_project(glb, project_path)

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
        project = mg.get_canonical_project(glb, project_path)

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

def action_put_file(glb, users,
                    project_template,
                    from_file_template,
                    to_file_template,
                    branch,
                    commit_message_template,
                    force_commit):
    for user in users:
        project_path = project_template.format(**user.row)
        from_file = from_file_template.format(**user.row)
        to_file = to_file_template.format(**user.row)
        extras = {
            'target_filename': to_file,
        }
        commit_message = commit_message_template.format(GL=extras, **user.row)

        project = mg.get_canonical_project(glb, project_path)
        from_file_content = pathlib.Path(from_file).read_text()

        commit_needed = force_commit
        if not force_commit:
            current_content = mg.get_file_contents(glb, project, branch, to_file)
            if current_content:
                commit_needed = current_content != from_file_content.encode('utf-8')
            else:
                commit_needed = True

        if commit_needed:
            print("Uploading {} to {} as {}".format(from_file, project.path_with_namespace, to_file))
            mg.put_file_overwriting(glb, project, branch, to_file, from_file_content, commit_message)
        else:
            print("Not uploading {} to {} as there is no change.".format(from_file, project.path_with_namespace))

def action_clone(glb, users,
                 project_template,
                 local_path_template,
                 branch,
                 deadline):
    for user in users:
        project = project_template.format(**user.row)
        local_path = local_path_template.format(**user.row)

        last_commit = mg.get_commit_before_deadline(glb, project, deadline, branch)
        mg.clone_or_fetch(glb, project, local_path)
        mg.reset_to_commit(local_path, last_commit.id)

def action_deadline_commits(glb, users,
                            project_template,
                            branch,
                            deadline,
                            output_header,
                            output_template,
                            output_filename):
    if output_filename:
        output = open(output_filename, 'w')
    else:
        output = sys.stdout

    print(output_header, file=output)
    for user in users:
        project = project_template.format(**user.row)
        last_commit = mg.get_commit_before_deadline(glb, project, deadline, branch)
        line = output_template.format(commit=last_commit, **user.row)
        print(line, file=output)
    if output_filename:
        output.close()

def main():
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

    args = argparse.ArgumentParser(description='Teachers GitLab for mass actions on GitLab')
    args.set_defaults(action='help')
    args_sub = args.add_subparsers(help='Select what to do')

    args_help = args_sub.add_parser('help', help='Show this help.')
    args_help.set_defaults(action='help')

    args_accounts = args_sub.add_parser('accounts',
                                        help='List accounts that were not found.',
                                        parents=[args_common, args_users])
    args_accounts.set_defaults(action='accounts')

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

    args_put_file = args_sub.add_parser('put-file',
                                        help='Upload file to multiple repos.',
                                        parents=[args_common, args_users])
    args_put_file.set_defaults(action='put-file')
    args_put_file.add_argument('--project',
                               required=True,
                               dest='project_path',
                               metavar='PROJECT_PATH_WITH_FORMAT',
                               help='Project path, including ' \
                                    'formatting characters from CSV columns.')
    args_put_file.add_argument('--from',
                               required=True,
                               dest='file_from',
                               metavar='LOCAL_FILE_PATH_WITH_FORMAT',
                               help='Local file path, including formatting.')
    args_put_file.add_argument('--to',
                               required=True,
                               dest='file_to',
                               metavar='REMOTE_FILE_PATH_WITH_FORMAT',
                               help='Remote file path, including formatting.')
    args_put_file.add_argument('--branch',
                               default='master',
                               dest='project_branch',
                               metavar='BRANCH',
                               help='Branch to commit to, defaults to master.')
    args_put_file.add_argument('--message',
                               default='Updating {GL[target_filename]}',
                               dest='commit_message',
                               metavar='COMMIT_MESSAGE_WITH_FORMAT',
                               help='Commit message, including formatting.')
    args_put_file.add_argument('--force-commit',
                               default=False,
                               dest='force_commit',
                               action='store_true',
                               help='Do not check current file content, always upload.')

    args_clone = args_sub.add_parser('clone',
                                     help='Clone multiple repos.',
                                     parents=[args_common, args_users])
    args_clone.set_defaults(action='clone')
    args_clone.add_argument('--project',
                            required=True,
                            dest='project_path',
                            metavar='PROJECT_PATH_WITH_FORMAT',
                            help='Project path, including ' \
                                 'formatting characters from CSV columns.')
    args_clone.add_argument('--to',
                            required=True,
                            dest='clone_to',
                            metavar='LOCAL_PATH_WITH_FORMAT',
                            help='Local repository path, including ' \
                                'formatting characters from CSV columns.')
    args_clone.add_argument('--branch',
                            default='master',
                            dest='project_branch',
                            metavar='BRANCH',
                            help='Branch to checkout.')
    args_clone.add_argument('--deadline',
                            default=time.strftime('%Y-%m-%dT%H:%M:S%z'),
                            dest='deadline',
                            metavar='YYYY-MM-DDTHH:MM:SSZ',
                            help='Submission deadline, ' \
                                'take last commit before deadline (defaults to now).')

    args_deadline_commit = args_sub.add_parser('deadline-commit',
                                     help='Get last commits before deadline.',
                                     parents=[args_common, args_users])
    args_deadline_commit.set_defaults(action='deadline-commit')
    args_deadline_commit.add_argument('--project',
                                      required=True,
                                      dest='project_path',
                                      metavar='PROJECT_PATH_WITH_FORMAT',
                                      help='Project path, including ' \
                                          'formatting characters from CSV columns.')
    args_deadline_commit.add_argument('--branch',
                                      default='master',
                                      dest='project_branch',
                                      metavar='BRANCH',
                                      help='Branch to use.')
    args_deadline_commit.add_argument('--deadline',
                                      default=time.strftime('%Y-%m-%dT%H:%M:%S%z'),
                                      dest='deadline',
                                      metavar='YYYY-MM-DDTHH:MM:SSZ',
                                      help='Submission deadline, ' \
                                         'take last commit before deadline (defaults to now).')
    args_deadline_commit.add_argument('--first-line',
                                      default='login,commit',
                                      dest='output_header',
                                      metavar='OUTPUT_HEADER',
                                      help='First line for the output.')
    args_deadline_commit.add_argument('--format',
                                      default='{login},{commit.id}',
                                      dest='output_format',
                                      metavar='OUTPUT_ROW_WITH_FORMAT',
                                      help='Formatting for the output row, ' \
                                          'defaults to {login},{commit.id}.')
    args_deadline_commit.add_argument('--output',
                                      default=None,
                                      dest='output_filename',
                                      metavar='OUTPUT_FILENAME',
                                      help='Output file, defaults to stdout.')

    if len(sys.argv) < 2:
        # pylint: disable=too-few-public-methods
        class HelpConfig:
            def __init__(self):
                self.action = 'help'
        config = HelpConfig()
    else:
        config = args.parse_args()

    if config.action == 'help':
        args.print_help()
        return

    glb = gitlab.Gitlab.from_config(config.gitlab_instance, config.gitlab_config_file)

    if hasattr(config, 'csv_users'):
        users_csv = load_users(config.csv_users)
        users = as_gitlab_users(glb, users_csv, config.csv_users_login_column)

    if config.action == 'accounts':
        action_accounts(users)
    elif config.action == 'clone':
        action_clone(glb,
                     users,
                     config.project_path,
                     config.clone_to,
                     config.project_branch,
                     config.deadline)
    elif config.action == 'deadline-commit':
        action_deadline_commits(glb,
                                users,
                                config.project_path,
                                config.project_branch,
                                config.deadline,
                                config.output_header,
                                config.output_format,
                                config.output_filename)
    elif config.action == 'fork':
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
    elif config.action == 'put-file':
        action_put_file(glb,
                        users,
                        config.project_path,
                        config.file_from,
                        config.file_to,
                        config.project_branch,
                        config.commit_message,
                        config.force_commit)
    else:
        raise Exception("Unknown action.")

if __name__ == '__main__':
    main()
