#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

"""Configuration file path management."""

import logging
import pathlib
import typing

from ._exceptions import ConfigurationPathsError

log = logging.getLogger(__name__)

PIPELINE_CONFIG_FILES = {
    "clients.yml",
    "release_states.yml",
    "deployments.yml",
    "frames.yml",
    "puff_map.yml",
    "service_principals.vault",
    "subscriptions.yml",
    "systems.yml",
    "tenants.yml",
}

T = typing.TypeVar("T", bound="PipelineConfigurationPaths")


class PipelineConfigurationPaths:
    """Paths to pipeline configuration files."""

    clients: pathlib.Path
    release_states: pathlib.Path
    deployments: pathlib.Path
    frames: pathlib.Path
    puff_map: pathlib.Path
    service_principals: pathlib.Path
    static_secrets: typing.Set[pathlib.Path]
    subscriptions: pathlib.Path
    systems: pathlib.Path
    tenants: pathlib.Path

    def __init__(self: T) -> None:
        """Construct ``PipelineConfigurationPaths`` object."""
        for this_file in PIPELINE_CONFIG_FILES:
            path = pathlib.Path(this_file)
            setattr(self, path.stem, path)

    @classmethod
    def from_dict(cls: typing.Type[T], data: dict) -> T:
        """
        Construct ``PipelineConfigurationPaths`` object.

        NOTE: Delivering valid paths is the users responsibility.

        Args:
            data: Dictionary of data to populate in object.
        """
        this_object = cls()
        for x, y in data.items():
            setattr(this_object, x, y)

        return this_object

    @classmethod
    def from_paths(
        cls: typing.Type[T],
        client_config: pathlib.Path,
        system_config: pathlib.Path,
    ) -> T:
        """
        Construct ``PipelineConfigurationPaths`` object.

        Args:
            client_config: Path to client configuration directory.
            system_config: Path to system configuration directory.

        Raises:
            ConfigurationPathsError: If any paths are duplicated between
                client and system.
        """
        this_object = cls()
        client_files = list()
        for x in client_config.iterdir():
            if (
                x.is_file()
                and (x.name in PIPELINE_CONFIG_FILES)
                and (x.stem != "static_secrets")
            ):
                setattr(this_object, x.stem, x)
                client_files.append(x)

        system_files = list()
        for x in system_config.iterdir():
            if x.is_file() and (x.name in PIPELINE_CONFIG_FILES):
                setattr(this_object, x.stem, x)
                system_files.append(x)

        if len(client_files + system_files) > len(PIPELINE_CONFIG_FILES):
            # must be duplicate files between the directories
            log.debug("client files, {0}".format(str(client_files)))
            log.debug("system files, {0}".format(str(system_files)))
            raise ConfigurationPathsError(
                "Duplicate files between "
                "directories, {0}, {1}".format(client_config, system_config)
            )
        secrets_path = client_config / "static_secrets"
        this_object.static_secrets = set()
        if secrets_path.is_dir():
            for x in secrets_path.iterdir():
                if x.is_file():
                    this_object.static_secrets.add(x)

        return this_object
