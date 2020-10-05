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


class ActionParameter:
    def __init__(self, name, **kwargs):
        self.name = name
        self.extra_args = kwargs

def register_command(name, help, callback_func, command_parser, parser_common, parser_users):
    parser = command_parser.add_parser(
        name,
        help=help,
        parents=[parser_common, parser_users]
    )
    for dest, param in callback_func.__annotations__.items():
        parser.add_argument(
            '--' + param.name,
            dest='command_' + dest,
            **param.extra_args
        )

    def callback_wrapper(glb, users, cfg, callback):
        kwargs = {}
        for dest, param in callback.__annotations__.items():
            kwargs[dest] = getattr(cfg, 'command_' + dest)
        callback(glb, users, **kwargs)

    parser.set_defaults(action='error')
    parser.set_defaults(func=lambda glb, users, cfg: callback_wrapper(glb, users, cfg, callback_func))



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


def action_fork(
        glb,
        users,
        from_project: ActionParameter(
            'from',
            required=True,
            metavar='REPO_PATH',
            help='Parent repository path.'
        ),
        to_project_template: ActionParameter(
            'to',
            required=True,
            metavar='REPO_PATH_WITH_FORMAT',
            help='Target repository path, including formatting characters from CSV columns.'
        ),
        hide_fork: ActionParameter(
            'hide-fork',
            default=False,
            action='store_true',
            help='Hide fork relationship.'
        )
    ):
    from_project = mg.get_canonical_project(glb, from_project)

    for user in users:
        to_full_path = to_project_template.format(**user.row)
        to_namespace = os.path.dirname(to_full_path)
        to_name = os.path.basename(to_full_path)

        print("Forking {} to {}/{} for user {}".format(from_project.path_with_namespace,
                                                       to_namespace, to_name,
                                                       user.username))
        to_project = mg.fork_project_idempotent(glb, from_project, to_namespace, to_name)
        mg.wait_for_project_to_be_forked(glb, to_project)

        if hide_fork:
            mg.remove_fork_relationship(glb, to_project)


def action_set_branch_protection(
        glb,
        users,
        project_template: ActionParameter(
            'project',
            required=True,
            metavar='PROJECT_PATH_WITH_FORMAT',
            help='Project path, including formatting characters from CSV columns.'
        ),
        branch_name: ActionParameter(
            'branch',
            required=True,
            metavar='GIT_BRANCH',
            help='Git branch name to set protection on.'
        ),
        developers_can_merge: ActionParameter(
            'developers-can-merge',
            default=False,
            action='store_true',
            help='Allow developers to merge into this branch.'
        ),
        developers_can_push: ActionParameter(
            'developers-can-push',
            default=False,
            action='store_true',
            help='Allow developers to merge into this branch.'
        )
    ):
    for user in users:
        project_path = project_template.format(**user.row)
        project = mg.get_canonical_project(glb, project_path)

        branch = project.branches.get(branch_name)
        print("Setting protection on branch {} in {}".format(branch.name, project.path_with_namespace))
        branch.protect(developers_can_push=developers_can_push, developers_can_merge=developers_can_merge)


def action_unprotect_branch(
        glb,
        users,
        project_template: ActionParameter(
            'project',
            required=True,
            metavar='PROJECT_PATH_WITH_FORMAT',
            help='Project path, including formatting characters from CSV columns.'
        ),
        branch_name: ActionParameter(
            'branch',
            required=True,
            metavar='GIT_BRANCH',
            help='Git branch name to unprotect.'
        )
    ):
    for user in users:
        project_path = project_template.format(**user.row)
        project = mg.get_canonical_project(glb, project_path)

        branch = project.branches.get(branch_name)
        print("Unprotecting branch {} on {}".format(branch.name, project.path_with_namespace))
        branch.unprotect()


def action_add_member(
        glb,
        users,
        project_template: ActionParameter(
            'project',
            required=True,
            metavar='PROJECT_PATH_WITH_FORMAT',
            help='Project path, including formatting characters from CSV columns.'
        ),
        access_level: ActionParameter(
            'access-level',
            required=True,
            metavar='LEVEL',
            help='Access level: devel or reporter.'
        )
    ):
    if access_level == 'devel':
        level = gitlab.DEVELOPER_ACCESS
    elif access_level == 'reporter':
        level = gitlab.REPORTER_ACCESS
    else:
        raise Exception("Unsupported access level.")

    for user in users:
        project_path = project_template.format(**user.row)
        project = mg.get_canonical_project(glb, project_path)

        try:
            print("Adding {} to {} (level {})".format(user.username, project.path_with_namespace, level))
            project.members.create({
                'user_id' : user.id,
                'access_level' : level,
            })
        except gitlab.GitlabCreateError as exp:
            if exp.response_code == http.HTTPStatus.CONFLICT:
                pass
            else:
                print(" -> error: {}".format(exp))


def action_get_file(
        glb,
        users,
        project_template: ActionParameter(
            'project',
            required=True,
            metavar='PROJECT_PATH_WITH_FORMAT',
            help='Project path, including formatting characters from CSV columns.'
        ),
        remote_file_template: ActionParameter(
            'remote-file',
            required=True,
            metavar='PROJECT_PATH_WITH_FORMAT',
            help='Project path, including formatting characters from CSV columns.'
        ),
        local_file_template: ActionParameter(
            'local-file',
            required=True,
            metavar='PROJECT_PATH_WITH_FORMAT',
            help='Project path, including formatting characters from CSV columns.'
        ),
        branch: ActionParameter(
            'branch',
            default='master',
            metavar='PROJECT_PATH_WITH_FORMAT',
            help='Project path, including formatting characters from CSV columns.'
        ),
        deadline: ActionParameter(
            'deadline',
            default='now',
            metavar='PROJECT_PATH_WITH_FORMAT',
            help='Project path, including formatting characters from CSV columns.'
        )
    ):

    if deadline == 'now':
        deadline = time.strftime('%Y-%m-%dT%H:%M:%S%z')
    for user in users:
        project_path = project_template.format(**user.row)
        remote_file = remote_file_template.format(**user.row)
        local_file = local_file_template.format(**user.row)

        try:
            project = mg.get_canonical_project(glb, project_path)
        except gitlab.exceptions.GitlabGetError:
            print("WARNING: project {} not found!".format(project_path), file=sys.stderr)
            continue

        last_commit = mg.get_commit_before_deadline(glb, project, deadline, branch)
        current_content = mg.get_file_contents(glb, project, last_commit.id, remote_file)
        if current_content is None:
            print("File {} does not exist in {}.".format(remote_file, project.path_with_namespace))
        else:
            print("File {} in {} has {}B.".format(remote_file, project.path_with_namespace, len(current_content)))
            with open(local_file, "wb") as f:
                f.write(current_content)


def action_put_file(
        glb,
        users,
        project_template: ActionParameter(
            'project',
            required=True,
            metavar='PROJECT_PATH_WITH_FORMAT',
            help='Project path, including formatting characters from CSV columns.'
        ),
        from_file_template: ActionParameter(
            'from',
            required=True,
            metavar='LOCAL_FILE_PATH_WITH_FORMAT',
            help='Local file path, including formatting.'
        ),
        to_file_template: ActionParameter(
            'to',
            required=True,
            metavar='REMOTE_FILE_PATH_WITH_FORMAT',
            help='Remote file path, including formatting.'
        ),
        branch: ActionParameter(
            'branch',
            default='master',
            metavar='BRANCH',
            help='Branch to commit to, defaults to master.'
        ),
        commit_message_template: ActionParameter(
            'message',
            default='Updating {GL[target_filename]}',
            metavar='COMMIT_MESSAGE_WITH_FORMAT',
            help='Commit message, including formatting.'
        ),
        force_commit: ActionParameter(
            'force-commit',
            default=False,
            action='store_true',
            help='Do not check current file content, always upload.'
        )
    ):
    for user in users:
        project_path = project_template.format(**user.row)
        from_file = from_file_template.format(**user.row)
        to_file = to_file_template.format(**user.row)
        extras = {
            'target_filename': to_file,
        }
        commit_message = commit_message_template.format(GL=extras, **user.row)

        try:
            project = mg.get_canonical_project(glb, project_path)
        except gitlab.exceptions.GitlabGetError:
            print("WARNING: project {} not found!".format(project_path), file=sys.stderr)
            continue
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

def action_clone(
        glb,
        users,
        project_template: ActionParameter(
            'project',
            required=True,
            metavar='PROJECT_PATH_WITH_FORMAT',
            help='Project path, including formatting characters from CSV columns.'
        ),
        local_path_template: ActionParameter(
            'to',
            required=True,
            metavar='LOCAL_PATH_WITH_FORMAT',
            help='Local repository path, including formatting characters from CSV columns.'
        ),
        branch: ActionParameter(
            'branch',
            default='master',
            metavar='BRANCH',
            help='Branch to clone, defaults to master.'
        ),
        commit: ActionParameter(
            'commit',
            default=None,
            metavar='COMMIT_WITH_FORMAT',
            help='Commit to reset to after clone.'
        ),
        deadline: ActionParameter(
            'deadline',
            default='now',
            metavar='YYYY-MM-DDTHH:MM:SSZ',
            help='Submission deadline, take last commit before deadline (defaults to now).'
        )
    ):
    # FIXME: commit and deadline are mutually exclusive

    if deadline == 'now':
        deadline = time.strftime('%Y-%m-%dT%H:%M:%S%z')

    for user in users:
        project = mg.get_canonical_project(glb, project_template.format(**user.row))
        local_path = local_path_template.format(**user.row)

        if commit:
            last_commit = project.commits.get(commit.format(**user.row))
        else:
            last_commit = mg.get_commit_before_deadline(glb, project, deadline, branch)
        mg.clone_or_fetch(glb, project, local_path)
        mg.reset_to_commit(local_path, last_commit.id)


def action_deadline_commits(
        glb,
        users,
        project_template: ActionParameter(
            'project',
            required=True,
            metavar='PROJECT_PATH_WITH_FORMAT',
            help='Project path, including formatting characters from CSV columns.'
        ),
        branch: ActionParameter(
            'branch',
            default='master',
            metavar='BRANCH',
            help='Branch name, defaults to master.'
        ),
        deadline: ActionParameter(
            'deadline',
            default='now',
            metavar='YYYY-MM-DDTHH:MM:SSZ',
            help='Submission deadline, take last commit before deadline (defaults to now).'
        ),
        output_header: ActionParameter(
            'first-line',
            default='login,commit',
            metavar='OUTPUT_HEADER',
            help='First line for the output.'
        ),
        output_template: ActionParameter(
            'format',
            default='{login},{commit.id}',
            metavar='OUTPUT_ROW_WITH_FORMAT',
            help='Formatting for the output row, defaults to {login},{commit.id}.'
        ),
        output_filename: ActionParameter(
            'output',
            default=None,
            metavar='OUTPUT_FILENAME',
            help='Output file, defaults to stdout.'
        )
    ):
    if output_filename:
        output = open(output_filename, 'w')
    else:
        output = sys.stdout

    if deadline == 'now':
        deadline = time.strftime('%Y-%m-%dT%H:%M:%S%z')


    print(output_header, file=output)
    for user in users:
        project = project_template.format(**user.row)
        try:
            last_commit = mg.get_commit_before_deadline(glb, project, deadline, branch)
            line = output_template.format(commit=last_commit, **user.row)
            print(line, file=output)
        except gitlab.exceptions.GitlabGetError:
            print("WARNING: project {} not found!".format(project), file=sys.stderr)
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

    register_command(
        'get-file',
        'Get file from multiple repos.',
        action_get_file,
        args_sub,
        args_common,
        args_users
    )
    register_command(
        'fork',
        'Fork one repo multiple times.',
        action_fork,
        args_sub,
        args_common,
        args_users
    )
    register_command(
        'unprotect',
        'Unprotect branch on multiple projects.',
        action_unprotect_branch,
        args_sub,
        args_common,
        args_users
    )
    register_command(
        'protect',
        'Set branch protection on multiple projects.',
        action_set_branch_protection,
        args_sub,
        args_common,
        args_users
    )
    register_command(
        'add-member',
        'Add member on multiple projects.',
        action_add_member,
        args_sub,
        args_common,
        args_users
    )
    register_command(
        'put-file',
        'Upload file to multiple repos.',
        action_put_file,
        args_sub,
        args_common,
        args_users
    )
    register_command(
        'clone',
        'Clone multiple repos.',
        action_clone,
        args_sub,
        args_common,
        args_users
    )
    register_command(
        'deadline-commit',
        'Get last commits before deadline.',
        action_deadline_commits,
        args_sub,
        args_common,
        args_users
    )

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
    else:
        users = None

    if hasattr(config, 'func'):
        config.func(glb, users, config)
    elif config.action == 'accounts':
        action_accounts(users)
    else:
        raise Exception("Unknown action.")

if __name__ == '__main__':
    main()
