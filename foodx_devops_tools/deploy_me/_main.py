#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

import asyncio
import logging
import pathlib
import sys
import typing

import click

from foodx_devops_tools._paths import (
    ConfigurationPathsError,
    acquire_configuration_paths,
)
from foodx_devops_tools._version import acquire_version
from foodx_devops_tools.pipeline_config import (
    DeploymentContext,
    PipelineConfiguration,
    ReleaseView,
)
from foodx_devops_tools.release_flow import (
    identify_release_id,
    identify_release_state,
)
from foodx_devops_tools.utility import run_command

from ._deployment import (
    DeploymentState,
    FlattenedDeployment,
    assess_results,
    do_deploy,
)
from ._state import ExitState

log = logging.getLogger(__name__)


class DeploymentConfigurationError(Exception):
    """Problem acquiring deployment configuration."""


def _get_sha() -> str:
    """Get the git commit SHA of HEAD."""
    result = run_command(
        ["git", "rev-parse", "HEAD"], text=True, capture_output=True
    )

    if result.returncode != 0:
        raise RuntimeError("Git commit SHA acquisition failed")
    else:
        this_sha = result.stdout[0:10]

    return this_sha


async def _gather_main(
    configuration: PipelineConfiguration,
    enable_validation: bool,
    deployment_iterations: typing.List[FlattenedDeployment],
) -> typing.List[DeploymentState]:
    result = await asyncio.gather(
        *[
            do_deploy(configuration, x, enable_validation)
            for x in deployment_iterations
        ]
    )
    return result


@click.command()
@click.version_option(acquire_version())
@click.argument(
    "client_config",
    type=click.Path(dir_okay=True, file_okay=False, path_type=pathlib.Path),
)
@click.argument(
    "system_config",
    type=click.Path(dir_okay=True, file_okay=False, path_type=pathlib.Path),
)
@click.option(
    "--git-ref",
    default=None,
    help="""Git reference to drive release management workflow.

eg.

    ``$(Build.SourceBranch)`` for Azure DevOps Pipelines.
    ``${GITHUB_REF}`` for Github Actions.
    ``${CI_COMMIT_REF_NAME}`` for Gitlab-CI.
""",
    type=str,
)
@click.option(
    "--pipeline-id",
    default="000+local",
    help="""The pipeline ID. Should be considered mandatory for a CI/CD
 pipeline (optional for developers running locally).

eg.

    ``$(Build.BuildNumber)`` for Azure DevOps Pipelines.
    ``${GITHUB_RUN_NUMBER}`` for Github Actions.
    ``${CI_PIPELINE_ID}`` for Gitlab-CI.""",
    type=str,
)
@click.option(
    "--validation",
    default=False,
    help="Force deployments to be a validation deployment, regardless of any "
    "specified deployment mode in configuration.",
    is_flag=True,
)
def deploy_me(
    client_config: pathlib.Path,
    system_config: pathlib.Path,
    git_ref: typing.Optional[str],
    pipeline_id: str,
    validation: bool,
) -> None:
    """
    Deploy system resources.

    CLIENT_CONFIG  The client specific configuration directory.
    SYSTEM_CONFIG  The directory containing all non-client related pipeline
                   and deployment configuration.
    """
    try:
        configuration_paths = acquire_configuration_paths(
            client_config, system_config
        )
        this_configuration = PipelineConfiguration.from_files(
            configuration_paths
        )

        if git_ref:
            release_id = identify_release_id(git_ref)
            release_state = identify_release_state(git_ref)
        else:
            raise DeploymentConfigurationError(
                "--git-ref is mandatory (for now)"
            )

        commit_sha = _get_sha()
        base_context = DeploymentContext(
            commit_sha=commit_sha,
            pipeline_id=pipeline_id,
            release_id=release_id,
            release_state=release_state.name,
        )
        pipeline_state = ReleaseView(this_configuration, base_context)
        deployment_iterations = pipeline_state.flatten()

        log.debug(str(deployment_iterations))

        results = asyncio.run(
            _gather_main(this_configuration, validation, deployment_iterations)
        )
        condensed_result = assess_results(results)
        if condensed_result.code == DeploymentState.ResultType.success:
            click.echo(
                click.style("success: Deployment succeeded.", fg="green")
            )
        else:
            click.echo(
                click.style(
                    "FAILED: Deployment failed. Check log for " "details.",
                    fg="red",
                )
            )
    except (ConfigurationPathsError, DeploymentConfigurationError) as e:
        message = str(e)
        log.error(message)
        click.echo(message, err=True)
        sys.exit(ExitState.BAD_DEPLOYMENT_CONFIGURATION.value)
    except asyncio.CancelledError:
        log.debug("Async cancellation exception")
        raise
    except Exception as e:
        log.exception(str(e))
        click.echo(
            "Deployment failed with unexpected error (see log for "
            "details), {0}".format(str(e)),
            err=True,
        )
        sys.exit(ExitState.UNKNOWN_ERROR.value)
