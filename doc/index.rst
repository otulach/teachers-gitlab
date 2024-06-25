Teachers GitLab
===============

A Python utility to help you manage multiple repositories at once.

Our target users are teachers that need to manage separate repository for
each student and massively fork, clone or upload files to them.

A typical scenario is that you have a CSV with your students that can look
like this (in ``students.csv`` file):

.. code-block:: text

    name,login,group
    Harry,harry,gryff
    Hermiona,herm,gryff
    Draco,draco,slyth
    ...

Then you can execute the following to fork your base project (that may
contain assignment description and project configuration with some tests,
for example) for all students.

.. code-block:: shell

    teachers_gitlab \
        fork \
        --entries students.csv \
        --from 'courses/software-magic/base' \
        --to 'courses/software-magic/students/{group}/{login}' \

Once this program finishes, there will be forked projects ``gryff/harry``,
``gryff/herm`` and ``slyth/draco``.

Typically you will then assign students to their projects and you are ready
to go.

.. code-block:: shell

    teachers_gitlab \
        add-member \
        --entries students.csv \
        --project 'courses/software-magic/students/{group}/{login}' \
        --access-level devel

A new student enrolled? Simply run the above commands again: existing projects
will be skipped and only new members will be added.


Table of Contents
-----------------

.. toctree::
   :maxdepth: 2

   install
   development
