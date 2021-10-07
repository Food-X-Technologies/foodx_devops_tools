#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

"""General support for templating."""

import logging
import pathlib
import typing

from foodx_devops_tools.puff import run_puff
from foodx_devops_tools.utilities.jinja2 import (
    FrameTemplates,
    TemplateParameters,
)

log = logging.getLogger(__name__)

JINJA_FILE_PREFIX = "jinja2."


def json_inlining(content: str) -> str:
    """
    Inline text content for inclusion in a JSON file (ARM template).

    Escape double quotes and retain newlines as escapes to embody the content
    in a single line.

    Args:
        content: Content to be "inlined".

    Returns:
        Modified content.
    """
    escaped_newlines = repr(content).strip("'").replace(r"\n", r"\n")
    escaped_quotes = escaped_newlines.replace('"', r"\"")

    return escaped_quotes


async def _apply_template(
    template_environment: FrameTemplates,
    source_file: pathlib.Path,
    target_directory: pathlib.Path,
    parameters: TemplateParameters,
) -> pathlib.Path:
    """
    Apply frame-specific template and parameters ready for deployment.

    Args:
        template_environment:   Frame-specific template environment.
        source_file:            Source template file.
        target_directory:       Target directory in which to store fulfilled
                                template file.
        parameters:             Parameter to apply to the template file.

    Returns:
        Target file path of the fulfilled template.
    """
    target_name = source_file.name.replace(JINJA_FILE_PREFIX, "")
    target_file = target_directory / target_name

    log.debug(
        "Applying jinja2 templating, {0} (source), "
        "{1} (destination)".format(source_file, target_file)
    )
    await template_environment.apply_template(
        source_file.name, target_file, parameters
    )

    return target_file


async def prepare_deployment_files(
    puff_file_path: pathlib.Path,
    arm_template_path: pathlib.Path,
    target_arm_path: pathlib.Path,
    parameters: TemplateParameters,
) -> typing.Tuple[pathlib.Path, pathlib.Path]:
    """Prepare final ARM template and parameter files for deployment."""
    template_environment = FrameTemplates(
        [puff_file_path.parent, arm_template_path.parent]
    )
    template_environment.environment.filters["json_inlining"] = json_inlining

    target_directory = target_arm_path.parent
    log.debug(f"templating output target directory, {target_directory}")
    if puff_file_path.name.startswith(JINJA_FILE_PREFIX):
        log.info(f"applying jinja2 to puff file, {puff_file_path}")
        templated_puff = await _apply_template(
            template_environment, puff_file_path, target_directory, parameters
        )
    else:
        templated_puff = puff_file_path

    if arm_template_path.name.startswith(JINJA_FILE_PREFIX):
        log.info(f"applying jinja2 to ARM template file, {arm_template_path}")
        templated_arm = await _apply_template(
            template_environment,
            arm_template_path,
            target_directory,
            parameters,
        )
    else:
        templated_arm = arm_template_path

    await run_puff(templated_puff, False, False, disable_ascii_art=True)

    return templated_arm, templated_puff
