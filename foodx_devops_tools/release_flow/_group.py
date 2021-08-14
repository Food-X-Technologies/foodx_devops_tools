#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

import pathlib

import click

from foodx_devops_tools._declarations import (
    DEFAULT_CONSOLE_LOGGING_ENABLED,
    DEFAULT_FILE_LOGGING_DISABLED,
    DEFAULT_LOG_LEVEL,
    VALID_LOG_LEVELS,
)
from foodx_devops_tools._logging import LoggingState
from foodx_devops_tools._version import acquire_version

from .azure_cd import azure_subcommand
from .npm_ci import npm_subcommand

DEFAULT_LOG_FILE = pathlib.Path("puff_run.log")


@click.group()
@click.version_option(version=acquire_version())
@click.option(
    "--log-enable-console",
    "enable_console_log",
    default=DEFAULT_CONSOLE_LOGGING_ENABLED,
    help="Log to console.",
    is_flag=True,
)
@click.option(
    "--log-disable-file",
    "disable_file_log",
    default=DEFAULT_FILE_LOGGING_DISABLED,
    help="Disable file logging.",
    is_flag=True,
)
@click.option(
    "--log-level",
    "log_level",
    default=DEFAULT_LOG_LEVEL,
    help="Select logging level to apply to all enabled log sinks.",
    type=click.Choice(VALID_LOG_LEVELS, case_sensitive=False),
)
def release_flow(
    disable_file_log: bool, enable_console_log: bool, log_level: str
) -> None:
    """Release flow command group."""
    # currently no need to change logging configuration at run time,
    # so no need to preserve the object.
    LoggingState(
        disable_file_logging=disable_file_log,
        enable_console_logging=enable_console_log,
        log_level_text=log_level,
        default_log_file=DEFAULT_LOG_FILE,
    )


release_flow.add_command(azure_subcommand, name="azure")
release_flow.add_command(npm_subcommand, name="npm")
