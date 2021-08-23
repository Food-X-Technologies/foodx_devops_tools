#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.
#
#  This file is part of build_harness.
#
#  You should have received a copy of the MIT License along with build_harness.
#  If not, see <https://opensource.org/licenses/MIT>.
#
# https://gitlab.com/ci-cd-devops/build_harness/-/blob/main/build_harness/_utility.py

"""General support for build harness implementation."""

import asyncio
import dataclasses
import logging
import subprocess
import typing

from ._exceptions import CommandError

log = logging.getLogger(__name__)

CommandArgs = typing.List[str]


@dataclasses.dataclass()
class CapturedStreams:
    """Encapsulate output and error streams captured from a process."""

    out: str
    error: str


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


async def run_async_command(command: CommandArgs) -> CapturedStreams:
    """
    Run an external command asynchronously.

    Args:
        command: Command to be executed.

    Returns:
        Any output or error streams captured from the process.
    """
    log.debug("command to run, {0}".format(str(command)))
    this_process = await asyncio.create_subprocess_exec(
        *command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )

    stdout, stderr = await this_process.communicate()
    result = CapturedStreams(
        out=stdout.decode("utf-8"), error=stderr.decode("utf-8")
    )
    if this_process.returncode != 0:
        raise CommandError(
            "External command run did not exit cleanly, {0}".format(
                result.error
            )
        )
    return result
