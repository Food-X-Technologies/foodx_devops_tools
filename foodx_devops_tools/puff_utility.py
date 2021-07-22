#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

"""Python clone of node.js puff utility."""

import asyncio
import enum
import logging
import pathlib
import sys

import click
import click_log  # type: ignore

from foodx_devops_tools._version import acquire_version

from .puff import PuffError, run_puff

log = logging.getLogger(__name__)
click_log.basic_config(log)


@enum.unique
class ExitState(enum.Enum):
    """Numeric script exit states."""

    UNKNOWN = 100
    PUFF_FAILED = 101


async def do_run(
    path: pathlib.Path, is_delete_files: bool, is_pretty: bool
) -> None:
    """
    Create or delete puff generated ARM template JSON files.

    Args:
        path: Root directory path to walk.
        is_delete_files: Flag enabling deleting files instead of creating.
        is_pretty: Create nicely formatted JSON for humans.
    """
    await run_puff(path, is_delete_files, is_pretty)


@click.command()
@click_log.simple_verbosity_option(log)
@click.version_option(version=acquire_version())
@click.argument(
    "path",
    type=click.Path(exists=True, file_okay=True, dir_okay=True),
)
@click.option(
    "--delete",
    "-d",
    default=False,
    help="Delete files that were generated.",
    is_flag=True,
    show_default=True,
)
@click.option(
    "--pretty",
    default=False,
    help="Create nicely formatted JSON for humans.",
    is_flag=True,
    show_default=True,
)
def _main(path: str, delete: bool, pretty: bool) -> None:
    """
    Create or delete ARM template parameter files from puff YAML configuration.

    If a directory is specified, all the yaml files in the directory (
    recursively) are assumed to be puff parameter files. If a file is
    specified then just the file is assumed to be a puff parameter file and
    in this case the json files are generated to the parameter files parent
    directory.

    PATH Directory or file path for finding yml files to generate from.
    """
    try:
        asyncio.run(do_run(pathlib.Path(path), delete, pretty))
    except PuffError as e:
        click.echo(str(e), err=True)
        sys.exit(ExitState.PUFF_FAILED.value)
    except asyncio.exceptions.CancelledError:
        log.warning("Exiting due to cancellation")
        # async CancelledError exceptions should usually be re-raised
        # https://docs.python.org/3.8/library/asyncio-exceptions.html#asyncio.CancelledError
        raise
    except Exception as e:
        log.error("Unexpected error, {0}".format(str(e)))
        sys.exit(ExitState.UNKNOWN.value)


def entrypoint() -> None:
    """Flit entry point."""
    _main()
