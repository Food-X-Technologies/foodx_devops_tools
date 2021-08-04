#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

import pathlib
import typing

import pydantic
import ruamel.yaml  # type: ignore # noqa: F401
from ruamel.yaml import YAML  # type: ignore


def load_configuration(
    file_path: pathlib.Path,
    data_model: typing.Type[pydantic.BaseModel],
    error_type: typing.Type[Exception],
    entity_name: str,
) -> pydantic.BaseModel:
    """
    Load definitions from file.

    Args:
        file_path: Path to definitions file.
        data_model: Pydantic data model to use for the data.
        error_type: Exception type to use for reporting errors.
        entity_name: Name of the entity being loaded.

    Returns:
        ``data_model`` object with populated data.
    Raises:
        error_type: If an error occurs loading the file.
    """
    with file_path.open(mode="r") as f:
        loader = YAML(typ="safe")
        yaml_data = loader.load(f)

    try:
        result = data_model.parse_obj(yaml_data)

        return result
    except pydantic.ValidationError as e:
        raise error_type(
            "Error validating {0} definition, {1}".format(
                entity_name.replace("_", " "), e
            )
        ) from e
