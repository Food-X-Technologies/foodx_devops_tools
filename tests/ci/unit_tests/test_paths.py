#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

import pytest

from foodx_devops_tools.pipeline_config import PipelineConfigurationPaths
from foodx_devops_tools.pipeline_config.exceptions import (
    ConfigurationPathsError,
)
from tests.ci.support.pipeline_config import CLEAN_SPLIT, split_directories


class TestFromPaths:
    def test_clean(self):
        with split_directories(CLEAN_SPLIT.copy()) as (
            client_path,
            system_path,
        ):
            client_config = client_path / "configuration"
            system_config = system_path / "configuration"
            under_test = PipelineConfigurationPaths.from_paths(
                client_config, system_config
            )

            all_paths = set(client_config.iterdir()).union(
                set(system_config.iterdir())
            )
            all_names = CLEAN_SPLIT["client"].union(CLEAN_SPLIT["system"])
            for this_name in all_names:
                if this_name != "static_secrets":
                    assert getattr(under_test, this_name) in all_paths

            assert {x.stem for x in under_test.static_secrets} == {
                "sys1_c1_r1a"
            }

    def test_no_secrets(self):
        split = {
            # duplicates between client and system dirs
            "client": {
                "clients",
                "deployments",
                "frames",
                "puff_map",
                "service_principals",
            },
            "system": {
                "release_states",
                "subscriptions",
                "systems",
                "tenants",
            },
        }
        with split_directories(split) as (
            client_path,
            system_path,
        ):
            client_config = client_path / "configuration"
            system_config = system_path / "configuration"
            under_test = PipelineConfigurationPaths.from_paths(
                client_config, system_config
            )

            all_paths = set(client_config.iterdir()).union(
                set(system_config.iterdir())
            )
            all_names = split["client"].union(split["system"])
            for this_name in all_names:
                assert getattr(under_test, this_name) in all_paths

            assert not under_test.static_secrets

    def test_duplicates_raises(self):
        split = {
            # duplicates between client and system dirs
            "client": {
                "clients",
                "deployments",
                "frames",
                "puff_map",
                "release_states",
                "service_principals",
            },
            "system": {
                "release_states",
                "subscriptions",
                "systems",
                "tenants",
            },
        }
        with split_directories(split) as (
            client_path,
            system_path,
        ), pytest.raises(
            ConfigurationPathsError,
            match=r"^Duplicate files between directories",
        ):
            client_config = client_path / "configuration"
            system_config = system_path / "configuration"
            PipelineConfigurationPaths.from_paths(client_config, system_config)
