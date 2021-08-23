#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

"""Generalized structured name for deep referencing objects in data model."""

import pathlib
import typing

T = typing.TypeVar("T", bound="StructuredName")


class StructuredName(typing.List[str]):
    """Structured name of frames, applications and application steps."""

    def __hash__(self: T) -> int:  # type: ignore[override]
        """Hash ``StructuredName`` object for use as dictionary keys."""
        return hash(str(self))

    def __str__(self: T) -> str:
        """Convert ``StructuredName`` object to a string representation."""
        return ".".join(self)


StructuredPathCollection = typing.Dict[StructuredName, pathlib.Path]
