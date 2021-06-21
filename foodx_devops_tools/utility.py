#
#  Copyright (c) 2020 Russell Smiley
#
#  This file is part of build_harness.
#
#  You should have received a copy of the MIT License along with build_harness.
#  If not, see <https://opensource.org/licenses/MIT>.
#
# https://gitlab.com/ci-cd-devops/build_harness/-/blob/main/build_harness/_utility.py

"""General support for build harness implementation."""

import logging
import subprocess
import typing

log = logging.getLogger(__name__)

CommandArgs = typing.List[str]


def run_command(
    command: CommandArgs, **kwargs: typing.Any
) -> subprocess.CompletedProcess:
    """
    Run a system command using ``subprocess.run``.

    Args:
        command: List of command and arguments.
        **kwargs: Optional arguments passed through to ``subprocess.run``.

    Returns:
        Subprocess results.
    """
    log.debug("command to run, {0}".format(str(command)))
    log.debug("command arguments, {0}".format(str(kwargs)))
    result = subprocess.run(command, **kwargs)

    return result
