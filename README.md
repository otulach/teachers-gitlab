# Teachers GitLab for mass actions on GitLab

Utilities to help you manage multiple repositories at once.
Targets teachers that need to manage separate repository for each
student and massively fork, clone or upload files to them.

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
the following contents:

```csv
email,login,number
student1@mff.cuni.cz,student1,1
student2@mff.cuni.cz,student2,2
```

## `fork`

Fork repository for all users given in a CSV file.

```shell
./teachers_gitlab.py fork \
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

## `unprotect`

Remove branch protection, typically needed for `master` branch
in simple setups.

Assuming the same input files as in `fork`, following command
unprotects `master` branch for all repositories from the previous
step.

```shell
./teachers_gitlab.py unprotect \
    --config-file config.ini \
    --users students.csv \
    --project "teaching/nswi177/2020-summer/solution-{number}-{login}" \
    --branch master
```

## `add-member`

Add member to a project. Typically called after `fork` (see above).

Adding users to their repositories from the example above is done with

```shell
./teachers_gitlab.py add-member \
    --config-file config.ini \
    --users students.csv \
    --project "teaching/nswi177/2020-summer/solution-{number}-{login}" \
    --access-level devel
```
