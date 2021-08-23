#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

import pathlib

import pytest

from foodx_devops_tools.pipeline_config import StructuredName, load_puff_map


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


class TestPuffFiles:
    mock_folders = {
        StructuredName(["f1"]): pathlib.Path("this/dir"),
        StructuredName(["f2"]): pathlib.Path("other/dir"),
    }

    def test_single(self, apply_puffmap_test):
        file_text = """---
    puff_map:
      frames:
          f1:
            applications:
              a1:
                arm_parameters_files:
                  r1:
                    sub1: 
                      label1: some/puff1.json
    """

        under_test = apply_puffmap_test(file_text)
        result = under_test.puff_map.arm_template_parameter_file_paths(
            self.mock_folders
        )

        assert result == {
            StructuredName(["f1", "a1", "r1", "sub1", "label1"]): pathlib.Path(
                "this/dir/some/puff1.json"
            ),
        }

    def test_multiple_steps(self, apply_puffmap_test):
        file_text = """---
    puff_map:
      frames:
          f1:
            applications:
              a1:
                arm_parameters_files:
                  r1:
                    sub1: 
                      label1: puff1.json
                      label2: puff2.json
    """

        under_test = apply_puffmap_test(file_text)
        result = under_test.puff_map.arm_template_parameter_file_paths(
            self.mock_folders
        )

        assert result == {
            StructuredName(["f1", "a1", "r1", "sub1", "label1"]): pathlib.Path(
                "this/dir/puff1.json"
            ),
            StructuredName(["f1", "a1", "r1", "sub1", "label2"]): pathlib.Path(
                "this/dir/puff2.json"
            ),
        }

    def test_multiple_frames(self, apply_puffmap_test):
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
          f2:
            applications:
              a1:
                arm_parameters_files:
                  r1:
                    sub1: 
                      label1: some/path/puff1.json
    """

        under_test = apply_puffmap_test(file_text)
        result = under_test.puff_map.arm_template_parameter_file_paths(
            self.mock_folders
        )

        assert result == {
            StructuredName(["f1", "a1", "r1", "sub1", "label1"]): pathlib.Path(
                "this/dir/some/path/puff1.json"
            ),
            StructuredName(["f2", "a1", "r1", "sub1", "label1"]): pathlib.Path(
                "other/dir/some/path/puff1.json"
            ),
        }

    def test_multiple_applications(self, apply_puffmap_test):
        file_text = """---
    puff_map:
      frames:
          f1:
            applications:
              a1:
                arm_parameters_files:
                  r1:
                    sub1: 
                      label1: path/puff1.json
              a2:
                arm_parameters_files:
                  r1:
                    sub1: 
                      label1: puff2.json
    """

        under_test = apply_puffmap_test(file_text)
        result = under_test.puff_map.arm_template_parameter_file_paths(
            self.mock_folders
        )

        assert result == {
            StructuredName(["f1", "a1", "r1", "sub1", "label1"]): pathlib.Path(
                "this/dir/path/puff1.json"
            ),
            StructuredName(["f1", "a2", "r1", "sub1", "label1"]): pathlib.Path(
                "this/dir/puff2.json"
            ),
        }

    def test_mixed(self, apply_puffmap_test):
        file_text = """---
    puff_map:
      frames:
          f1:
            applications:
              a1:
                arm_parameters_files:
                  r1:
                    sub1: 
                      label1: puff1.json
              a2:
                arm_parameters_files:
                  r1:
                    sub1: 
                      label2: puff2.json
                    sub2: 
                      label3: puff3.json
                  r2:
                    sub1: 
                      label4: puff4.json
          f2:
            applications:
              a1:
                arm_parameters_files:
                  r1:
                    sub1: 
                      label1: puff5.json
    """

        under_test = apply_puffmap_test(file_text)
        result = under_test.puff_map.arm_template_parameter_file_paths(
            self.mock_folders
        )

        assert result == {
            StructuredName(["f1", "a1", "r1", "sub1", "label1"]): pathlib.Path(
                "this/dir/puff1.json"
            ),
            StructuredName(["f1", "a2", "r1", "sub1", "label2"]): pathlib.Path(
                "this/dir/puff2.json"
            ),
            StructuredName(["f1", "a2", "r1", "sub2", "label3"]): pathlib.Path(
                "this/dir/puff3.json"
            ),
            StructuredName(["f1", "a2", "r2", "sub1", "label4"]): pathlib.Path(
                "this/dir/puff4.json"
            ),
            StructuredName(["f2", "a1", "r1", "sub1", "label1"]): pathlib.Path(
                "other/dir/puff5.json"
            ),
        }
