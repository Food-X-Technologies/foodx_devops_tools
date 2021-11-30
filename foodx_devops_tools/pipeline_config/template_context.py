#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

"""Template context variable deployment configuration I/O."""
import copy
import logging
import pathlib
import typing

import deepmerge  # type: ignore
import pydantic

from ._exceptions import TemplateContextError
from ._loader import load_yaml_data

log = logging.getLogger(__name__)

ENTITY_NAME = "context"

ValueType = typing.Dict[str, typing.Any]


class TemplateContext(pydantic.BaseModel):
    """Define a collection of template context variables."""

    context: ValueType


def load_template_context(
    context_paths: typing.Set[pathlib.Path],
) -> TemplateContext:
    """Load template context variables from the relevant directory."""
    try:
        context_data: dict = {
            ENTITY_NAME: dict(),
        }
        log.info(f"template context paths, {context_paths}")
        for this_path in context_paths:
            if this_path.is_file():
                log.info("loading template context, {0}".format(this_path))
                yaml_data = load_yaml_data(this_path)
                if ENTITY_NAME in yaml_data:
                    context_data = deepmerge.always_merger.merge(
                        copy.deepcopy(context_data), yaml_data
                    )
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
