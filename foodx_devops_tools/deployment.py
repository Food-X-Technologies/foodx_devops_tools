#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

"""Declarations relating to deployment management."""

import dataclasses
import re
import typing

TUPLE_REGEX_PATTERN = (
    r"(?P<system>[a-z0-9_]+)-(?P<client>[a-z0-9_]+)-("
    r"?P<release_state>[a-z0-9_]+)"
)


class DeploymentTupleError(Exception):
    """Problem parsing deployment tuple text."""


T = typing.TypeVar("T", bound="DeploymentTuple")


@dataclasses.dataclass
class DeploymentTuple:
    """System deployment tuple."""

    client: str
    release_state: str
    system: str

    def __str__(self: T) -> str:
        """Convert ``DeploymentTuple` object to normalized representation."""
        result = "-".join([self.system, self.client, self.release_state])
        return result

    @classmethod
    def parse(cls: typing.Type[T], text: str) -> T:
        """
        Convert deployment tuple text to ``DeploymentTuple`` object.

        Args:
            text: Deployment tuple text to be parsed.

        Returns:
            ``DeploymentTuple`` object.
        """
        result = re.match(TUPLE_REGEX_PATTERN, text)
        if not result:
            raise DeploymentTupleError(
                "Error parsing tuple text, " "{0}".format(text)
            )

        client = result.group("client")
        system = result.group("system")
        release_state = result.group("release_state")

        return cls(client=client, release_state=release_state, system=system)
