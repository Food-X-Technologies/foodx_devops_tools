foodx_devops_tools
==================

Foodx DevOps pipeline utilities.

.. contents::

.. section-numbering::


Installation
------------

The ``foodx_devops_tools`` package is available from PyPI. Installing into a virtual
environment is recommended.

.. code-block::

   python3 -m venv .venv; .venv/bin/pip install foodx_devops_tools


Developers
----------

The first time you clone this project use the following command to set up the virtual environment for the project.
Ensure that you have Python3, git and the Python package venv installed on your system.

Note that while ``venv`` is in the Python standard library, in Ubuntu it is not installed with the standard Python 3
apt package so you must explicitly install it with ``sudo apt install python3-venv``.

.. code-block::

   git clone <foodx_devops_tools repo url>
   cd foodx_devops_tools
   python3 -m venv .venv; .venv/bin/pip install build_harness; .venv/bin/build-harness install

Run the same static analysis as the pipeline using the ``build-harness`` utility:

.. code-block::

   # apply PEP-8 formatting to the code (mandatory as the pipeline will fail if not PEP-8 compliant formatting)
   build-harness formatting
   # apply formatting and then do additional static checks using flake8, mypy and pydocstyle
   build-harness static-analysis
   # run unit tests - for this project the test dir specification is necessary to avoid running manual tests
   build-harness unit-test --test-dir tests/ci
   # generate unit test coverage report
   build-harness unit-test --test-dir tests/ci --coverage-html

Examine the ``.gitlab-ci.yml`` file for more examples of using the ``build-harness`` utility.
