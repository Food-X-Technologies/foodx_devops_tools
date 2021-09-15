#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

"""File maintainer utility."""

import asyncio
import datetime
import enum
import functools
import logging
import os
import pathlib
import shutil
import sys
import typing

import click

from foodx_devops_tools._version import acquire_version

from ._declarations import (
    DEFAULT_CONSOLE_LOGGING_ENABLED,
    DEFAULT_FILE_LOGGING_DISABLED,
    DEFAULT_LOG_LEVEL,
    VALID_LOG_LEVELS,
)
from ._logging import LoggingState

log = logging.getLogger(__name__)

DEFAULT_LOG_FILE = pathlib.Path("file_maintainer.log")
MAX_DELETE_ITEMS = 10


@enum.unique
class ExitState(enum.Enum):
    """Maintain console utility exit states."""

    UNKNOWN = enum.auto()


def _get_filesystem_capacity_used(directory: pathlib.Path) -> int:
    """
    Calculate the used capacity of the filesystem in percent.

    Returns:
        Percentage of capacity used.
    """
    stats = os.statvfs(directory)

    size_bytes = stats.f_frsize * stats.f_blocks
    available_bytes = stats.f_frsize * stats.f_bavail

    capacity_used_percent = int((1 - (available_bytes / size_bytes)) * 100)

    log.info("filesystem size (bytes), {0}".format(size_bytes))
    log.info("filesystem available size (bytes), {0}".format(size_bytes))

    log.info("filesystem capacity used (%), {0}".format(capacity_used_percent))

    return capacity_used_percent


T = typing.TypeVar("T", bound="RunMonitor")


class RunMonitor:
    """Maintain the iterations for when persistence is not required."""

    def __init__(
        self: T, persist_interval_minutes: typing.Optional[int]
    ) -> None:
        """Construct ``RunMonitor`` object."""
        self.__persist_interval_minutes = persist_interval_minutes
        self.__loop_count = 0

    def keep_running(self: T) -> bool:
        """Determine when to keep a loop running."""
        # if persistence is specified the loop always keeps running
        result = True
        if (self.__persist_interval_minutes is None) and (
            self.__loop_count == 0
        ):
            # increment the counter so that the next time around the loop the
            # iteration will be cancelled
            self.__loop_count += 1
            log.info("no persistence. exiting after this iteration")
        elif self.__persist_interval_minutes is None:
            # cancel iterating on the loop because the loop counter is non-zero
            log.info("cancelling iteration due to no persistence")
            result = False
        else:
            log.debug("persistence specified")

        return result

    async def sleep(self: T) -> None:
        """Sleep for an interval if necessary."""
        # only sleep when the persistence interval has been specified
        if self.__persist_interval_minutes is not None:
            duration_seconds = self.__persist_interval_minutes * 60
            log.debug(
                "sleeping for interval, {0} (seconds)".format(duration_seconds)
            )

            await asyncio.sleep(duration_seconds)
        else:
            log.info("not sleeping because no persistence specified")


async def _do_delete(this_dir: pathlib.Path) -> None:
    log.info("deleting subdirectory, {0}".format(this_dir))

    this_partial = functools.partial(pathlib.Path, ignore_errors=True)

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, shutil.rmtree, this_partial(this_dir))


async def _clean_filesystem(directory: pathlib.Path) -> None:
    subdirectories = [x for x in directory.iterdir() if x.is_dir()]
    subdirectory_ages = {
        x: datetime.datetime.fromtimestamp(x.stat().st_mtime)
        for x in subdirectories
    }
    # NOTE: this only works Python >=3.7 when dict insertion order
    # preservation was implemented.
    subdirectories_by_age = {
        k: v
        for k, v in sorted(
            subdirectory_ages.items(), key=lambda item: item[1], reverse=True
        )
    }

    number_items = MAX_DELETE_ITEMS
    if len(subdirectories_by_age) <= MAX_DELETE_ITEMS:
        number_items = len(subdirectories_by_age) - 1

    delete_items = list(subdirectories_by_age.keys())[0:number_items]

    click.echo("deleting subdirectories to improve available space")
    await asyncio.gather(*[_do_delete(x) for x in delete_items])


async def _run_maintainer(
    directory: pathlib.Path,
    persist_interval_minutes: typing.Optional[int],
    threshold_percent: int,
) -> None:
    this_iteration = RunMonitor(persist_interval_minutes)
    while this_iteration.keep_running():
        capacity_used_percent = _get_filesystem_capacity_used(directory)

        if capacity_used_percent >= threshold_percent:
            click.echo(
                "capacity above threshold, {0} ({1})".format(
                    capacity_used_percent, threshold_percent
                )
            )
            await _clean_filesystem(directory)

        await this_iteration.sleep()


@click.command()
@click.version_option(version=acquire_version())
@click.argument(
    "directory",
    type=click.Path(
        exists=True,
        file_okay=False,
        dir_okay=True,
        writable=True,
        path_type=pathlib.Path,
    ),
)
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
    show_default=True,
    type=click.Choice(VALID_LOG_LEVELS, case_sensitive=False),
)
@click.option(
    "--persist-interval",
    "persist_interval_minutes",
    default=None,
    help="Persist indefinitely checking the directory on the specified "
    "interval (minutes).",
    show_default=True,
    type=int,
)
@click.option(
    "--threshold",
    default=80,
    help="Filesystem threshold to trigger clean up.",
    show_default=True,
    type=int,
)
def file_maintainer(
    directory: pathlib.Path,
    disable_file_log: bool,
    enable_console_log: bool,
    log_level: str,
    persist_interval_minutes: typing.Optional[int],
    threshold: int,
) -> None:
    """
    Delete old sub-directories from the specified directory.

    By default the utility will check the specified directory, erase relevant
    subdirectories and exit. Use the ``--persist-interval`` option for the
    utility to run indefinitely, checking the directory periodically on the
    specified interval.

    DIRECTORY:  The directory to monitor.
    """
    try:
        # currently no need to change logging configuration at run time,
        # so no need to preserve the object.
        LoggingState(
            disable_file_logging=disable_file_log,
            enable_console_logging=enable_console_log,
            log_level_text=log_level,
            default_log_file=DEFAULT_LOG_FILE,
        )

        asyncio.run(
            _run_maintainer(directory, persist_interval_minutes, threshold)
        )

        click.echo("maintainer exiting due to task completion")
    except asyncio.exceptions.CancelledError:
        log.warning("exiting due to cancellation")
        # async CancelledError exceptions should usually be re-raised
        # https://docs.python.org/3.8/library/asyncio-exceptions.html#asyncio.CancelledError
        raise
    except Exception as e:
        click.echo(
            "failed with unexpected error (see log for "
            "details), {0}".format(str(e)),
            err=True,
        )
        log.exception("unexpected error, {0}".format(str(e)))
        sys.exit(ExitState.UNKNOWN.value)


def flit_entry() -> None:
    """Flit script entry function for ``file-maintainer`` utility."""
    file_maintainer()
