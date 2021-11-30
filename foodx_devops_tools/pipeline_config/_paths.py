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
    context: typing.Set[pathlib.Path]
    deployments: pathlib.Path
    frames: pathlib.Path
    puff_map: pathlib.Path
    release_states: pathlib.Path
    service_principals: pathlib.Path
    static_secrets: typing.Set[pathlib.Path]
    subscriptions: pathlib.Path
    systems: pathlib.Path
    tenants: pathlib.Path

    CONFIG_SUBDIRS: typing.Set[str] = {"static_secrets", "context"}

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
        client_files = this_object.__acquire_client_files(client_config)
        system_files = this_object.__acquire_system_files(system_config)

        if len(client_files + system_files) > len(PIPELINE_CONFIG_FILES):
            # must be duplicate files between the directories
            log.debug("client files, {0}".format(str(client_files)))
            log.debug("system files, {0}".format(str(system_files)))
            raise ConfigurationPathsError(
                "Duplicate files between "
                "directories, {0}, {1}".format(client_config, system_config)
            )

        this_object.static_secrets = cls.__acquire_static_secrets(client_config)
        this_object.context = cls.__acquire_template_context(
            client_config, system_config
        )

        return this_object

    @staticmethod
    def __acquire_static_secrets(
        client_config: pathlib.Path,
    ) -> typing.Set[pathlib.Path]:
        secrets_path = client_config / "static_secrets"
        result = PipelineConfigurationPaths.__acquire_subdir_files(
            secrets_path, "static secrets"
        )
        return result

    @staticmethod
    def __acquire_template_context(
        client_config: pathlib.Path, system_config: pathlib.Path
    ) -> typing.Set[pathlib.Path]:
        # template context could be located in either client or system config.
        context_client_path = client_config / "context"
        client_context_files = (
            PipelineConfigurationPaths.__acquire_subdir_files(
                context_client_path, "client template context"
            )
        )
        context_system_path = system_config / "context"
        system_context_files = (
            PipelineConfigurationPaths.__acquire_subdir_files(
                context_system_path, "system template context"
            )
        )
        result = client_context_files.union(system_context_files)
        return result

    def __acquire_client_files(
        self: T, client_config: pathlib.Path
    ) -> typing.List[pathlib.Path]:
        client_files = list()
        for x in client_config.iterdir():
            if (
                x.is_file()
                and (x.name in PIPELINE_CONFIG_FILES)
                and (x.stem not in self.CONFIG_SUBDIRS)
            ):
                log.info("adding client configuration file, {0}".format(x))
                setattr(self, x.stem, x)
                client_files.append(x)

        return client_files

    def __acquire_system_files(
        self: T, system_config: pathlib.Path
    ) -> typing.List[pathlib.Path]:
        system_files = list()
        for x in system_config.iterdir():
            if x.is_file() and (x.name in PIPELINE_CONFIG_FILES):
                log.info("adding system configuration file, {0}".format(x))
                setattr(self, x.stem, x)
                system_files.append(x)

        return system_files

    @staticmethod
    def __acquire_subdir_files(
        this_path: pathlib.Path, category: str
    ) -> typing.Set[pathlib.Path]:
        result = set()
        if this_path.is_dir():
            log.debug(
                "{2} directory, {0}, {1}".format(
                    this_path, str(list(this_path.iterdir())), category
                )
            )
            for x in this_path.iterdir():
                if x.is_file():
                    log.info(
                        "adding file to configuration, {1}, {0}".format(
                            x, category
                        )
                    )
                    result.add(x)
        elif this_path.exists():
            log.debug(f"{category} not a directory, {this_path}")
        else:
            log.debug(f"{category} not present, {this_path}")

        return result
