#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

"""Subscriptions deployment configuration I/O."""

import pathlib
import typing

import pydantic

from ._loader import load_configuration

ENTITY_NAME = "subscriptions"


class SubscriptionsDefinitionError(Exception):
    """Problem loading subscription definitions."""


class SingularSubscriptionDefinition(pydantic.BaseModel):
    """Single subscription definition."""

    ado_service_connection: typing.Optional[str]
    azure_id: str
    tenant: str


T = typing.TypeVar("T", bound="SubscriptionsDefinition")

ValueType = typing.Dict[str, SingularSubscriptionDefinition]


class SubscriptionsDefinition(pydantic.BaseModel):
    """Definition of deployment Azure subscriptions."""

    subscriptions: ValueType

    @pydantic.validator(ENTITY_NAME)
    def check_subscriptions(
        cls: pydantic.BaseModel, value: ValueType
    ) -> ValueType:
        """Validate ``subscriptions`` field."""
        if not value:
            raise ValueError("Empty subscription definition prohibited")

        return value


def load_subscriptions(file_path: pathlib.Path) -> SubscriptionsDefinition:
    """
    Load system definitions from file.

    Args:
        file_path: Path to system definitions file.

    Returns:
        System definitions.
    Raises:
        SystemsDefinitionError: If an error occurs loading the file.
    """
    result = load_configuration(
        file_path,
        SubscriptionsDefinition,
        SubscriptionsDefinitionError,
        ENTITY_NAME,
    )

    return typing.cast(SubscriptionsDefinition, result)
