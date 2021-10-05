#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

"""Jinja2 template application."""

import pathlib
import typing

import aiofiles
import jinja2

TemplateParameters = typing.Dict[str, typing.Any]

T = typing.TypeVar("T", bound="FrameTemplates")


class FrameTemplates:
    """Manage the template environment for a frame."""

    environment: jinja2.Environment

    def __init__(
        self: T, template_search_paths: typing.List[pathlib.Path]
    ) -> None:
        """
        Construct ``FrameTemplates`` object.

        Args:
            template_search_paths: Directory paths where templates may be found.
        """
        self.environment = jinja2.Environment(
            loader=jinja2.FileSystemLoader(template_search_paths),
            autoescape=jinja2.select_autoescape(),
        )

    async def apply_template(
        self: T,
        source_template: str,
        target_path: pathlib.Path,
        parameters: TemplateParameters,
    ) -> None:
        """
        Apply jinja2 template to a target file.

        Args:
            source_template: Name of jinja2 template.
            target_path: Target fulfilled file.
            parameters: Parameters to be consumed by the template.
        """
        template = self.environment.get_template(source_template)
        content = template.render(**parameters)
        async with aiofiles.open(target_path, mode="w") as f:
            await f.write(content)
