#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

"""Manage puff map configuration files."""
import copy
import logging
import pathlib
import typing

import pydantic

from ._exceptions import FolderPathError, PuffMapDefinitionsError
from ._loader import load_configuration
from ._structure import StructuredName, StructuredPathCollection

log = logging.getLogger(__name__)

ENTITY_NAME = "puff_map"
ENTITY_SINGULAR = "puff_map"

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

T = typing.TypeVar("T", bound="PuffMap")


class PuffMap(pydantic.BaseModel):
    """Map puff generated ARM template parameter files to subscriptions."""

    frames: PuffMapFrames

    def arm_template_parameter_file_paths(
        self: T, folder_paths: StructuredPathCollection
    ) -> StructuredPathCollection:
        """
        Generate a collection ARM template parameter file paths from puff_map.

        Args:
            folder_paths: Frame folder paths.

        Returns:
            ARM template parameter file paths indexed by structured name.
        Raises:
            FolderPathError: If there is a problem acquiring frame folder
                             path for the specified frame.
        """
        results: StructuredPathCollection = dict()
        for frame_name, frame_data in self.frames.items():
            frame_structure = StructuredName()
            frame_structure.append(frame_name)
            for app_name, app_data in frame_data.applications.items():
                app_structure = copy.deepcopy(frame_structure)
                app_structure.append(app_name)
                for (
                    release_state,
                    release_data,
                ) in app_data.arm_parameters_files.items():
                    release_structure = copy.deepcopy(app_structure)
                    release_structure.append(release_state)
                    for sub_name, sub_data in release_data.items():
                        sub_structure = copy.deepcopy(release_structure)
                        sub_structure.append(sub_name)
                        for step_name, puff_file in sub_data.items():
                            step_structure = copy.deepcopy(sub_structure)
                            step_structure.append(step_name)

                            try:
                                results[step_structure] = (
                                    folder_paths[frame_structure] / puff_file
                                )
                            except KeyError as e:
                                raise FolderPathError(
                                    "Structure for specified foldet path does "
                                    "not exist, {0}, {1}".format(
                                        str(frame_structure),
                                        str(step_structure),
                                    )
                                ) from e

        return results


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
