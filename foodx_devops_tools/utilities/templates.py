#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

"""General support for templating."""

import asyncio
import dataclasses
import logging
import pathlib

import pydantic

from foodx_devops_tools.puff import run_puff
from foodx_devops_tools.utilities.jinja2 import (
    FrameTemplates,
    TemplateParameters,
)

log = logging.getLogger(__name__)

JINJA_FILE_PREFIX = "jinja2."


class ArmTemplates(pydantic.BaseModel):
    """Collection of file paths for ARM templates."""

    source: pathlib.Path
    target: pathlib.Path

    @pydantic.root_validator()
    def check_jinja2_templating(
        cls: pydantic.BaseModel, candidate: dict
    ) -> dict:
        """Check source target patterns when jinja2 templating is not needed."""
        source = candidate.get("source")
        target = candidate.get("target")
        if (
            source
            and (not source.name.startswith(JINJA_FILE_PREFIX))
            and (source != target)
        ):
            message = (
                "source and target for non-jinja files must be "
                "identical, {0}, {1}".format(
                    source,
                    target,
                )
            )
            log.error(message)
            raise ValueError(message)

        return candidate


class ArmTemplateParameters(pydantic.BaseModel):
    """Collection of file paths for puff file and ARM template parameters."""

    source_puff: pathlib.Path
    templated_puff: pathlib.Path
    target: pathlib.Path

    @pydantic.root_validator()
    def check_jinja2_templating(
        cls: pydantic.BaseModel, candidate: dict
    ) -> dict:
        """Check source target patterns when jinja2 templating is not needed."""
        source = candidate.get("source_puff")
        target = candidate.get("templated_puff")
        if (
            source
            and (not source.name.startswith(JINJA_FILE_PREFIX))
            and (source != target)
        ):
            message = (
                "source and target for non-jinja files must be "
                "identical, {0}, {1}".format(
                    source,
                    target,
                )
            )
            log.error(message)
            raise ValueError(message)

        return candidate


@dataclasses.dataclass
class TemplateFiles:
    """Collection of file paths for template processing."""

    arm_template: ArmTemplates
    arm_template_parameters: ArmTemplateParameters


@dataclasses.dataclass
class ArmTemplateDeploymentFiles:
    """Paths to the two files needed for ARM template deployment."""

    arm_template: pathlib.Path
    parameters: pathlib.Path


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


async def _apply_jinja2_file(
    template_environment: FrameTemplates,
    source_file: pathlib.Path,
    target_directory: pathlib.Path,
    parameters: TemplateParameters,
) -> pathlib.Path:
    """Apply Jinja2 to an ARM template related file."""
    if source_file.name.startswith(JINJA_FILE_PREFIX):
        templated_file = await _apply_template(
            template_environment, source_file, target_directory, parameters
        )
    else:
        templated_file = source_file

    return templated_file


async def prepare_deployment_files(
    template_files: TemplateFiles,
    parameters: TemplateParameters,
) -> ArmTemplateDeploymentFiles:
    """Prepare final ARM template and parameter files for deployment."""
    source_arm_template_path = template_files.arm_template.source
    source_puff_file_path = template_files.arm_template_parameters.source_puff
    template_environment = FrameTemplates(
        # folders containing _source_ files
        list({source_arm_template_path.parent, source_puff_file_path.parent})
    )
    template_environment.environment.filters["json_inlining"] = json_inlining

    arm_target_directory = template_files.arm_template.target.parent
    log.debug(f"arm templating output target directory, {arm_target_directory}")
    puff_target_directory = template_files.arm_template_parameters.target.parent
    log.debug(
        f"puff templating output target directory," f" {puff_target_directory}"
    )

    log.info(f"applying jinja2 to puff file, {source_puff_file_path}")
    log.info(
        f"applying jinja2 to ARM template file, {source_arm_template_path}"
    )
    futures = await asyncio.gather(
        _apply_jinja2_file(
            template_environment,
            source_puff_file_path,
            puff_target_directory,
            parameters,
        ),
        _apply_jinja2_file(
            template_environment,
            source_arm_template_path,
            arm_target_directory,
            parameters,
        ),
    )
    templated_puff = futures[0]
    templated_arm = futures[1]
    # now transform the jinja2 processed puff file to arm template parameter
    # json files.
    await run_puff(
        templated_puff,
        False,
        False,
        disable_ascii_art=True,
        output_dir=puff_target_directory,
    )
    result = ArmTemplateDeploymentFiles(
        arm_template=templated_arm,
        parameters=template_files.arm_template_parameters.target,
    )
    return result
