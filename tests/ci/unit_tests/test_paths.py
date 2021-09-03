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
            client_config,
            system_config,
        ):
            under_test = PipelineConfigurationPaths.from_paths(
                client_config, system_config
            )

            all_paths = set(client_config.iterdir()).union(
                set(system_config.iterdir())
            )
            all_names = CLEAN_SPLIT["client"].union(CLEAN_SPLIT["system"])
            for this_name in all_names:
                assert getattr(under_test, this_name) in all_paths

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
            client_config,
            system_config,
        ), pytest.raises(
            ConfigurationPathsError,
            match=r"^Duplicate files between directories",
        ):
            PipelineConfigurationPaths.from_paths(client_config, system_config)