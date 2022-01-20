#  Copyright (c) 2022 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

import logging

import click

from foodx_devops_tools.pipeline_config import FlattenedDeployment
from foodx_devops_tools.pipeline_config.frames import ApplicationStepScript
from foodx_devops_tools.utilities.command import run_async_command
from foodx_devops_tools.utilities.jinja2 import apply_dynamic_template

log = logging.getLogger(__name__)


async def script_step(
    this_step: ApplicationStepScript,
    deployment_data: FlattenedDeployment,
    this_context: str,
) -> None:
    """
    Run command line commands in Bash shell.

    Args:
        this_step: Deployment definition for this step action.
        deployment_data: Deployment context related parameters.
        this_context: Structured string context id.
    """
    step_context = f"{this_context}.{this_step.name}"

    log.debug(
        f"deployment_data.context, "
        f"{step_context}, {str(deployment_data.context)}"
    )
    log.debug(
        f"deployment_data.data, {step_context}, "
        f"{str(deployment_data.data.deployment_tuple)}, "
        f"{str(deployment_data.data.location_primary)}, "
        f"{str(deployment_data.data.location_secondary)}, "
        f"{str(deployment_data.data.release_state)}, "
        f"{str(deployment_data.data.iteration_context)}"
    )
    try:
        template_parameters = deployment_data.construct_template_parameters()
        log.debug(f"template parameters, {step_context}, {template_parameters}")

        templated_inline_script = apply_dynamic_template(
            this_step.script, template_parameters
        )
        this_command = [
            "/bin/bash",
            "-c",
            templated_inline_script,
        ]
        await run_async_command(this_command)

    except Exception as e:
        message = f"step shell script failed, {step_context}, {str(e)}"
        log.error(message)
        click.echo(click.style(message, fg="red"), err=True)
        raise
