# Copyright (c) 2021 Food-X Technologies
#
# This file is part of foodx_devops_tools.
#
# You should have received a copy of the MIT License along with
# foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

import pytest

from foodx_devops_tools.release_flow._cd_release_state import (
    ReleaseState,
    ReleaseStateError,
    identify_release_state,
)


class TestIdentifyReleaseState:
    def test_clean_feature(self):
        expected_state = ReleaseState.ftr

        result = identify_release_state("refs/heads/feature/some/path")
        assert result == expected_state

        # Assume PR is only valid for feature/*->main
        result = identify_release_state("refs/pull/1/merge")
        assert result == expected_state

    def test_clean_development(self):
        expected_state = ReleaseState.dev

        result = identify_release_state("refs/heads/main")
        assert result == expected_state

    def test_clean_qa(self):
        expected_state = ReleaseState.qa

        result = identify_release_state("refs/tags/3.14.159-alpha.13")
        assert result == expected_state

    def test_clean_staging(self):
        expected_state = ReleaseState.stg

        result = identify_release_state("refs/tags/3.14.159-beta.13")
        assert result == expected_state

    def test_clean_production(self):
        expected_state = ReleaseState.prd

        result = identify_release_state("refs/tags/3.14.159")
        assert result == expected_state

    def test_dirty_qa(self):
        """Only strictly semantic version alpha tags allowed."""
        with pytest.raises(
            ReleaseStateError,
            match="^Unable to match git reference to any release state",
        ):
            identify_release_state("refs/tags/3.14.159-alpha")

        with pytest.raises(
            ReleaseStateError,
            match="^Unable to match git reference to any release state",
        ):
            identify_release_state("refs/tags/3.14.159-alpha13")

    def test_dirty_staging(self):
        """Only strictly semantic version beta tags allowed."""
        with pytest.raises(
            ReleaseStateError,
            match="^Unable to match git reference to any release state",
        ):
            identify_release_state("refs/tags/3.14.159-beta")

        with pytest.raises(
            ReleaseStateError,
            match="^Unable to match git reference to any release state",
        ):
            identify_release_state("refs/tags/3.14.159-beta13")

    def test_dirty_production(self):
        """Only strictly semantic releases are allowed."""
        with pytest.raises(
            ReleaseStateError,
            match="^Unable to match git reference to any release state",
        ):
            identify_release_state("refs/tags/3.14.159.54")
