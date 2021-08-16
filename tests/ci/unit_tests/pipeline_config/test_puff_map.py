#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

import pathlib

import pytest

from foodx_devops_tools.pipeline_config import load_puff_map


@pytest.fixture
def apply_puffmap_test(apply_pipeline_config_test):
    def _apply(mock_content: str):
        result = apply_pipeline_config_test(mock_content, load_puff_map)
        return result

    return _apply


def test_single_default(apply_puffmap_test):
    file_text = """---
puff_map:
  frames:
      f1:
        applications:
          a1:
            arm_parameters_files:
              r1:
                sub1: 
                  label1: some/path/puff1.json
"""

    result = apply_puffmap_test(file_text)

    result_map = result.puff_map
    assert len(result_map.frames) == 1
    assert len(result_map.frames["f1"].applications) == 1
    assert (
        len(result_map.frames["f1"].applications["a1"].arm_parameters_files)
        == 1
    )
    assert (
        len(
            result_map.frames["f1"]
            .applications["a1"]
            .arm_parameters_files["r1"]
        )
        == 1
    )
    assert (
        len(
            result_map.frames["f1"]
            .applications["a1"]
            .arm_parameters_files["r1"]["sub1"]
        )
        == 1
    )
    assert result_map.frames["f1"].applications["a1"].arm_parameters_files[
        "r1"
    ]["sub1"]["label1"] == pathlib.Path("some/path/puff1.json")
