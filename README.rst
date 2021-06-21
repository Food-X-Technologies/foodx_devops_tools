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
