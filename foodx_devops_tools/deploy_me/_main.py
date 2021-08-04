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

from foodx_devops_tools._version import acquire_version
from foodx_devops_tools.pipeline_config import (
    DeploymentContext,
    PipelineConfiguration,
    PipelineConfigurationPaths,
    ReleaseView,
)
from foodx_devops_tools.release_flow import (
    identify_release_id,
    identify_release_state,
)
from foodx_devops_tools.utility import run_command

from ._state import ExitState

log = logging.getLogger(__name__)

PIPELINE_CONFIG_FILES = {
    "clients.yml",
    "release_states.yml",
    "deployments.yml",
    "frames.yml",
    "subscriptions.yml",
    "systems.yml",
    "tenants.yml",
}


class DeploymentConfigurationError(Exception):
    """Problem acquiring deployment configuration."""


def _acquire_configuration_paths(
    client_config: pathlib.Path, system_config: pathlib.Path
) -> PipelineConfigurationPaths:
    """Acquire system, pipeline configuration paths."""
    client_files = [
        x
        for x in client_config.iterdir()
        if x.is_file() and x.name in PIPELINE_CONFIG_FILES
    ]
    system_files = [
        x
        for x in system_config.iterdir()
        if x.is_file() and x.name in PIPELINE_CONFIG_FILES
    ]

    if len(client_files + system_files) > len(PIPELINE_CONFIG_FILES):
        # must be duplicate files between the directories
        log.debug("client files, {0}".format(str(client_files)))
        log.debug("system files, {0}".format(str(system_files)))
        raise DeploymentConfigurationError(
            "Duplicate files between "
            "directories, {0}, {1}".format(client_config, system_config)
        )

    path_arguments = {
        x.name.strip(".yml"): x
        for x in set(client_files).union(set(system_files))
    }
    result = PipelineConfigurationPaths(**path_arguments)
    return result


def _get_sha() -> str:
    result = run_command(
        ["git", "rev-parse", "HEAD"], text=True, capture_output=True
    )

    if result.returncode != 0:
        raise RuntimeError("Git commit SHA acquisition failed")
    else:
        this_sha = result.stdout[0:10]

    return this_sha


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
    help="Git reference to drive release management workflow",
    type=str,
)
@click.option(
    "--pipeline-id",
    default="000+local",
    help="""The pipeline ID. Should be considered mandatory for a CI/CD
 pipeline (optional for developers running locally).

  eg.``$(Build.BuildNumber)`` for Azure DevOps Pipelines.
     ``${GITHUB_RUN_NUMBER}`` for Github Actions.
     ``${CI_PIPELINE_ID}`` for Gitlab-CI.""",
    type=str,
)
def deploy_me(
    client_config: pathlib.Path,
    system_config: pathlib.Path,
    git_ref: typing.Optional[str],
    pipeline_id: str,
) -> None:
    """
    Deploy system resources.

    CLIENT_CONFIG  The client specific configuration directory.
    SYSTEM_CONFIG  The directory containing all non-client related pipeline
                   and deployment configuration.
    """
    try:
        configuration_paths = _acquire_configuration_paths(
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
    except DeploymentConfigurationError as e:
        message = str(e)
        log.error(message)
        click.echo(message, err=True)
        sys.exit(ExitState.BAD_DEPLOYMENT_CONFIGURATION)
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
        sys.exit(ExitState.UNKNOWN_ERROR)
