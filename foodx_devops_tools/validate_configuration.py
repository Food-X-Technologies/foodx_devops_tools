#!python3
# Copyright (c) 2021 Food-X Technologies
#
# This file is part of foodx_devops_tools.
#
# You should have received a copy of the MIT License along with
# foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

"""Validation pipeline configuration data."""

import asyncio
import enum
import pathlib
import sys

import click

from ._paths import ConfigurationPathsError, acquire_configuration_paths
from ._version import acquire_version
from .console import report_failure, report_success
from .pipeline_config import PipelineConfiguration, do_path_check
from .pipeline_config.exceptions import (
    ClientsDefinitionError,
    DeploymentsDefinitionError,
    FrameDefinitionsError,
    PipelineConfigurationError,
    PipelineViewError,
    ReleaseStatesDefinitionError,
    SubscriptionsDefinitionError,
    SystemsDefinitionError,
    TenantsDefinitionError,
)


@enum.unique
class ExitState(enum.Enum):
    """Validate configuration script exit states."""

    UNKNOWN = 100
    MISSING_GITREF = 101
    GITREF_PARSE_FAILURE = 102
    BAD_CONFIGURATION_PATHS = 103


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
    "--check-paths",
    default=False,
    help="Check paths in configuration for file or directory existence.",
    is_flag=True,
)
def _main(
    client_config: pathlib.Path, system_config: pathlib.Path, check_paths: bool
) -> None:
    """
    Validate pipeline configuration files.

    Exits non-zero if validation fails. Without the ``--check-paths`` option
    the utility loads the configuration to check for self-consistency of the
    data. In this case the release state does not need to be known.

    With the ``--check-paths`` option, the utility iterates over the release
    states configured for the client to check that all arm template and arm
    templates paramater files are in the expected locations unless the
    ``--git-ref`` option is also specified. In this case the check path tests
    only apply to the release state implied by the git ref.

    CLIENT_CONFIG:  The path to the directory where client configuration
                    files are located.
    SYSTEM_CONFIG:  The path to the directory where system configuration
                    files are located.
    """
    try:
        configuration_paths = acquire_configuration_paths(
            client_config, system_config
        )
        pipeline_configuration = PipelineConfiguration.from_files(
            configuration_paths
        )

        if check_paths:
            asyncio.run(do_path_check(pipeline_configuration))

        report_success("pipeline configuration validated")
    except FileNotFoundError as e:
        report_failure(str(e))
        sys.exit(ExitState.BAD_CONFIGURATION_PATHS.value)
    except ConfigurationPathsError as e:
        report_failure(str(e))
        sys.exit(ExitState.BAD_CONFIGURATION_PATHS.value)
    except PipelineConfigurationError as e:
        report_failure(str(e))
        sys.exit(ExitState.MISSING_GITREF.value)
    except (
        PipelineConfigurationError,
        ClientsDefinitionError,
        DeploymentsDefinitionError,
        FrameDefinitionsError,
        ReleaseStatesDefinitionError,
        SubscriptionsDefinitionError,
        SystemsDefinitionError,
        TenantsDefinitionError,
        PipelineViewError,
    ) as e:
        report_failure("Configuration schema error, {0}".format(e))
        sys.exit(ExitState.BAD_CONFIGURATION_PATHS.value)
    except Exception as e:
        report_failure("unknown error, {0}".format(str(e)))
        sys.exit(ExitState.UNKNOWN.value)


def flit_entry() -> None:
    """Flit script entry function for ``validate-configuration`` utility."""
    _main()
