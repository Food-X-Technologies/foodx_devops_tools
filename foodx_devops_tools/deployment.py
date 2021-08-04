#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

"""Declarations relating to deployment management."""

import dataclasses
import typing

T = typing.TypeVar("T", bound="DeploymentState")


@dataclasses.dataclass
class DeploymentState:
    """System deployment tuple."""

    client: str
    release_state: str
    system: str

    def __str__(self: T) -> str:
        """Convert ``DeploymentState`` object to normalized representation."""
        result = "-".join([self.system, self.client, self.release_state])
        return result
