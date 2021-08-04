#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

"""Manage the structured ``--to`` specifier."""

import dataclasses
import logging
import re
import typing

log = logging.getLogger(__name__)

T = typing.TypeVar("T", bound="StructuredTo")

SPECIFIER_REGEX = (
    r"^(?P<frame>[a-z0-9_\-]+)"
    r"(\."
    r"(?P<application>[a-z0-9_\-]+)"
    r"(\["
    r"(?P<start>[0-9]+)"
    r"(:"
    r"(?P<stop>[0-9]+)"
    r")?"
    r"\])?"
    r")?$"
)


class StructuredToError(Exception):
    """Problem occurred parsing a "--to" specifier."""


@dataclasses.dataclass()
class StructuredTo:
    """Structured deployment specifier."""

    frame: typing.Optional[str] = None
    application: typing.Optional[str] = None
    deployment_range: typing.Optional[range] = None

    @classmethod
    def from_specifier(
        cls: typing.Type[T], to_specified: typing.Optional[str]
    ) -> T:
        """
        Construct a ``StructuredTo`` object from a specifier string.

        Args:
            to_specified: Structured specifier string to be parsed.

        Returns:
            Constructed ``StructuredTo`` object.
        """
        this_object = cls()

        if to_specified:
            this_match = re.match(SPECIFIER_REGEX, to_specified)
            if this_match:
                this_object.frame = this_match.group("frame")

                this_application = this_match.group("application")
                if this_application:
                    this_object.application = this_match.group("application")
                    this_start = this_match.group("start")
                    this_stop = this_match.group("stop")
                    if this_start and (not this_stop):
                        this_object.deployment_range = range(
                            int(this_start), int(this_start) + 1
                        )
                    elif this_start and this_stop:
                        this_object.deployment_range = range(
                            int(this_start), int(this_stop)
                        )
            else:
                # log the error and return the default object
                log.error(
                    "Missing frame from specifier, " "{0}".format(to_specified)
                )
        # else return the default object

        return this_object
