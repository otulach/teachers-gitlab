# MFF GitLab utilities

Few helper scripts to setup repositories for students.

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

## `fork`

Fork repository for all users given in a CSV file.

Assuming CSV file with students in format

```
email,login,number
student1@mff.cuni.cz,student1,1
student2@mff.cuni.cz,student2,2
```

running

```shell
./mff-gitlab.py fork \
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
./mff-gitlab.py unprotect \
    --config-file config.ini \
    --users students.csv \
    --project "teaching/nswi177/2020-summer/solution-{number}-{login}" \
    --branch master
```

## `add-member`

Add member to a project. Typically called after `fork` (see above).

Adding users to their repositories from the example above is done with

```shell
./mff-gitlab.py add-member \
    --config-file config.ini \
    --users students.csv \
    --project "teaching/nswi177/2020-summer/solution-{number}-{login}" \
    --access-level devel
```
