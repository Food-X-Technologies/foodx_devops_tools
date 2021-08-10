#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

"""Core implementation of ``puff`` utility."""

import asyncio
import dataclasses
import enum
import logging
import pathlib
import typing

import click

from ._ascii_art import JELLY, PUFFIN
from ._exceptions import PuffError
from .arm import do_arm_template_parameter_action
from .puffignore import IgnorePatterns, load_puffignore

log = logging.getLogger(__name__)

GENERATING_MESSAGE = "generating files..."
DELETING_MESSAGE = "deleting generated files..."


@enum.unique
class PuffActions(enum.Enum):
    """Puff utility action types."""

    create = enum.auto()
    delete = enum.auto()


@dataclasses.dataclass
class ActionConfiguration:
    """Configuration defining puff actions."""

    message: str
    art: str


ACTION_MESSAGES = {
    PuffActions.create: ActionConfiguration(
        message=GENERATING_MESSAGE, art=JELLY
    ),
    PuffActions.delete: ActionConfiguration(
        message=DELETING_MESSAGE, art=PUFFIN
    ),
}
DEFAULT_PUFFIGNORE_PATH = pathlib.Path("./.puffignore")

YamlFilenames = typing.Set[pathlib.Path]


def _acquire_yaml_filenames(
    path: pathlib.Path, ignore_patterns: IgnorePatterns
) -> YamlFilenames:
    """
    Collect paths to YAML files under root path.

    Args:
        path: Root path to search recursively.
        ignore_patterns: Unix style globs to exclude from search results.

    Returns:
        Discovered YAML file names excluding those matching ignore patterns.
    """
    yaml_files = set(path.glob("**/*.yml")).union(set(path.glob("**/*.yaml")))
    for this_pattern in ignore_patterns:
        yaml_files = yaml_files.difference(path.glob(this_pattern))

    return yaml_files


async def run_puff(
    path: pathlib.Path, is_delete_files: bool, is_pretty: bool
) -> None:
    """
    Search filesystem for YAML files and create or delete ARM template files.

    Args:
        path: Root path to search recursively for YAML files.
        is_delete_files: Enable/disable delete instead of create action.
        is_pretty: Create nicely formatted JSON for humans.
    """
    if is_delete_files:
        this_action = PuffActions.delete
    else:
        this_action = PuffActions.create

    click.echo(ACTION_MESSAGES[this_action].art)
    click.echo(ACTION_MESSAGES[this_action].message)

    ignore_patterns = await load_puffignore(DEFAULT_PUFFIGNORE_PATH)
    if path.is_dir():
        yaml_filenames = _acquire_yaml_filenames(path, ignore_patterns)
    elif path.is_file():
        yaml_filenames = {path}
    else:
        raise PuffError("Path must be file or directory, {0}".format(path))

    log.debug(str(yaml_filenames))

    if not yaml_filenames:
        log.warning(
            "No puff parameter files found in directory, {0}".format(path)
        )

    await asyncio.gather(
        *[
            do_arm_template_parameter_action(x, is_delete_files, is_pretty)
            for x in yaml_filenames
        ]
    )
