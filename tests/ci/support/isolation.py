#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

import contextlib
import os
import pathlib
import tempfile
import typing


@contextlib.contextmanager
def simple_isolated_filesystem() -> typing.Generator[pathlib.Path, None, None]:
    with tempfile.TemporaryDirectory() as dir:
        d = pathlib.Path(dir)
        yield d
