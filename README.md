# Teachers GitLab for mass actions on GitLab

Utilities to help you manage multiple repositories at once.
Targets teachers that need to manage separate repository for each
student and massively fork, clone or upload files to them.

## Installation

It is possible to install the script via:

```shell
pip install -r requirements.txt
./setup.py build
./setup.py install
```

This will give you `teachers_gitlab` on your `$PATH`. You can also
use `virtualenv` to test locally or use the provided shell script
wrapper (as used in the examples) which sets up a virtual
environment automatically.

## Configuration

The script expects a configuration file for Python GitLab
format (`config.ini` in the following examples):

```ini
[global]
default = mff
ssl_verify = true
timeout = 5

[mff]
url = https://gitlab.mff.cuni.cz/
private_token = your-private-token
```

Generally, the script expects that the user has a CSV file with
list of students on which to operate.

For the following examples, we will assume CSV `students.csv` with
the following contents (similar CSV can be generated from SIS,
use the "Studenti předběžně zapsaní na předmět" query in
"Studijní sestavy"):

```csv
email,login,number
student1@mff.cuni.cz,student1,1
student2@mff.cuni.cz,student2,2
```
## Template parameters

Some command line parameters accept a template value that is
really a Python format string. Where applicable, these template
arguments are evaluated for each user record, providing some 
usage flexibility, especially when it comes to mass operations.

For example, using `--project student-{login}` in an action such
as **add-member** will perform the operation on multiple projects
corresponding to user login names.


## `fork`

Fork repository for all users given in a CSV file.

```shell
./teachers_gitlab.sh fork \
    --config-file config.ini \
    --users students.csv \
    --from teaching/course/upstream/template \
    --to "teaching/course/student-{number}-{login}" \
    --hide-fork
```

will fork the `teaching/course/upstream/template` into
repositories `teaching/course/student-1-student1`
and `teaching/course/student-2-student2`, removing the
fork relationship.


## `protect`

Create a protected branch (or pattern).

Assuming the same input files as in `fork`, the following command
protects `master` branch for all repositories from the previous
step but allows developers to push and merge

```shell
./teachers_gitlab.sh protect \
    --config-file config.ini \
    --users students.csv \
    --project "teaching/nswi177/2020-summer/solution-{number}-{login}" \
    --branch master \
    --merge-access-level developer \
    --push-access-level developer
```

## `unprotect`

Remove a protected branch (or pattern).

Typically needed for the `master` branch in simple setups.

Assuming the same input files as in `fork`, the following command
unprotects `master` branch for all repositories from the previous
step.

```shell
./teachers_gitlab.sh unprotect \
    --config-file config.ini \
    --users students.csv \
    --project "teaching/nswi177/2020-summer/solution-{number}-{login}" \
    --branch master
```

## `protect-tag`

Create a protected tag (or pattern).

Typically used for automatically created checkpoint tags.

```shell
./teachers_gitlab.sh protect-tag \
    --config-file config.ini \
    --users students.csv \
    --project "teaching/nswi004/2022/student-{login}" \
    --tag 'checkpoint/*' \
    --create-access-level maintainer
```

## `unprotect-tag`

Remove a protected tag (or pattern).

```shell
./teachers_gitlab.sh unprotect-tag \
    --config-file config.ini \
    --users students.csv \
    --project "teaching/nswi004/2022/student-{login}" \
    --tag 'checkpoint/*'
```

## `add-member`

Add member(s) to project(s). Typically called after `fork` (see
above), but also to add students to shared projects.

Adding students to their course projects can be done with

```shell
./teachers_gitlab.sh add-member \
    --config-file config.ini \
    --users students.csv \
    --project "teaching/nswi177/2020-summer/solution-{number}-{login}" \
    --access-level developer
```

Adding students to a common project can be done with

```shell
./teachers_gitlab.sh add-member \
    --config-file config.ini \
    --users students.csv \
    --project "teaching/nswi004/upstream/forum" \
    --access-level reporter
```

## `remove-member`

Remove member(s) from project(s). Typically used to remove
students from past course runs or students who have dropped out.

Removing students from a common project can be done with

```shell
./teachers_gitlab.sh remove-member \
    --config-file config.ini \
    --users students.csv \
    --project "teaching/nswi004/2022/upstream/forum"
```

Removing students from their course projects can be done with

```shell
./teachers_gitlab.sh remove-member \
    --config-file config.ini \
    --users students.csv \
    --project "teaching/nswi004/2022/student-{login}"
```

## `clone`

Clone project to local disk. It is possible to specify a deadline to
checkout to a specific commit (last before given deadline).

```shell
./teachers_gitlab.sh clone \
    --config-file config.ini \
    --users students.csv \
    --project "teaching/nswi177/2020-summer/solution-{number}-{login}" \
    --to "solutions/01-{number}-{login}" \
    --deadline '2020-01-01T00:00:00Z'
```

## `deadline-commit`

Get last commits before a given deadline.

By default, it generates a CSV with logins and commit ids.

```shell
./teachers_gitlab.sh deadline-commit \
    --config-file config.ini \
    --users students.csv \
    --project "teaching/nswi177/2020-summer/solution-{number}-{login}" \
    --deadline '2020-01-01T00:00:00Z' \
    --output commits_01.csv \
    --first-line 'login,number,commit' \
    --format '{login},{number},{commit.id}'
```

## `get-file`

Get specific file before a given deadline.

```shell
./teachers_gitlab.sh get-file \
    --config-file config.ini \
    --users students.csv \
    --project "teaching/nswi177/2020-summer/solution-{number}-{login}" \
    --deadline '2020-01-01T00:00:00Z' \
    --remote-file "quiz-01.json" \
    --local-file "quiz-01-{login}.json"
```

## `get-last-pipeline`

Get status of last pipeline as JSON.

```shell
./teachers_gitlab.sh get-file \
    --config-file config.ini \
    --users students.csv \
    --project "teaching/nswi177/2020-summer/solution-{number}-{login}"
```

```shell
./teachers_gitlab.sh get-file \
    --config-file config.ini \
    --users students.csv \
    --project "teaching/nswi177/2020-summer/solution-{number}-{login}" \
    --summary-only
```

## `get-pipeline-at-commit`

Get status of the first non-skipped pipeline at or prior to specified commit as JSON.

```shell
./teachers_gitlab.sh get-pipeline-at-commit \
    --config-file config.ini \
    --users students.csv \
    --project "teaching/nswi177/2021-summer/student-{login}" \
    --commits "grading/results/commits.13.csv"
```

## `commit-stats`

Overview of all commits, including line statistics, as JSON.

```shell
./teachers_gitlab.sh commit-stats \
    --config-file config.ini \
    --users students.csv \
    --project "teaching/nswi177/2020-summer/solution-{number}-{login}"
```
