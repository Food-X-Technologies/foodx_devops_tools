#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with foodx_devops_tools.
#  If not, see <https://opensource.org/licenses/MIT>.

import pathlib

import pytest

from foodx_devops_tools.pipeline_config import StructuredName, load_frames
from foodx_devops_tools.pipeline_config._structure import FrameFile
from foodx_devops_tools.pipeline_config.exceptions import FrameDefinitionsError


@pytest.fixture
def apply_applications_test(apply_pipeline_config_test):
    def _apply(mock_content: str):
        result = apply_pipeline_config_test(mock_content, load_frames)
        return result

    return _apply


def test_single_default(apply_applications_test):
    file_text = """---
frames:
  frames:
    f1:
      applications:
        a1: 
          steps:
          - name: a1l1
            mode: Incremental
            resource_group: a1_group
        a2:
          steps:
          - name: a2l1
            mode: Complete
            resource_group: a2_group
      folder: some/path
"""

    result = apply_applications_test(file_text)

    result_frames = result.frames
    assert len(result_frames.frames) == 1
    assert len(result_frames.frames["f1"].applications["a1"].steps) == 1
    assert (
        result_frames.frames["f1"].applications["a1"].steps[0].resource_group
        == "a1_group"
    )
    assert (
        not result_frames.frames["f1"]
        .applications["a1"]
        .steps[0]
        .static_secrets
    )
    assert len(result_frames.frames["f1"].applications["a2"].steps) == 1
    assert (
        result_frames.frames["f1"].applications["a2"].steps[0].resource_group
        == "a2_group"
    )
    assert result_frames.frames["f1"].folder == pathlib.Path("some/path")
    assert result_frames.frames["f1"].triggers is None
    assert (
        result_frames.frames["f1"].applications["a2"].steps[0].arm_file is None
    )
    assert (
        result_frames.frames["f1"].applications["a2"].steps[0].puff_file is None
    )
    assert result_frames.frames["f1"].applications["a2"].steps[0].name == "a2l1"
    assert result_frames.triggers is None


def test_deploy_delay(apply_applications_test):
    file_text = """---
frames:
  frames:
    f1:
      applications:
        a1: 
          steps:
          - name: a1l1
            mode: Incremental
            resource_group: a1_group
          - delay_seconds: 23
      folder: some/path
"""

    result = apply_applications_test(file_text)

    result_frames = result.frames
    assert len(result_frames.frames) == 1
    assert len(result_frames.frames["f1"].applications["a1"].steps) == 2
    assert (
        result_frames.frames["f1"].applications["a1"].steps[0].resource_group
        == "a1_group"
    )
    assert (
        not result_frames.frames["f1"]
        .applications["a1"]
        .steps[0]
        .static_secrets
    )
    assert not hasattr(
        result_frames.frames["f1"].applications["a1"].steps[0], "delay_seconds"
    )
    assert (
        result_frames.frames["f1"].applications["a1"].steps[1].delay_seconds
        == 23
    )
    assert not hasattr(
        result_frames.frames["f1"].applications["a1"].steps[1], "resource_group"
    )


def test_deploy_script(apply_applications_test):
    file_text = """---
frames:
  frames:
    f1:
      applications:
        a1: 
          steps:
          - name: a1l1
            mode: Incremental
            resource_group: a1_group
          - name: a1s2
            script: |
              some command \
                --argument
              another command
      folder: some/path
"""

    result = apply_applications_test(file_text)

    result_frames = result.frames
    assert len(result_frames.frames) == 1
    assert len(result_frames.frames["f1"].applications["a1"].steps) == 2
    assert (
        result_frames.frames["f1"].applications["a1"].steps[0].resource_group
        == "a1_group"
    )
    assert (
        not result_frames.frames["f1"]
        .applications["a1"]
        .steps[0]
        .static_secrets
    )
    assert not hasattr(
        result_frames.frames["f1"].applications["a1"].steps[0], "script"
    )
    assert (
        result_frames.frames["f1"].applications["a1"].steps[1].script
        == """some command \
                --argument
another command
"""
    )


def test_enable_static_secrets(apply_applications_test):
    file_text = """---
frames:
  frames:
    f1:
      applications:
        a1: 
          steps:
          - name: a1l1
            mode: Incremental
            resource_group: a1_group
            static_secrets: true
        a2:
          steps:
          - name: a2l1
            mode: Complete
            resource_group: a2_group
      folder: some/path
"""

    result = apply_applications_test(file_text)

    result_frames = result.frames
    assert len(result_frames.frames) == 1
    assert len(result_frames.frames["f1"].applications["a1"].steps) == 1
    assert (
        result_frames.frames["f1"].applications["a1"].steps[0].resource_group
        == "a1_group"
    )
    assert result_frames.frames["f1"].applications["a1"].steps[0].static_secrets
    assert (
        not result_frames.frames["f1"]
        .applications["a2"]
        .steps[0]
        .static_secrets
    )
    assert len(result_frames.frames["f1"].applications["a2"].steps) == 1
    assert (
        result_frames.frames["f1"].applications["a2"].steps[0].resource_group
        == "a2_group"
    )
    assert result_frames.frames["f1"].folder == pathlib.Path("some/path")
    assert result_frames.frames["f1"].triggers is None
    assert (
        result_frames.frames["f1"].applications["a2"].steps[0].arm_file is None
    )
    assert (
        result_frames.frames["f1"].applications["a2"].steps[0].puff_file is None
    )
    assert result_frames.frames["f1"].applications["a2"].steps[0].name == "a2l1"
    assert result_frames.triggers is None


def test_arm_optional(apply_applications_test):
    file_text = """---
frames:
  frames:
    f1:
      applications:
        a1: 
          steps:
          - name: a1l1
            mode: Incremental
            resource_group: a1_group
            
        a2:
          steps:
          - name: a2l1
            arm_file: something.json
            mode: Complete
            resource_group: a2_group
      folder: some/path
"""

    result = apply_applications_test(file_text)

    result_frames = result.frames
    assert result_frames.frames["f1"].applications["a2"].steps[
        0
    ].arm_file == pathlib.Path("something.json")


def test_global_path_triggers_optional(apply_applications_test):
    file_text = """---
frames:
  triggers:
    paths:
      - "some/glob/**"
      - "*/stuff/*"
  frames:
    f1:
      applications:
        a1: 
          steps:
          - name: a1l1
            resource_group: a1_group
            mode: Incremental
        a2:
          steps:
          - name: a2l1
            resource_group: a2_group
            mode: Complete
            arm_file: something.json
      folder: some/path
"""

    result = apply_applications_test(file_text)

    result_frames = result.frames
    assert len(result_frames.triggers.paths) == 2
    assert result_frames.triggers.paths[0] == "some/glob/**"
    assert result_frames.triggers.paths[1] == "*/stuff/*"


def test_frame_path_triggers_optional(apply_applications_test):
    file_text = """---
frames:
  frames:
    f1:
      applications:
        a1: 
          steps:
          - name: a1l1
            resource_group: a1_group
            mode: Incremental
        a2:
          steps:
          - name: a2l1
            resource_group: a2_group
            mode: Complete
            arm_file: something.json
      folder: some/path
      triggers:
        paths:
          - "some/glob/**"
          - "*/stuff/*"
"""

    result = apply_applications_test(file_text)

    result_frames = result.frames
    assert len(result_frames.frames["f1"].triggers.paths) == 2
    assert result_frames.frames["f1"].triggers.paths[0] == "some/glob/**"
    assert result_frames.frames["f1"].triggers.paths[1] == "*/stuff/*"


def test_puff_optional(apply_applications_test):
    file_text = """---
frames:
  frames:
    f1:
      applications:
        a1: 
          steps:
          - name: a1l1
            resource_group: a1_group
            mode: Incremental
        a2:
          steps:
          - name: a2l1
            resource_group: a2_group
            mode: Complete
            puff_file: something.yml
      folder: some/path
"""

    result = apply_applications_test(file_text)

    result_frames = result.frames
    assert result_frames.frames["f1"].applications["a2"].steps[
        0
    ].puff_file == pathlib.Path("something.yml")


def test_frames_sequenced(apply_applications_test):
    file_text = """---
frames:
  frames:
    f1:
      applications:
        a1:
          steps:
          - name: a1l1
            resource_group: f1a1
            mode: Complete
        a2:
          steps:
          - name: a2l1
            resource_group: f1a2
            mode: Incremental
      folder: some/f1-path
    f2:
      applications:
        a3:
          steps:
          - name: a3l1
            resource_group: f2a3
            mode: Complete
        a4:
          steps:
          - name: a4l1
            resource_group: f2a4
            mode: Incremental
      depends_on:
        - f1
      folder: some/f2-path
"""

    result = apply_applications_test(file_text)

    result_frames = result.frames
    assert len(result_frames.frames) == 2
    assert "f1" in result_frames.frames
    assert "f2" in result_frames.frames
    assert result_frames.frames["f2"].depends_on[0] == "f1"


def test_applications_sequenced(apply_applications_test):
    file_text = """---
frames:
  frames:
    f1:
      applications:
        a1:
          depends_on:
            - a2
          steps:
            - name: a1l1
              resource_group: f1a1
              mode: Complete
        a2:
          steps:
            - name: a2l1
              resource_group: f1a2
              mode: Incremental
      folder: some/f1-path
"""

    result = apply_applications_test(file_text)

    result_frames = result.frames
    assert len(result_frames.frames["f1"].applications["a1"].depends_on) == 1
    assert result_frames.frames["f1"].applications["a1"].depends_on[0] == "a2"


def test_multiple_unsequenced(apply_applications_test):
    file_text = """---
frames:
  frames:
    f1:
      applications:
        a1:
          steps:
          - name: a1l1
            resource_group: f1a1
            mode: Complete
        a2:
          steps:
          - name: a2l1
            resource_group: f1a2
            mode: Complete
      folder: some/f1-path
    f3:
      applications:
        a5:
          steps:
          - name: a5l1
            resource_group: f3a5
            mode: Complete
        a6:
          steps:
          - name: a6l1
            resource_group: f3a6
            mode: Complete
      folder: some/f3-path
    f2:
      applications:
        a3:
          steps:
          - name: a3l1
            resource_group: f2a3
            mode: Complete
        a4:
          steps:
          - name: a4l1
            resource_group: f2a4
            mode: Complete
      folder: some/f2-path
"""

    result = apply_applications_test(file_text)

    result_frames = result.frames
    assert len(result_frames.frames) == 3
    assert all([x in result_frames.frames for x in ["f1", "f2", "f3"]])


def test_none_raises(apply_applications_test):
    file_text = """---
"""

    with pytest.raises(
        FrameDefinitionsError, match=r"Error validating frames definition"
    ):
        apply_applications_test(file_text)


def test_empty_raises(apply_applications_test):
    file_text = """---
frames:
"""

    with pytest.raises(
        FrameDefinitionsError, match=r"Error validating frames definition"
    ):
        apply_applications_test(file_text)


def test_bad_dependency_raises(apply_applications_test):
    file_text = """---
frames:
  frames:
    f1:
      applications:
        - a1
        - a2
      folder: some/f1-path
    f2:
      applications:
        - a3
        - a4
      depends_on:
        - bad_value
      folder: some/f2-path
"""

    with pytest.raises(
        FrameDefinitionsError, match=r"Error validating frames definition"
    ):
        apply_applications_test(file_text)


def test_duplicate_step_names_raises(apply_applications_test):
    file_text = """---
frames:
  frames:
    f1:
      applications:
        a1:
          steps:
            - arm_file: something.json
              mode: Incremental
              name: same_name
              resource_group: a1_group
            - arm_file: something_else.json
              mode: Incremental
              name: same_name
              resource_group: other_group
      folder: some/f2-path
"""

    with pytest.raises(
        FrameDefinitionsError, match=r"Application step names must be unique"
    ):
        apply_applications_test(file_text)


def test_missing_name_raises(apply_applications_test):
    file_text = """---
frames:
  frames:
    f1:
      applications:
        a1: 
          steps:
          - name: a1l1
            mode: Incremental
            resource_group: a1_group
        a2:
          steps:
          - mode: Complete
            resource_group: a2_group
      folder: some/path
"""

    with pytest.raises(
        FrameDefinitionsError, match=r"Error validating frames definition"
    ):
        apply_applications_test(file_text)


def test_missing_mode_raises(apply_applications_test):
    file_text = """---
frames:
  frames:
    f1:
      applications:
        a1: 
          steps:
          - name: a1l1
            mode: Incremental
            resource_group: a1_group
        a2:
          steps:
          - name: a2l1
            resource_group: a2_group
      folder: some/path
"""

    with pytest.raises(
        FrameDefinitionsError, match=r"Error validating frames definition"
    ):
        apply_applications_test(file_text)


def test_external_application_dependency_raises(apply_applications_test):
    file_text = """---
frames:
  frames:
    f1:
      applications:
        a1: 
          steps:
          - name: a1s1
            mode: Incremental
            resource_group: a1_group
          depends_on:
            - a2
      folder: f1/path
    f2:
      applications:
        a2:
          steps:
          - name: a2s1
            mode: Incremental
            resource_group: a2_group
      folder: f2/path
"""

    with pytest.raises(
        FrameDefinitionsError, match=r"Error validating frames definition"
    ):
        apply_applications_test(file_text)


def test_frame_application_dependency_raises(apply_applications_test):
    file_text = """---
frames:
  frames:
    f1:
      applications:
        a1: 
          steps:
            - name: a1s1
              mode: Incremental
              resource_group: a1_group
          depends_on:
            # application dependency can only depend on other peer applications
            - f2
      folder: f1/path
    f2:
      applications:
        a2:
          steps:
          - name: a2s1
            mode: Incremental
            resource_group: a2_group
      folder: f2/path
"""

    with pytest.raises(
        FrameDefinitionsError, match=r"Error validating frames definition"
    ):
        apply_applications_test(file_text)


class TestArmFilePaths:
    def test_default(self, apply_applications_test):
        file_text = """---
frames:
  frames:
    f1:
      applications:
        a1: 
          steps:
          - name: a1l1
            mode: Incremental
            resource_group: rgn
      folder: some/path
"""

        under_test = apply_applications_test(file_text)
        result = under_test.frames.arm_file_paths()

        assert result == {
            StructuredName(["f1", "a1", "a1l1"]): FrameFile(
                dir=pathlib.Path("some/path/"),
                file=None,
            ),
        }

    def test_explicit(self, apply_applications_test):
        file_text = """---
frames:
  frames:
    f1:
      applications:
        a1: 
          steps:
          - name: a1l1
            mode: Incremental
            arm_file: arm_file.json
            resource_group: rgn
      folder: some/path
"""

        under_test = apply_applications_test(file_text)
        result = under_test.frames.arm_file_paths()

        assert result == {
            StructuredName(["f1", "a1", "a1l1"]): FrameFile(
                dir=pathlib.Path("some/path/"),
                file=pathlib.Path("arm_file.json"),
            )
        }

    def test_mixed(self, apply_applications_test):
        file_text = """---
frames:
  frames:
    f1:
      applications:
        a1: 
          steps:
          - name: a1l1
            mode: Incremental
            resource_group: rgn
        a2: 
          steps:
          - name: a2l1
            mode: Incremental
            arm_file: arm_file.json
            resource_group: rgn
      folder: some/path
"""

        under_test = apply_applications_test(file_text)
        result = under_test.frames.arm_file_paths()

        assert result == {
            StructuredName(["f1", "a1", "a1l1"]): FrameFile(
                dir=pathlib.Path("some/path/"), file=None
            ),
            StructuredName(["f1", "a2", "a2l1"]): FrameFile(
                dir=pathlib.Path("some/path/"),
                file=pathlib.Path("arm_file.json"),
            ),
        }

    def test_subpath(self, apply_applications_test):
        file_text = """---
frames:
  frames:
    f1:
      applications:
        a1: 
          steps:
          - name: a1l1
            mode: Incremental
            arm_file: other/path/arm_file.json
            resource_group: rgn
      folder: some/path
"""

        under_test = apply_applications_test(file_text)
        result = under_test.frames.arm_file_paths()

        assert result == {
            StructuredName(["f1", "a1", "a1l1"]): FrameFile(
                dir=pathlib.Path("some/path/"),
                file=pathlib.Path("other/path/arm_file.json"),
            )
        }


class TestPuffFilePaths:
    def test_default(self, apply_applications_test):
        file_text = """---
frames:
  frames:
    f1:
      applications:
        a1: 
          steps:
          - name: a1l1
            mode: Incremental
            resource_group: rgn
      folder: some/path
"""

        under_test = apply_applications_test(file_text)
        result = under_test.frames.puff_file_paths()

        assert result == {
            StructuredName(["f1", "a1", "a1l1"]): FrameFile(
                dir=pathlib.Path("some/path/"),
                file=None,
            ),
        }

    def test_explicit(self, apply_applications_test):
        file_text = """---
frames:
  frames:
    f1:
      applications:
        a1: 
          steps:
          - name: a1l1
            mode: Incremental
            puff_file: puff_file.yml
            resource_group: rgn
      folder: some/path
"""

        under_test = apply_applications_test(file_text)
        result = under_test.frames.puff_file_paths()

        assert result == {
            StructuredName(["f1", "a1", "a1l1"]): FrameFile(
                dir=pathlib.Path("some/path/"),
                file=pathlib.Path("puff_file.yml"),
            )
        }

    def test_mixed(self, apply_applications_test):
        file_text = """---
frames:
  frames:
    f1:
      applications:
        a1: 
          steps:
          - name: a1l1
            mode: Incremental
            resource_group: rgn
        a2: 
          steps:
          - name: a2l1
            mode: Incremental
            puff_file: puff/file.yml
            resource_group: rgn
      folder: some/path
"""

        under_test = apply_applications_test(file_text)
        result = under_test.frames.puff_file_paths()

        assert result == {
            StructuredName(["f1", "a1", "a1l1"]): FrameFile(
                dir=pathlib.Path("some/path/"),
                file=None,
            ),
            StructuredName(["f1", "a2", "a2l1"]): FrameFile(
                dir=pathlib.Path("some/path/"),
                file=pathlib.Path("puff/file.yml"),
            ),
        }

    def test_subpath(self, apply_applications_test):
        file_text = """---
frames:
  frames:
    f1:
      applications:
        a1: 
          steps:
          - name: a1l1
            mode: Incremental
            puff_file: other/path/puff_file.yml
            resource_group: rgn
      folder: some/path
"""

        under_test = apply_applications_test(file_text)
        result = under_test.frames.puff_file_paths()

        assert result == {
            StructuredName(["f1", "a1", "a1l1"]): FrameFile(
                dir=pathlib.Path("some/path/"),
                file=pathlib.Path("other/path/puff_file.yml"),
            )
        }


class TestFrameFolders:
    def test_single(self, apply_applications_test):
        file_text = """---
frames:
  frames:
    f1:
      applications:
        a1: 
          steps:
          - name: a1l1
            mode: Incremental
            resource_group: rgn
      folder: some/path
"""

        under_test = apply_applications_test(file_text)
        result = under_test.frames.frame_folders()

        assert result == {
            StructuredName(["f1"]): FrameFile(
                dir=pathlib.Path("some/path"), file=pathlib.Path("")
            )
        }

    def test_multiple(self, apply_applications_test):
        file_text = """---
frames:
  frames:
    f1:
      applications:
        a1: 
          steps:
          - name: a1l1
            mode: Incremental
            resource_group: rgn
      folder: some/path
    f2:
      applications:
        a1: 
          steps:
          - name: a1l1
            mode: Incremental
            resource_group: rgn
      folder: f2/path
"""

        under_test = apply_applications_test(file_text)
        result = under_test.frames.frame_folders()

        assert result == {
            StructuredName(["f1"]): FrameFile(
                dir=pathlib.Path("some/path"), file=pathlib.Path("")
            ),
            StructuredName(["f2"]): FrameFile(
                dir=pathlib.Path("f2/path"), file=pathlib.Path("")
            ),
        }
