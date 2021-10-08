#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

"""Generalized structured name for deep referencing objects in data model."""

import dataclasses
import pathlib
import typing

U = typing.TypeVar("U", bound="FrameFile")


@dataclasses.dataclass
class FrameFile:
    """
    Record directory and file paths of a frame separately.

    In a frame the frame folder must eventually be combined with a relative
    file path to access a file, but preprocessing often requires the two to
    be separate, but conceptually linked until needed.
    """

    dir: typing.Optional[pathlib.Path]
    file: typing.Optional[pathlib.Path]

    @property
    def path(self: U) -> typing.Optional[pathlib.Path]:
        """Combine the directory and file paths."""
        result = None
        if self.dir and self.file:
            result = self.dir / self.file
        elif self.dir:
            result = self.dir
        elif self.file:
            result = self.file

        return result


T = typing.TypeVar("T", bound="StructuredName")


class StructuredName(typing.List[str]):
    """Structured name of frames, applications and application steps."""

    def __hash__(self: T) -> int:  # type: ignore[override]
        """Hash ``StructuredName`` object for use as dictionary keys."""
        return hash(str(self))

    def __str__(self: T) -> str:
        """Convert ``StructuredName`` object to a string representation."""
        return ".".join(self)


StructuredPathCollection = typing.Dict[StructuredName, FrameFile]
