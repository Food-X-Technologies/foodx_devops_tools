#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

"""Manage templating of deployment definitions."""

import pathlib
import re

import aiofiles  # type: ignore

ESCOLAR_REGEX = r"(?P<reference>#(?P<file_path>.+?)#)"


async def _do_substitutions(source_content: str) -> str:
    escolards = re.finditer(ESCOLAR_REGEX, source_content)

    modified_content = source_content
    for occurrence in escolards:
        snippet_file = pathlib.Path(occurrence.group("file_path"))
        async with aiofiles.open(snippet_file, mode="r") as f:
            snippet_content = await f.read()
            # escape double quotes and retain newlines as escapes to embody
            # the snippet in a single line
            escaped_newlines = (
                repr(snippet_content).strip("'").replace(r"\n", r"\\n")
            )
            escaped_quotes = escaped_newlines.replace('"', r'\\"')
            modified_content = re.sub(
                occurrence.group("reference"), escaped_quotes, modified_content
            )

    return modified_content


async def do_snippet_substitution(
    source_file: pathlib.Path, destination_file: pathlib.Path
) -> None:
    """
    Apply template parameters.

    Presently uses the legacy "escolar" way of doing template substitution.
    """
    async with aiofiles.open(source_file, mode="r") as source:
        source_content = await source.read()

    modified_content = await _do_substitutions(source_content)

    async with aiofiles.open(destination_file, mode="w") as target:
        await target.writelines(modified_content)
