#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

"""Manage pipeline configuration files collectively."""

import dataclasses
import pathlib
import re
import typing

import pydantic

from .clients import ValueType as ClientsData
from .clients import load_clients
from .release_states import ValueType as ReleaseStatesData
from .release_states import load_release_states
from .subscriptions import ValueType as SubscriptionsData
from .subscriptions import load_subscriptions
from .systems import ValueType as SystemsData
from .systems import load_systems

SUBSCRIPTION_NAME_REGEX = (
    r"^(?P<system>[a-z0-9]+)"
    r"[_-]"
    r"(?P<client>[a-z0-9]+)"
    r"[_-]"
    r"(?P<release_state>[a-z0-9]+)$"
)


class PipelineConfigurationError(Exception):
    """Problem occurred loading pipeline configuration."""


@dataclasses.dataclass()
class PipelineConfigurationPaths:
    """Paths to pipeline configuration files."""

    clients: pathlib.Path
    release_states: pathlib.Path
    subscriptions: pathlib.Path
    systems: pathlib.Path


T = typing.TypeVar("T", bound="PipelineConfiguration")


class PipelineConfiguration(pydantic.BaseModel):
    """Pipeline configuration data."""

    clients: ClientsData
    release_states: ReleaseStatesData
    subscriptions: SubscriptionsData
    systems: SystemsData

    @classmethod
    def from_files(cls: typing.Type[T], paths: PipelineConfigurationPaths) -> T:
        """
        Load pipeline configuration from collection of files.

        Args:
            paths: Paths to pipeline configuration files.

        Returns:
            Instantiated ``PipelineConfiguration`` object.
        """
        client_config = load_clients(paths.clients)
        release_state_config = load_release_states(paths.release_states)
        subscription_config = load_subscriptions(paths.subscriptions)
        system_config = load_systems(paths.systems)
        kwargs = {
            "clients": client_config.clients,
            "release_states": release_state_config.release_states,
            "subscriptions": subscription_config.subscriptions,
            "systems": system_config.systems,
        }
        cls._validate_subscriptions(kwargs)
        new_object = cls(**kwargs)

        return new_object

    @staticmethod
    def _validate_subscriptions(loaded_data: dict) -> None:
        """
        Validate loaded subscription data.

        Args:
            loaded_data: Data loaded from pipeline configuration.
        """
        subscription_names = set(loaded_data["subscriptions"].keys())
        this_re = re.compile(SUBSCRIPTION_NAME_REGEX)
        for this_name in subscription_names:
            result = this_re.match(this_name)

            if not result:
                raise PipelineConfigurationError(
                    "Bad subscription name, " "{0}".format(this_name)
                )

            this_client = result.group("client")
            if this_client not in loaded_data["clients"]:
                raise PipelineConfigurationError(
                    "Bad client in subscription "
                    "name, {0}".format(this_client)
                )

            this_release_state = result.group("release_state")
            if this_release_state not in loaded_data["release_states"]:
                raise PipelineConfigurationError(
                    "Bad release state in "
                    "subscription name, "
                    "{0}".format(this_release_state)
                )

            this_system = result.group("system")
            if this_system not in loaded_data["systems"]:
                raise PipelineConfigurationError(
                    "Bad system in subscription "
                    "name, {0}".format(this_system)
                )
