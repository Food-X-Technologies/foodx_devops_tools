#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

import asyncio
import logging
import pathlib
import typing

import aiofiles

from foodx_devops_tools._to import StructuredTo
from foodx_devops_tools.utilities.templates import prepare_deployment_files

from ._structure import StructuredName
from .pipeline import PipelineConfiguration
from .views import DeploymentContext, ReleaseView

log = logging.getLogger(__name__)

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


async def _check_paths(
    paths: typing.Iterable[pathlib.Path],
) -> FileExistsCollection:
    results = await asyncio.gather(*[_file_exists(x) for x in paths])

    collection: FileExistsCollection = dict()
    for file, state in zip(paths, results):
        collection[file] = state

    return collection


async def _check_arm_files(
    arm_template_files: typing.List[pathlib.Path],
) -> FileExistsCollection:
    return await _check_paths(arm_template_files)


async def _check_puff_maps(
    arm_parameter_files: typing.List[pathlib.Path],
) -> FileExistsCollection:
    return await _check_paths(arm_parameter_files)


PathList = typing.List[pathlib.Path]


async def _prepare_deployment_files(
    pipeline_configuration: PipelineConfiguration,
) -> typing.Tuple[PathList, PathList]:
    arm_paths = pipeline_configuration.frames.arm_file_paths()
    frame_folders = pipeline_configuration.frames.frame_folders()
    puff_paths = pipeline_configuration.frames.puff_file_paths()
    puff_parameter_paths = (
        pipeline_configuration.puff_map.arm_template_parameter_file_paths(
            pipeline_configuration.frames.frame_folders()
        )
    )

    assert set(puff_paths.keys()) == set(arm_paths.keys())

    templated_arm_files = list()
    expected_arm_parameter_files = list()
    for release_state in pipeline_configuration.release_states:
        base_context = DeploymentContext(
            commit_sha="abc123",
            git_ref=None,
            pipeline_id="000",
            release_id="0.0.0+local",
            release_state=release_state,
        )
        log.info("top-level deployment context, {0}".format(str(base_context)))

        pipeline_state = ReleaseView(pipeline_configuration, base_context)
        deployment_iterations = pipeline_state.flatten(StructuredTo())

        for this_iteration in deployment_iterations:
            for structure_name in arm_paths.keys():
                # have to initialise some data here that in a deployment is
                # fulfilled as part of the deployment.
                this_iteration.context.frame_name = structure_name[0]
                this_iteration.context.application_name = structure_name[1]
                this_iteration.data.frame_folder = frame_folders[
                    StructuredName([this_iteration.context.frame_name])
                ].dir

                puff_map_structure_name = StructuredName(
                    [
                        this_iteration.context.frame_name,
                        this_iteration.context.application_name,
                        release_state,
                        this_iteration.context.azure_subscription_name,
                        structure_name[-1],
                    ]
                )
                template_files = this_iteration.construct_deployment_paths(
                    arm_paths[structure_name].file,
                    puff_paths[structure_name].file,
                    puff_parameter_paths[puff_map_structure_name].file,
                )
                log.debug(
                    f"template files for configuration validation,"
                    f" {puff_map_structure_name},  {template_files}"
                )

                template_parameters = (
                    this_iteration.construct_template_parameters()
                )
                log.debug(
                    f"template parameters applied to configuration "
                    f"validation,"
                    f" {puff_map_structure_name}, {template_parameters}"
                )

                deployment_files = await prepare_deployment_files(
                    template_files,
                    template_parameters,
                )

                templated_arm_files.append(deployment_files.arm_template)
                expected_arm_parameter_files.append(deployment_files.parameters)

    return templated_arm_files, expected_arm_parameter_files


async def do_path_check(pipeline_configuration: PipelineConfiguration) -> None:
    """
    Check that paths in configuration actually exist.

    Check that all the generated ARM template parameter files and ARM
    template files are where they are expected to be for the current
    *client* configuration.
    """
    (
        templated_arm_files,
        expected_arm_parameter_files,
    ) = await _prepare_deployment_files(pipeline_configuration)

    this_futures = await asyncio.gather(
        _check_arm_files(templated_arm_files),
        _check_puff_maps(expected_arm_parameter_files),
        return_exceptions=False,
    )

    done_items = [x for x in this_futures if x]
    collated_results = _collate_results(done_items)
    missing_files = [str(x) for x, y in collated_results.items() if not y]
    if missing_files:
        raise FileNotFoundError(
            "files missing from deployment, {0}".format(str(missing_files))
        )
