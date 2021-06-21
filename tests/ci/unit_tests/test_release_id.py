# Copyright (c) 2021 Food-X Technologies
#
# This file is part of foodx_devops_tools.
#
# You should have received a copy of the MIT License along with
# foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

import pytest

from foodx_devops_tools.release_id import (
    ReleaseIdentityError,
    _main,
    identify_release_id,
)

from ..support.capture import capture_stdout_stderr


class TestIdentifyReleaseId:
    def test_clean_feature(self):
        expected_id = "0.0.0-post.000"

        result = identify_release_id("refs/heads/feature/some/path")
        assert result == expected_id

        # Assume PR is only valid for feature/*->main
        result = identify_release_id("refs/pull/1/merge")
        assert result == expected_id

    def test_clean_development(self):
        expected_id = "0.0.0-post.000"

        result = identify_release_id("refs/heads/main")
        assert result == expected_id

    def test_clean_qa(self):
        expected_id = "3.14.159-alpha.13"

        result = identify_release_id("refs/tags/3.14.159-alpha.13")
        assert result == expected_id

    def test_clean_staging(self):
        expected_id = "3.14.159-beta.13"

        result = identify_release_id("refs/tags/3.14.159-beta.13")
        assert result == expected_id

    def test_clean_production(self):
        expected_id = "3.14.159"

        result = identify_release_id("refs/tags/3.14.159")
        assert result == expected_id

    def test_dirty_qa(self):
        """Only strictly semantic version alpha tags allowed."""
        with pytest.raises(
            ReleaseIdentityError,
            match="^Unable to match git reference to any release id",
        ):
            identify_release_id("refs/tags/3.14.159-alpha")

        with pytest.raises(
            ReleaseIdentityError,
            match="^Unable to match git reference to any release id",
        ):
            identify_release_id("refs/tags/3.14.159-alpha13")

    def test_dirty_staging(self):
        """Only strictly semantic version beta tags allowed."""
        with pytest.raises(
            ReleaseIdentityError,
            match="^Unable to match git reference to any release id",
        ):
            identify_release_id("refs/tags/3.14.159-beta")

        with pytest.raises(
            ReleaseIdentityError,
            match="^Unable to match git reference to any release id",
        ):
            identify_release_id("refs/tags/3.14.159-beta13")

    def test_dirty_production(self):
        """Only strictly semantic releases are allowed."""
        with pytest.raises(
            ReleaseIdentityError,
            match="^Unable to match git reference to any release id",
        ):
            identify_release_id("refs/tags/3.14.159.54")

    def test_unknown_state(self, mocker):
        mocker.patch("foodx_devops_tools.release_id.identify_release_state")
        with pytest.raises(
            ReleaseIdentityError,
            match="^Unable to match git reference to any release id",
        ):
            identify_release_id("refs/tags/3.14.159.54")


class TestMain:
    def test_default(self):
        mock_input = ["release_id", "refs/tags/3.14.159-alpha.13"]

        with capture_stdout_stderr() as (captured_out, captured_err):
            _main(mock_input)

        captured_out.seek(0)

        assert captured_out.read().strip() == "3.14.159-alpha.13"
