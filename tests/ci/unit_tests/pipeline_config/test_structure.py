#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

import pathlib

from foodx_devops_tools.pipeline_config._structure import FrameFile


def test_clean():
    under_test = FrameFile(dir=pathlib.Path("some"), file=pathlib.Path("file"))

    assert under_test.path == pathlib.Path("some/file")


def test_none_dir_file():
    under_test = FrameFile(dir=None, file=None)

    assert under_test.path is None


def test_none_dir():
    under_test = FrameFile(dir=None, file=pathlib.Path("file"))

    assert under_test.path == pathlib.Path("file")


def test_none_file():
    under_test = FrameFile(dir=pathlib.Path("some"), file=None)

    assert under_test.path == pathlib.Path("some")
