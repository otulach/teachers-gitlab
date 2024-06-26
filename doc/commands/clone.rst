Cloning multiple repositories
=============================

The `clone` subcommand allows you to clone multiple repositories at once and
also to reset each clone to a particular commit.

.. code-block:: shell

  -h, --help            show this help message and exit
  --debug               Print debugging messages.
  --config-file GITLAB_CONFIG_FILE
                        GitLab configuration file.
  --instance GITLAB_INSTANCE
                        Which GitLab instance to choose.
  --users LIST.csv, --entries LIST.csv
                        CSV with entries on which to perform an action
  --project PROJECT_PATH_WITH_FORMAT
                        Project path, formatted from CSV columns.
  --to LOCAL_PATH_WITH_FORMAT
                        Local repository path, formatted from CSV columns.
  --branch BRANCH       Branch to clone, defaults to master.
  --commit COMMIT_WITH_FORMAT
                        Commit to reset to after clone.
  --deadline YYYY-MM-DDTHH:MM:SSZ
                        Submission deadline (defaults to now).
  --blacklist BLACKLIST
                        Commit authors to ignore (regular expression).

