#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

"""Manage .puffignore data and methods."""

import copy
import logging
import pathlib
import typing

import aiofiles  # type: ignore

log = logging.getLogger(__name__)

BASE_IGNORE = ["**/node_modules/**/*"]

IgnorePatterns = typing.List[str]


async def load_puffignore(puffignore_path: pathlib.Path) -> IgnorePatterns:
    """
    Load .puffignore data from current working directory.

    A non-existent or empty .puffignore file is silently ignored.

    Returns:
        Loaded ignore patterns or empty list.
    """
    try:
        async with aiofiles.open(str(puffignore_path), mode="r") as f:
            lines = await f.readlines()
    except FileNotFoundError:
        log.info(
            "No .puffignore file found, {0}".format(puffignore_path.absolute())
        )
        lines = list()

    filtered_lines = copy.deepcopy(BASE_IGNORE)
    for this_line in lines:
        stripped_line = this_line.strip()
        if stripped_line and not stripped_line.startswith("#"):
            if stripped_line.endswith("/"):
                # append wildcard
                filtered_lines.append(stripped_line + "*")
            else:
                filtered_lines.append(stripped_line)

    return filtered_lines
