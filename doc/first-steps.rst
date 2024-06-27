First steps with Teachers GitLab
================================

The script expects a configuration file for Python GitLab
format (`config.ini` in the following examples):

.. code-block:: ini

    [global]
    default = mff
    ssl_verify = true
    timeout = 5

    [mff]
    url = https://gitlab.mff.cuni.cz/
    private_token = your-private-token



Generally, the script expects that the user has a CSV file with
list of students on which to operate.

The CSV can be as simple as the following one and usually a teacher
will get it from their student information system.
