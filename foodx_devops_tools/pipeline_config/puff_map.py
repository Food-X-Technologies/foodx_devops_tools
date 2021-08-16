#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

"""Manage puff map configuration files."""

import logging
import pathlib
import typing

import pydantic

from ._loader import load_configuration

log = logging.getLogger(__name__)

ENTITY_NAME = "puff_map"
ENTITY_SINGULAR = "puff_map"


class PuffMapDefinitionsError(Exception):
    """Problem parsing puff map definitions."""


PuffMapPaths = typing.Dict[str, pathlib.Path]
PuffMapSubscriptions = typing.Dict[str, PuffMapPaths]
PuffMapReleaseStates = typing.Dict[str, PuffMapSubscriptions]


class PuffMapApplication(pydantic.BaseModel):
    """Singular application collection of puff file mappings."""

    arm_parameters_files: PuffMapReleaseStates


PuffMapApplications = typing.Dict[str, PuffMapApplication]


class PuffMapFrame(pydantic.BaseModel):
    """Singular frame collection of puff file mappings of it's applications."""

    applications: PuffMapApplications


PuffMapFrames = typing.Dict[str, PuffMapFrame]


class PuffMap(pydantic.BaseModel):
    """Map puff generated ARM template parameter files to subscriptions."""

    frames: PuffMapFrames


class PuffMapGeneratedFiles(pydantic.BaseModel):
    """Map puff generated ARM template parameter files to subscriptions."""

    puff_map: PuffMap


def load_puff_map(file_path: pathlib.Path) -> PuffMapGeneratedFiles:
    """
    Load puff map definitions from file.

    Args:
        file_path: Path to puff map definitions file.

    Returns:
        Puff map definitions.
    Raises:
        PuffMapDefinitionsError: If an error occurs loading the file.
    """
    log.info("loading frame definitions from file, {0}".format(file_path))
    result = load_configuration(
        file_path, PuffMapGeneratedFiles, PuffMapDefinitionsError, ENTITY_NAME
    )

    return typing.cast(PuffMapGeneratedFiles, result)
