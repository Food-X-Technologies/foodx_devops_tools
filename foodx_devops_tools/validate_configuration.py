#!python3
# Copyright (c) 2021 Food-X Technologies
#
# This file is part of foodx_devops_tools.
#
# You should have received a copy of the MIT License along with
# foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

"""Validation pipeline configuration data."""

import enum
import pathlib
import sys

import click

from ._paths import ConfigurationPathsError, acquire_configuration_paths
from .console import report_failure, report_success
from .pipeline_config import PipelineConfiguration, PipelineConfigurationError


@enum.unique
class ExitState(enum.Enum):
    """Validate configuration script exit states."""

    UNKNOWN = 100
    MISSING_GITREF = 101
    GITREF_PARSE_FAILURE = 102
    BAD_CONFIGURATION_PATHS = 103


@click.command()
@click.argument(
    "client_config",
    type=click.Path(dir_okay=True, file_okay=False, path_type=pathlib.Path),
)
@click.argument(
    "system_config",
    type=click.Path(dir_okay=True, file_okay=False, path_type=pathlib.Path),
)
def _main(client_config: pathlib.Path, system_config: pathlib.Path) -> None:
    """Validate pipeline configuration files.

    Exits non-zero if validation fails.

    CONFIGURATION_DIR is the path to the directory where pipeline configuration
    files are located.
    """
    try:
        configuration_paths = acquire_configuration_paths(
            client_config, system_config
        )
        PipelineConfiguration.from_files(configuration_paths)

        report_success("pipeline configuration validated")
    except ConfigurationPathsError as e:
        report_failure(str(e))
        sys.exit(ExitState.BAD_CONFIGURATION_PATHS.value)
    except PipelineConfigurationError as e:
        report_failure(str(e))
        sys.exit(ExitState.MISSING_GITREF.value)
    except Exception as e:
        report_failure("unknown error, {0}".format(str(e)))
        sys.exit(ExitState.UNKNOWN.value)


def flit_entry() -> None:
    """Flit script entry function for ``validate-configuration`` utility."""
    _main()
