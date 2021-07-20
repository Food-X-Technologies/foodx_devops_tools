#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

import contextlib
import os
import pathlib

import pytest
from click.testing import CliRunner


@pytest.fixture()
def click_runner() -> CliRunner:
    return CliRunner()


@contextlib.contextmanager
def isolated_filesystem(expected_dir, mock_runner):
    with mock_runner.isolated_filesystem():
        os.makedirs(expected_dir)

        yield pathlib.Path(expected_dir).absolute()
