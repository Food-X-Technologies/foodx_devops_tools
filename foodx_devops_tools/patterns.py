#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

"""Declarations of constants for pipeline reference parsing."""

import dataclasses
import re
import typing

BRANCH_PREFIX = r"refs/heads/"
TAG_PREFIX = r"refs/tags/"

SEMANTIC_VERSION_GITREF = r"(\d+\.\d+\.\d+)"

SUBSCRIPTION_NAME = (
    r"(?P<system>[a-z0-9]+)"
    r"_"
    r"(?P<client>[a-z0-9]+)"
    r"_"
    r"(?P<resource_suffix>[a-z0-9]+)"
)


class SubscriptionNameError(Exception):
    """Problem parsing a subscription name into subscription data."""


T = typing.TypeVar("T", bound="SubscriptionData")


@dataclasses.dataclass
class SubscriptionData:
    """Manage components of a subscription name."""

    client: str
    resource_suffix: str
    system: str

    def __str__(self: T) -> str:
        """Convert subscription data to a string."""
        return "{0}_{1}_{2}".format(
            self.system, self.client, self.resource_suffix
        )

    @classmethod
    def from_subscription_name(cls: typing.Type[T], value: str) -> T:
        """Extract subscription data from a string."""
        result = re.match(SUBSCRIPTION_NAME, value)
        if not result:
            raise SubscriptionNameError(
                "Subscription name does not conform to naming pattern "
                "<system>_<client>_<resource_suffix>, {0}".format(value)
            )

        this_object = cls(
            client=result.group("client"),
            resource_suffix=result.group("resource_suffix"),
            system=result.group("system"),
        )

        return this_object
