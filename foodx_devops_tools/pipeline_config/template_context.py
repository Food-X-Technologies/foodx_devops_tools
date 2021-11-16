#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

"""Template context variable deployment configuration I/O."""


import logging
import pathlib
import typing

import pydantic

from ._exceptions import TemplateContextError
from ._loader import load_yaml_data

log = logging.getLogger(__name__)

ENTITY_NAME = "context"

ValueType = typing.Dict[str, typing.Dict[str, typing.Any]]


class TemplateContext(pydantic.BaseModel):
    """Define a collection of template context variables."""

    context: ValueType


def _apply_existing_keys(
    context_data: dict, yaml_data: dict, this_path: pathlib.Path
) -> None:
    """Merge existing template context keys instead of over-write."""
    existing_keys = [
        x
        for x in yaml_data[ENTITY_NAME].keys()
        if x in context_data[ENTITY_NAME].keys()
    ]
    if existing_keys:
        log.debug(
            f"merging existing template context keys, {existing_keys}, "
            f"{this_path}"
        )
        for key in existing_keys:
            context_data[ENTITY_NAME][key].update(yaml_data[ENTITY_NAME][key])
    else:
        log.debug(
            f"no existing template context keys to be merged, {this_path}"
        )


def _apply_nonexisting_keys(
    context_data: dict, yaml_data: dict, this_path: pathlib.Path
) -> None:
    """Add non-existing template context keys to the context."""
    nonexisting_keys = [
        x
        for x in yaml_data[ENTITY_NAME].keys()
        if x not in context_data[ENTITY_NAME].keys()
    ]
    if nonexisting_keys:
        log.debug(
            f"adding new template context keys, {nonexisting_keys}, "
            f"{this_path}"
        )
        for key in nonexisting_keys:
            context_data[ENTITY_NAME][key] = yaml_data[ENTITY_NAME][key]
    else:
        log.debug(f"no new template context keys, {this_path}")


def load_template_context(
    context_paths: typing.Set[pathlib.Path],
) -> TemplateContext:
    """Load template context variables from the relevant directory."""
    try:
        context_data: dict = {
            ENTITY_NAME: dict(),
        }
        for this_path in context_paths:
            if this_path.is_file():
                log.info("loading template context, {0}".format(this_path))
                yaml_data = load_yaml_data(this_path)
                if ENTITY_NAME in yaml_data:
                    _apply_existing_keys(context_data, yaml_data, this_path)
                    _apply_nonexisting_keys(context_data, yaml_data, this_path)
                else:
                    message = (
                        f"template context object not present in "
                        f"file, {this_path}"
                    )
                    log.error(message)
                    raise TemplateContextError(message)

        this_object = TemplateContext.parse_obj(context_data)

        return this_object
    except (NotADirectoryError, FileNotFoundError) as e:
        raise TemplateContextError(str(e)) from e
