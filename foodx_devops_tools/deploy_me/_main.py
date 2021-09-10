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

from foodx_devops_tools._declarations import (
    DEFAULT_CONSOLE_LOGGING_ENABLED,
    DEFAULT_FILE_LOGGING_DISABLED,
    DEFAULT_LOG_LEVEL,
    VALID_LOG_LEVELS,
)
from foodx_devops_tools._logging import LoggingState
from foodx_devops_tools._to import StructuredTo, StructuredToParameter
from foodx_devops_tools._version import acquire_version
from foodx_devops_tools.pipeline_config import (
    DeploymentContext,
    PipelineConfiguration,
    PipelineConfigurationPaths,
    ReleaseView,
)
from foodx_devops_tools.pipeline_config.exceptions import (
    ConfigurationPathsError,
)
from foodx_devops_tools.release_flow import (
    identify_release_id,
    identify_release_state,
)
from foodx_devops_tools.utilities import acquire_token, get_sha

from ._deployment import (
    DeploymentState,
    FlattenedDeployment,
    assess_results,
    do_deploy,
)
from ._exceptions import DeploymentTerminatedError
from ._state import ExitState, PipelineCliOptions

log = logging.getLogger(__name__)

DEFAULT_LOG_FILE = pathlib.Path("deploy_me.log")


class DeploymentConfigurationError(Exception):
    """Problem acquiring deployment configuration."""


async def _gather_main(
    configuration: PipelineConfiguration,
    deployment_iterations: typing.List[FlattenedDeployment],
    pipeline_parameters: PipelineCliOptions,
) -> None:
    """Deploy each deployment iteration asynchronously."""
    results = await asyncio.gather(
        *[
            do_deploy(configuration, x, pipeline_parameters)
            for x in deployment_iterations
        ],
        return_exceptions=False,
    )

    filtered_results = [x for x in results if isinstance(x, DeploymentState)]
    if len(filtered_results) != len(results):
        log.error("Some deployments may have had unexpected failures.")

    condensed_result = await assess_results(filtered_results)
    _report_results(condensed_result.code, len(deployment_iterations))


def _report_results(
    result_code: DeploymentState.ResultType, number_iterations: int
) -> None:
    if (result_code == DeploymentState.ResultType.success) and (
        number_iterations != 0
    ):
        click.echo(click.style("success: Deployment succeeded.", fg="green"))
    elif (result_code == DeploymentState.ResultType.success) and (
        number_iterations == 0
    ):
        click.echo(click.style("skipped: Deployment skipped.", fg="yellow"))
        # exit "clean" because a skip is not a failure per-se.
    else:
        click.echo(
            click.style(
                "FAILED: Deployment failed. Check log for details.",
                fg="red",
            )
        )
        sys.exit(ExitState.DEPLOYMENT_FAILED.value)


@click.command()
@click.version_option(acquire_version())
@click.argument(
    "client_path",
    type=click.Path(dir_okay=True, file_okay=False, path_type=pathlib.Path),
)
@click.argument(
    "system_path",
    type=click.Path(dir_okay=True, file_okay=False, path_type=pathlib.Path),
)
@click.argument(
    "password_file",
    type=click.File(mode="r"),
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
    "--log-enable-console",
    "enable_console_log",
    default=DEFAULT_CONSOLE_LOGGING_ENABLED,
    help="Log to console.",
    is_flag=True,
)
@click.option(
    "--log-disable-file",
    "disable_file_log",
    default=DEFAULT_FILE_LOGGING_DISABLED,
    help="Disable file logging.",
    is_flag=True,
)
@click.option(
    "--log-level",
    "log_level",
    default=DEFAULT_LOG_LEVEL,
    help="Select logging level to apply to all enabled log sinks.",
    show_default=True,
    type=click.Choice(VALID_LOG_LEVELS, case_sensitive=False),
)
@click.option(
    "--monitor-sleep",
    default=30,
    help="Sleep time in seconds between frame dependency status polls.",
    show_default=True,
    type=int,
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
    "--to",
    default=StructuredTo(),
    help="""Specify a structured name to deploy a specific system component.

<frame>.<application>.<step>

[default: deploy everything]
""",
    type=StructuredToParameter(),
)
@click.option(
    "--validation",
    default=False,
    help="Force deployments to be a validation deployment, regardless of any "
    "specified deployment mode in configuration.",
    is_flag=True,
)
@click.option(
    "--wait-timeout",
    default=15,
    help="Maximum wait time in minutes for frame, application or step "
    "completion. Failure results if the timeout is exceeded.",
    show_default=True,
    type=int,
)
def deploy_me(
    client_path: pathlib.Path,
    system_path: pathlib.Path,
    password_file: typing.IO,
    disable_file_log: bool,
    enable_console_log: bool,
    log_level: str,
    monitor_sleep: int,
    git_ref: typing.Optional[str],
    pipeline_id: str,
    to: StructuredTo,
    validation: bool,
    wait_timeout: int,
) -> None:
    """
    Deploy system resources.

    CLIENT_PATH  The client specific deployment definition directory.
    SYSTEM_PATH  The directory containing all non-client related pipeline
                   and deployment definition.
    PASSWORD_FILE:  The path to a file where the service principal decryption
                    password is stored, or "-" for stdin.
    """
    try:
        # currently no need to change logging configuration at run time,
        # so no need to preserve the object.
        LoggingState(
            disable_file_logging=disable_file_log,
            enable_console_logging=enable_console_log,
            log_level_text=log_level,
            default_log_file=DEFAULT_LOG_FILE,
        )

        pipeline_parameters = PipelineCliOptions(
            enable_validation=validation,
            monitor_sleep_seconds=monitor_sleep,
            wait_timeout_seconds=(60 * wait_timeout),
        )
        client_config = client_path / "configuration"
        system_config = system_path / "configuration"
        configuration_paths = PipelineConfigurationPaths.from_paths(
            client_config, system_config
        )
        decrypt_token = acquire_token(password_file)
        this_configuration = PipelineConfiguration.from_files(
            configuration_paths, decrypt_token
        )

        if git_ref:
            release_id = identify_release_id(git_ref)
            release_state = identify_release_state(git_ref)
        else:
            raise DeploymentConfigurationError(
                "--git-ref is mandatory (for now)"
            )

        commit_sha = get_sha()
        base_context = DeploymentContext(
            commit_sha=commit_sha,
            pipeline_id=pipeline_id,
            release_id=release_id,
            release_state=release_state.name,
        )
        log.info("top-level deployment context, {0}".format(str(base_context)))

        pipeline_state = ReleaseView(this_configuration, base_context)
        deployment_iterations = pipeline_state.flatten(to)

        log.info(
            "number deployment iteration, {0}".format(
                len(deployment_iterations)
            )
        )
        log.debug(str(deployment_iterations))

        asyncio.run(
            _gather_main(
                this_configuration, deployment_iterations, pipeline_parameters
            )
        )
    except (ConfigurationPathsError, DeploymentConfigurationError) as e:
        message = str(e)
        log.error(message)
        click.echo(message, err=True)
        sys.exit(ExitState.BAD_DEPLOYMENT_CONFIGURATION.value)
    except asyncio.CancelledError:
        log.error("Async cancellation exception")
        click.echo("Exiting due to async cancellation", err=True)
        sys.exit(ExitState.DEPLOYMENT_CANCELLED.value)
    except DeploymentTerminatedError as e:
        log.error("Deployment cancelled exception, {0}".format(str(e)))
        click.echo(
            click.style("Exiting due to deployment cancellation", fg="red"),
            err=True,
        )
        sys.exit(ExitState.DEPLOYMENT_CANCELLED.value)
    except asyncio.TimeoutError:
        click.echo(click.style("Exiting due to timeout", fg="red"), err=True)
        sys.exit(ExitState.DEPLOYMENT_TIMEOUT.value)
    except Exception as e:
        log.exception(str(e))
        click.echo(
            "Deployment failed with unexpected error (see log for "
            "details), {0}".format(str(e)),
            err=True,
        )
        sys.exit(ExitState.UNKNOWN_ERROR.value)
