#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.
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

import click

log = logging.getLogger(__name__)

SPECIFIER_REGEX = (
    r"^(?P<frame>[a-z0-9_\-]+)"
    r"(\."
    r"(?P<application>[a-z0-9_\-]+)"
    r"(\."
    r"(?P<step>[a-z0-9_\-]+)"
    r")?"
    r")?$"
)


class StructuredToError(Exception):
    """Problem occurred parsing a "--to" specifier."""


U = typing.TypeVar("U", bound="StructuredTo")


@dataclasses.dataclass()
class StructuredTo:
    """Structured deployment specifier."""

    frame: typing.Optional[str] = None
    application: typing.Optional[str] = None
    step: typing.Optional[str] = None

    def __str__(self: U) -> str:
        """Convert structure back to "specifier" form for use in messages."""
        if (not self.frame) and (not self.application) and (not self.step):
            result = "<all>"
        elif (not self.application) and (not self.step):
            result = "{0}".format(self.frame)
        elif not self.step:
            result = "{0}.{1}".format(self.frame, self.application)
        else:
            result = "{0}.{1}.{2}".format(
                self.frame, self.application, self.step
            )
        return result

    @classmethod
    def from_specifier(
        cls: typing.Type[U], to_specified: typing.Optional[str]
    ) -> U:
        """
        Construct a ``StructuredTo`` object from a specifier string.

        Args:
            to_specified: Structured specifier string to be parsed.

        Returns:
            Constructed ``StructuredTo`` object.
        Raises:
            StructuredToError: If the string specified is non conformant.
        """
        this_object = cls()

        if to_specified:
            this_match = re.match(SPECIFIER_REGEX, to_specified)
            if this_match:
                this_frame = this_match.group("frame")
                if this_frame:
                    this_object.frame = this_frame
                    this_application = this_match.group("application")
                    if this_application:
                        this_object.application = this_application
                        this_step = this_match.group("step")
                        if this_step:
                            this_object.step = this_step
            else:
                message = "Bad structured deployment specifier, {0}".format(
                    to_specified
                )
                raise StructuredToError(message)

        return this_object


T = typing.TypeVar("T", bound="StructuredToParameter")


class StructuredToParameter(click.ParamType):
    """Custom click parameter for the structured to option."""

    # https://click.palletsprojects.com/en/8.0.x/parameters/#implementing-custom-types

    name: str = "structured_to"

    def convert(
        self: T,
        value: typing.Optional[typing.Union[str, StructuredTo]],
        param: typing.Optional[click.Parameter],
        context: typing.Optional[click.Context],
    ) -> StructuredTo:
        """Convert command line option value to a structured to type."""
        if isinstance(value, StructuredTo):
            return value

        try:
            if isinstance(value, str) or (value is None):
                this_object = StructuredTo.from_specifier(value)
            else:
                raise StructuredToError()

            return this_object
        except StructuredToError:
            self.fail(
                f"{value!r} is not a valid deployment specifier", param, context
            )
