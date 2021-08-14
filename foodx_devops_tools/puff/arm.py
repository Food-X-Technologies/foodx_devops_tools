#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

"""Azure ARM template parameter generation."""

import copy
import json
import logging
import pathlib
import typing

import aiofiles  # type: ignore
import aiofiles.os  # type: ignore
import click
import pydantic
import ruamel.yaml
from deepmerge import always_merger  # type: ignore

from ._exceptions import ArmTemplateError
from ._header import ARMTEMPLATE_PARAMETERS_HEADER
from ._puff_parameters import PuffParameterModel

log = logging.getLogger(__name__)

YamlData = typing.Dict[str, typing.Any]

BASE_PARAMETER_EXCLUDE_LABELS = ["default", "environments", "name", "services"]


async def load_yaml(path: pathlib.Path) -> YamlData:
    """
    Asynchronously load yaml file data.

    Args:
        path: Path to YAML file to load.

    Returns:
        Loaded YAML data.
    Raises:
        FileNotFoundError: If file cannot be loaded.
        IsADirectoryError: If path is a directory instead of a file.
    """
    try:
        yaml = ruamel.yaml.YAML(typ="safe")
        async with aiofiles.open(str(path), mode="r") as f:
            content = await f.read()
        yaml_data = yaml.load(content)
        log.debug("{0}, {1}".format(path, str(yaml_data)))

        if not yaml_data:
            log.warning("Empty YAML file, {0}".format(str(path)))

        return yaml_data
    except FileNotFoundError:
        log.error("File not found, {0}".format(str(path)))
        raise
    except IsADirectoryError:
        log.error("Path is a directory, {0}".format(str(path)))
        raise
    except Exception:
        log.error("Unexpected error with path, {0}".format(str(path)))
        raise


def _remove_keys(
    parameters: typing.Dict[str, typing.Any], exclude_labels: typing.List[str]
) -> dict:
    """
    Remove keys from a dictionary without changing the original.

    Attempts to remove keys that don't exist in the dictinary are silently
    ignored.

    Args:
        parameters: Dictionary to be adjusted.

    Returns:
        Modified dictionary.
    """
    this_copy = parameters.copy()
    for k in exclude_labels:
        try:
            del this_copy[k]
        except KeyError:
            # silently ignore missing keys by suppressing this exception
            pass

    return this_copy


async def _save_parameter_file(
    target_path: pathlib.Path,
    parameter_data: typing.Optional[dict],
    is_pretty: bool,
) -> None:
    """
    Create ARM template parameter file.

    Args:
        target_path: File path to be created or deleted.
        parameter_data: Parameters to be applied to data.
        is_pretty: Create nicely formatted JSON for humans.
    """
    # WARNING: The header template dict contains a dict in a field and
    # dict.copy() is shallow so care needs to be taken to ensure all
    # concurrent copies are unique due to Python reference-copy default.
    generated_parameters = copy.deepcopy(ARMTEMPLATE_PARAMETERS_HEADER)
    if parameter_data:
        parameters = dict()
        for item_key, value in parameter_data.items():
            if isinstance(value, dict):
                # assume the dict is valid ARM template parameter structure.
                # the dict SHOULD be an ARM template parameter reference:
                # https://docs.microsoft.com/en-us/azure/azure-resource-manager/templates/parameter-files#parameter-file
                parameters[item_key] = value
            elif isinstance(value, (bool, float, int, str, list)):
                parameters[item_key] = {
                    "value": value,
                }
            else:
                # assume the value is convertible to str
                parameters[item_key] = {
                    "value": str(value),
                }
        generated_parameters["parameters"] = parameters
    dump_arguments: dict = dict()
    if is_pretty:
        dump_arguments = {"sort_keys": True, "indent": 2}
    async with aiofiles.open(target_path, mode="w") as f:
        log.info("saving parameter file, {0}".format(target_path))
        await f.write(json.dumps(generated_parameters, **dump_arguments))


async def _delete_parameter_file(
    target_path: pathlib.Path,
) -> None:
    """
    Delete generated ARM template parameter file.

    Args:
        target_path: File path to be created or deleted.
    """
    if target_path.exists():
        log.warning("deleting parameter file, {0}".format(target_path))
        await aiofiles.os.remove(target_path)


async def _do_file_actions(
    is_delete_action: bool,
    target_path: pathlib.Path,
    parameter_data: dict,
    is_pretty: bool,
) -> None:
    """
    Create or delete generated ARM template parameter files.

    Args:
        is_delete_action: Signal deleting or creating parameter files.
        target_path: Directory to store or delete parameter files.
        parameter_data: Data for each ARM template parameter file.
        is_pretty: Create nicely formatted JSON for humans.
    """
    for key, values in parameter_data.items():
        this_path = target_path / ".".join([key, "json"])
        if is_delete_action:
            await _delete_parameter_file(this_path)
        else:
            await _save_parameter_file(this_path, values, is_pretty)


def _linearize_name(base_data: dict, filename: str) -> dict:
    cleaned = _remove_keys(base_data, ["name"])
    this_name = base_data.get("name", filename)
    if not this_name:
        raise RuntimeError("Invalid empty name")

    linearized = {
        this_name: cleaned,
    }
    return linearized


def _merge_default_name(base_data: dict) -> dict:
    this_data = copy.deepcopy(base_data)
    for key, value in this_data.items():
        if "default" in value:
            new_parameters = value["default"]
            cleaned = _remove_keys(value, ["default"])

            updated = always_merger.merge(cleaned, new_parameters)

            this_data[key] = updated

    return this_data


def _iterate_iterable(
    cleaned: dict, base_key: str, this_data: dict, singular: str
) -> dict:
    linearized = dict()
    for iterable_key, iterable_data in this_data.items():
        if not iterable_key:
            raise RuntimeError("Invalid empty {0} name".format(singular))

        if iterable_data:
            this_value = always_merger.merge(
                copy.deepcopy(cleaned), iterable_data
            )
        else:
            this_value = copy.deepcopy(cleaned)

        this_value[singular] = iterable_key
        linearized["{0}.{1}".format(base_key, iterable_key)] = this_value

    return linearized


def _linearize_iterable(base_data: dict, plural: str, singular: str) -> dict:
    linearized = dict()
    for base_key, base_value in base_data.items():
        this_data = (
            copy.deepcopy(base_value[plural])
            if plural in base_value
            else dict()
        )
        cleaned = _remove_keys(copy.deepcopy(base_value), [plural])
        if this_data:
            iterated = _iterate_iterable(cleaned, base_key, this_data, singular)
            linearized.update(iterated)
        else:
            linearized[base_key] = cleaned

    return linearized if linearized else base_data.copy()


def _linearize_services(base_data: dict) -> dict:
    plural = "services"
    singular = "service"
    return _linearize_iterable(base_data, plural, singular)


def _linearize_environments(base_data: dict) -> dict:
    plural = "environments"
    singular = "environment"
    return _linearize_iterable(base_data, plural, singular)


def _merge_list_of_dict(this_data: typing.List[dict]) -> dict:
    result: dict = dict()
    for item in this_data:
        if isinstance(item, dict):
            for k, v in item.items():
                if k in result:
                    result[k].update(v if v is not None else dict())
                else:
                    result[k] = v if v is not None else dict()
        else:
            log.error("ignoring non-dict list entry, {0}".format(str(item)))
    return result


def _linearize_regions(base_data: dict) -> dict:
    plural = "regions"
    singular = "region"
    linearized = dict()
    for base_key, base_value in base_data.items():
        this_data = (
            copy.deepcopy(base_value[plural])
            if plural in base_value
            else list()
        )
        cleaned = _remove_keys(base_value, [plural])
        # special handling of the region list unique to regions
        if this_data:
            merged_list = _merge_list_of_dict(this_data)
            iterated = _iterate_iterable(
                cleaned, base_key, merged_list, singular
            )
            linearized.update(iterated)
        else:
            linearized[base_key] = cleaned

    return linearized if linearized else copy.deepcopy(base_data)


def _linearize_parameters(yaml_data: dict, file_name: str) -> dict:
    level0_merge = _linearize_name(yaml_data, file_name)

    # a hack to enable a variable called "name" to be specified.
    default_merged = _merge_default_name(level0_merge)

    level1_merge = _linearize_services(default_merged)
    level2_merge = _linearize_environments(level1_merge)
    level3_merge = _linearize_regions(level2_merge)

    return level3_merge


async def do_arm_template_parameter_action(
    puff_file_path: pathlib.Path,
    is_delete_action: bool,
    is_pretty: bool,
) -> None:
    """
    Generate ARM template parameter files from puff YAML file.

    The generated files are always output to the same directory as the source
    puff file.

    Args:
        puff_file_path: Path to source YAML parameter file.
        is_delete_action: True if files should be deleted instead of created.
        is_pretty: Create nicely formatted JSON for humans.
    """
    target_path = puff_file_path.parent

    click.echo("loading, {0}".format(puff_file_path))
    yaml_data = await load_yaml(puff_file_path)
    try:
        # for now, just use the pydantic model to validate the YAML data.
        PuffParameterModel.parse_obj(yaml_data)

        file_name = pathlib.Path(puff_file_path.stem).name
        merged_data = _linearize_parameters(yaml_data, file_name)
        await _do_file_actions(
            is_delete_action, target_path, merged_data, is_pretty
        )
    except pydantic.ValidationError as e:
        raise ArmTemplateError(
            "Puff parameter validation failed, "
            "{0}. {1}".format(puff_file_path, str(e))
        ) from e
