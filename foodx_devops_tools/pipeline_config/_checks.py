#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

import asyncio
import pathlib
import typing

import aiofiles  # type: ignore

from ._structure import StructuredPathCollection
from .frames import FramesTriggersDefinition
from .pipeline import PipelineConfiguration
from .puff_map import PuffMap

FileExistsCollection = typing.Dict[pathlib.Path, bool]


def _collate_results(
    results: typing.List[FileExistsCollection],
) -> FileExistsCollection:
    collated_results: FileExistsCollection = dict()
    for this_result in results:
        collated_results.update(this_result)

    return collated_results


async def _file_exists(file: pathlib.Path) -> bool:
    """Test for file existence asynchronously."""
    try:
        async with aiofiles.open(str(file), mode="r"):
            pass

        exists = True
    except FileNotFoundError:
        exists = False

    return exists


async def _check_paths(paths: typing.Set[pathlib.Path]) -> FileExistsCollection:
    results = await asyncio.gather(*[_file_exists(x) for x in paths])

    collection: FileExistsCollection = dict()
    for file, state in zip(paths, results):
        collection[file] = state

    return collection


async def _check_arm_files(
    frames: FramesTriggersDefinition,
) -> FileExistsCollection:
    return await _check_paths(set(frames.arm_file_paths().values()))


async def _check_puff_maps(
    frame_folders: StructuredPathCollection, puff_map: PuffMap
) -> FileExistsCollection:
    return await _check_paths(
        set(puff_map.arm_template_parameter_file_paths(frame_folders).values())
    )


async def do_path_check(
    pipeline_configuration: PipelineConfiguration,
) -> None:
    """Check that paths in configuration actually exist."""
    # check that all the generated ARM template parameter files and ARM
    # template files are where they are expected to be for the current
    # *client* configuration.
    this_futures = await asyncio.gather(
        _check_arm_files(pipeline_configuration.frames),
        _check_puff_maps(
            pipeline_configuration.frames.frame_folders(),
            pipeline_configuration.puff_map,
        ),
        return_exceptions=False,
    )

    done_items = [x for x in this_futures if x]
    collated_results = _collate_results(done_items)
    missing_files = [str(x) for x, y in collated_results.items() if not y]
    if missing_files:
        raise FileNotFoundError(
            "files missing from deployment, {0}".format(str(missing_files))
        )
