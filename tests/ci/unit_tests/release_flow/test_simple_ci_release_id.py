#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

from foodx_devops_tools.release_flow.npm_ci import (
    acquire_release_id,
    normalize_package_name,
    output_package_name,
)


class TestNormalizePackageName:
    def test_group(self):
        result = normalize_package_name("@this-group/some-name")

        assert result == "this-group-some-name"

    def test_no_group(self):
        result = normalize_package_name("some-name")

        assert result == "some-name"


class TestAcquireReleaseId:
    # Pytest capturing stdout https://docs.pytest.org/en/6.2.x/capture.html
    def test_main_branch(self, mocker):
        mock_arguments = [
            "refs/heads/main",
            "123abc",
        ]
        mocker.patch(
            "foodx_devops_tools.release_flow._simple_ci_release_id.acquire_post_data",
            return_value=("3.1.4", "26"),
        )

        result = acquire_release_id(*mock_arguments)

        assert result == "3.1.4-post.26.123abc"

    def test_long_sha(self, mocker):
        mock_arguments = [
            "refs/heads/main",
            "123abc123abc123abc",
        ]
        mocker.patch(
            "foodx_devops_tools.release_flow._simple_ci_release_id.acquire_post_data",
            return_value=("3.1.4", "26"),
        )

        result = acquire_release_id(*mock_arguments)

        assert result == "3.1.4-post.26.123abc1"

    def test_release_tag(self, capsys, mocker):
        mock_arguments = [
            "refs/tags/31.415.9",
            "123abc",
        ]
        mocker.patch(
            "foodx_devops_tools.release_flow._simple_ci_release_id.acquire_post_data",
            return_value=("3.1.4", "26"),
        )

        result = acquire_release_id(*mock_arguments)

        assert result == "31.415.9"

    def test_semantic_prerelease_tag(self, capsys, mocker):
        """
        Should not be using prerelease tags, but if they are used then
        they are a local release id (essential ignored).
        """
        mock_arguments = [
            "refs/tags/31.415.9-alpha.4",
            "123abc",
        ]
        mocker.patch(
            "foodx_devops_tools.release_flow._simple_ci_release_id.acquire_post_data",
            return_value=("3.1.4", "26"),
        )

        result = acquire_release_id(*mock_arguments)

        assert result == "3.1.4-post.26.123abc"

    def test_dryrun_tag(self, capsys, mocker):
        """Dryrun tag should be preserved as if it were a release."""
        mock_arguments = [
            "refs/tags/31.415.9-dryrun15",
            "123abc",
        ]
        mocker.patch(
            "foodx_devops_tools.release_flow._simple_ci_release_id.acquire_post_data",
            return_value=("3.1.4", "26"),
        )

        result = acquire_release_id(*mock_arguments)

        assert result == "31.415.9-dryrun15"

    def test_feature_branch(self, capsys, mocker):
        mock_arguments = [
            "refs/heads/feature/rcs/some_branch",
            "123abc",
        ]
        mocker.patch(
            "foodx_devops_tools.release_flow._simple_ci_release_id.acquire_post_data",
            return_value=("3.1.4", "26"),
        )

        result = acquire_release_id(*mock_arguments)

        assert result == "3.1.4-post.26.123abc"


class TestOutputPackageName:
    def test_output1(self, capsys):
        arguments = [
            "some-package",
            "3.1.4",
        ]

        output_package_name(*arguments)

        content = capsys.readouterr()
        assert content.out == "some-package-3.1.4.tgz"

    def test_output2(self, capsys):
        arguments = [
            "group-some-package",
            "3.1.4",
        ]

        output_package_name(*arguments)

        content = capsys.readouterr()
        assert content.out == "group-some-package-3.1.4.tgz"
