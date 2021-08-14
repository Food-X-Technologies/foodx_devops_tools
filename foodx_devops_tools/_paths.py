#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

import logging
import pathlib

from foodx_devops_tools.pipeline_config import PipelineConfigurationPaths

from ._exceptions import ConfigurationPathsError

log = logging.getLogger(__name__)

PIPELINE_CONFIG_FILES = {
    "clients.yml",
    "release_states.yml",
    "deployments.yml",
    "frames.yml",
    "puff_map.yml",
    "subscriptions.yml",
    "systems.yml",
    "tenants.yml",
}


def acquire_configuration_paths(
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
        raise ConfigurationPathsError(
            "Duplicate files between "
            "directories, {0}, {1}".format(client_config, system_config)
        )

    path_arguments = {
        x.name.strip(".yml"): x
        for x in set(client_files).union(set(system_files))
    }
    result = PipelineConfigurationPaths(**path_arguments)
    return result
