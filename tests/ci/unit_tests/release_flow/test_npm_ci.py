# Copyright (c) 2021 Food-X Technologies
#
# This file is part of foodx_devops_tools.
#
# You should have received a copy of the MIT License along with
# foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

from foodx_devops_tools.release_flow_entry import release_flow
from tests.ci.support.click_runner import click_runner  # noqa: F401


class TestNpmSubcommand:
    MOCK_PACKAGE_JSON_CONTENT = """{
  "author": "FoodX",
  "description": "some package",
  "keywords": [
    "foodx"
  ],
  "license": "SEE LICENSE IN LICENSE",
  "name": "@foodx/some-package",
  "version": "0.0.0+local"
}
"""

    def test_npm_id_nonrelease(self, click_runner, mocker):
        mock_input = [
            "npm",
            "id",
            "package.json",
            "refs/tags/3.14.159-alpha.13",
            "abc123def",
        ]
        mocker.patch(
            "foodx_devops_tools.release_flow._simple_ci_release_id.acquire_post_data",
            return_value=("3.1.4", "26"),
        )

        result = click_runner.invoke(release_flow, mock_input)

        assert result.exit_code == 0
        assert result.output == "3.1.4-post.26.abc123d"

    def test_npm_id_release(self, click_runner, mocker):
        mock_input = [
            "npm",
            "id",
            "package.json",
            "refs/tags/3.14.159",
            "abc123def",
        ]
        mocker.patch(
            "foodx_devops_tools.release_flow._simple_ci_release_id.acquire_post_data",
            return_value=("3.1.4", "26"),
        )

        result = click_runner.invoke(release_flow, mock_input)

        assert result.exit_code == 0
        assert result.output == "3.14.159"

    def test_npm_package_nonrelease(self, click_runner, mocker):
        mock_input = [
            "npm",
            "package",
            "package.json",
            "refs/tags/3.14.159-alpha.13",
            "abc123def",
        ]
        mocker.patch(
            "foodx_devops_tools.release_flow._simple_ci_release_id.acquire_post_data",
            return_value=("3.1.4", "26"),
        )

        with click_runner.isolated_filesystem():
            with open("package.json", mode="w") as f:
                f.write(self.MOCK_PACKAGE_JSON_CONTENT)
            result = click_runner.invoke(release_flow, mock_input)

        assert result.exit_code == 0
        assert result.output == "foodx-some-package-3.1.4-post.26.abc123d.tgz"

    def test_npm_package_release(self, click_runner, mocker):
        mock_input = [
            "npm",
            "package",
            "package.json",
            "refs/tags/3.14.159",
            "abc123def",
        ]
        mocker.patch(
            "foodx_devops_tools.release_flow._simple_ci_release_id.acquire_post_data",
            return_value=("3.1.4", "26"),
        )

        with click_runner.isolated_filesystem():
            with open("package.json", mode="w") as f:
                f.write(self.MOCK_PACKAGE_JSON_CONTENT)
            result = click_runner.invoke(release_flow, mock_input)

        assert result.exit_code == 0
        assert result.output == "foodx-some-package-3.14.159.tgz"

    def test_main_branch(self, click_runner, mocker):
        mock_arguments = [
            "npm",
            "package",
            "package.json",
            "refs/heads/main",
            "123abc",
        ]
        mocker.patch(
            "foodx_devops_tools.release_flow.npm_ci.apply_package_release_id",
            return_value="@some-group/this-package",
        )
        mocker.patch(
            "foodx_devops_tools.release_flow._simple_ci_release_id.acquire_post_data",
            return_value=("3.1.4", "26"),
        )

        with click_runner.isolated_filesystem():
            with open("package.json", mode="w") as f:
                f.write(self.MOCK_PACKAGE_JSON_CONTENT)
            result = click_runner.invoke(release_flow, mock_arguments)

        assert result.exit_code == 0
        assert (
            result.output == "some-group-this-package-3.1.4-post.26.123abc.tgz"
        )

    def test_release_tag(self, click_runner, mocker):
        mock_arguments = [
            "npm",
            "package",
            "package.json",
            "refs/tags/3.14.159",
            "123abc",
        ]
        mocker.patch(
            "foodx_devops_tools.release_flow.npm_ci.apply_package_release_id",
            return_value="@some-group/this-package",
        )
        mocker.patch(
            "foodx_devops_tools.release_flow._simple_ci_release_id.acquire_post_data",
            return_value=("3.1.4", "26"),
        )

        with click_runner.isolated_filesystem():
            with open("package.json", mode="w") as f:
                f.write(self.MOCK_PACKAGE_JSON_CONTENT)
            result = click_runner.invoke(release_flow, mock_arguments)

        assert result.exit_code == 0
        assert result.output == "some-group-this-package-3.14.159.tgz"

    def test_dryrun_tag(self, click_runner, mocker):
        mock_arguments = [
            "npm",
            "package",
            "package.json",
            "refs/tags/3.14.159-dryrun45",
            "123abc",
        ]
        mocker.patch(
            "foodx_devops_tools.release_flow.npm_ci.apply_package_release_id",
            return_value="@some-group/this-package",
        )
        mocker.patch(
            "foodx_devops_tools.release_flow._simple_ci_release_id.acquire_post_data",
            return_value=("3.1.4", "26"),
        )

        with click_runner.isolated_filesystem():
            with open("package.json", mode="w") as f:
                f.write(self.MOCK_PACKAGE_JSON_CONTENT)
            result = click_runner.invoke(release_flow, mock_arguments)

        assert result.exit_code == 0
        assert result.output == "some-group-this-package-3.14.159-dryrun45.tgz"
