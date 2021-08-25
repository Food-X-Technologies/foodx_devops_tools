#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

import contextlib
import os
import pathlib
import tempfile

import ruamel.yaml

from foodx_devops_tools.pipeline_config import (
    DeploymentContext,
    PipelineConfigurationPaths,
)
from foodx_devops_tools.pipeline_config.service_principals import _encrypt_vault

MOCK_CONTEXT = DeploymentContext(
    commit_sha="abc123",
    pipeline_id="12345",
    release_id="0.0.0-dev.3",
    release_state="r1",
)

CLEAN_SPLIT = {
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
NOT_SPLIT = {
    "client": {},
    "system": {
        "release_states",
        "subscriptions",
        "systems",
        "tenants",
        "clients",
        "deployments",
        "frames",
        "puff_map",
        "service_principals",
    },
}

MOCK_SECRET = "verysecret"

MOCK_RESULTS = {
    "clients": {
        "c1": {
            "release_states": [
                "r1",
                "r2",
            ],
            "system": "sys1",
        },
        "c2": {
            "release_states": [
                "r2",
            ],
            "system": "sys2",
        },
    },
    "deployments": {
        "sys1-c1-r1": {
            "subscriptions": {
                "sub1": {
                    "locations": [{"primary": "l1"}, {"primary": "l2"}],
                },
            },
        },
    },
    "frames": {
        "frames": {
            "f1": {
                "applications": {
                    "a1": [
                        {
                            "resource_group": "a1_group",
                            "name": "a1l1",
                            "mode": "Incremental",
                        },
                    ],
                },
                "folder": "some/path",
            },
        },
    },
    "puff_map": {
        "frames": {
            "f1": {
                "applications": {
                    "a1": {
                        "arm_parameters_files": {
                            "r1": {
                                "sub1": {
                                    "a1l1": "some/puff_map/path",
                                },
                            },
                        },
                    },
                },
            },
        },
    },
    "release_states": ["r1", "r2"],
    "service_principals": {
        "sub1": {"id": "12345", "secret": "verysecret", "name": "sp_name"},
    },
    "subscriptions": {
        "sub1": {
            "ado_service_connection": "some-name",
            "azure_id": "abc123",
            "tenant": "t1",
        },
    },
    "systems": ["sys1", "sys2"],
    "tenants": {"t1": {"azure_id": "123abc"}},
}

MOCK_PATHS = PipelineConfigurationPaths(
    **{
        "clients": pathlib.Path("client/path"),
        "release_states": pathlib.Path("release_state/path"),
        "deployments": pathlib.Path("deployment/path"),
        "frames": pathlib.Path("frame/path"),
        "puff_map": pathlib.Path("puff_map/path"),
        "service_principals": pathlib.Path("service_principal/path"),
        "subscriptions": pathlib.Path("subscription/path"),
        "systems": pathlib.Path("system/path"),
        "tenants": pathlib.Path("tenant/path"),
    }
)


@contextlib.contextmanager
def split_directories(split: dict, decrypt_token: str = MOCK_SECRET):
    """Generate configuration files split across two directories."""
    yaml = ruamel.yaml.YAML(typ="safe")
    with tempfile.TemporaryDirectory() as dir1:
        pd1 = pathlib.Path(dir1)
        with tempfile.TemporaryDirectory() as dir2:
            pd2 = pathlib.Path(dir2)
            paths = {
                "client": pd1,
                "system": pd2,
            }
            for key, files in split.items():
                for this_file in files:
                    if this_file != "service_principals":
                        file_path = paths[key] / "{0}.yml".format(this_file)
                        with file_path.open(mode="w") as f:
                            yaml.dump({this_file: MOCK_RESULTS[this_file]}, f)
                    else:
                        # service_principals requires special handling due to
                        # encryption
                        file_path = paths[key] / "{0}.yml".format(this_file)
                        with file_path.open(mode="w") as f:
                            yaml.dump({this_file: MOCK_RESULTS[this_file]}, f)

                        encrypted_file_path = paths[key] / "{0}.vault".format(
                            this_file
                        )
                        password_file_path = pathlib.Path(
                            str(encrypted_file_path) + ".password"
                        )
                        with password_file_path.open(mode="w") as f:
                            f.write(decrypt_token)
                        _encrypt_vault(
                            encrypted_file_path, password_file_path, file_path
                        )

                        os.remove(password_file_path)
                        os.remove(file_path)

            yield pd1, pd2
