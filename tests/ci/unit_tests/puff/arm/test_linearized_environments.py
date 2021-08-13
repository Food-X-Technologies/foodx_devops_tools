#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

from foodx_devops_tools.puff.arm import _linearize_environments


class TestLinearizedEnvironments:
    def test_environments_regions(self):
        mock_base = {
            "this.stub": {
                "p1": "bp1",
                "k2": "bk2",
                "environments": {
                    "e1": {
                        "k1": "e1k1",
                        "regions": [
                            {"r1": {"k1": "e1r1k1"}},
                            {"r2": {"k2": "e1r2k2"}},
                        ],
                    },
                },
            },
        }
        expected_result = {
            "this.stub.e1": {
                "environment": "e1",
                "p1": "bp1",
                "k1": "e1k1",
                "k2": "bk2",
                "regions": [
                    {"r1": {"k1": "e1r1k1"}},
                    {"r2": {"k2": "e1r2k2"}},
                ],
            },
        }
        result = _linearize_environments(mock_base)

        assert result == expected_result

    def test_multiple_stubs_multiple_environments(self):
        mock_base = {
            "stub1": {
                "p1": "stub1.p1",
                "k2": "stub1.k2",
                # "full" environment
                "environments": {
                    "e1": {
                        "k1": "e1k1",
                    },
                    "e2": {
                        "k1": "e2k1",
                    },
                },
            },
        }
        expected_result = {
            "stub1.e1": {
                "environment": "e1",
                "p1": "stub1.p1",
                "k1": "e1k1",
                "k2": "stub1.k2",
            },
            "stub1.e2": {
                "environment": "e2",
                "p1": "stub1.p1",
                "k1": "e2k1",
                "k2": "stub1.k2",
            },
        }
        result = _linearize_environments(mock_base)

        assert result == expected_result

    def test_multiple_stubs_mixed_environments(self):
        mock_base = {
            "stub1": {
                "p1": "stub1.p1",
                "k2": "stub1.k2",
                # "full" environment
                "environments": {
                    "e1": {
                        "k1": "e1k1",
                        "regions": [
                            {"r1": {"k1": "e1r1k1"}},
                            {"r2": {"k2": "e1r2k2"}},
                        ],
                    },
                },
            },
            "stub2": {
                "p1": "stub2.p1",
                "k2": "stub2.k2",
                # empty environment
                "environments": dict(),
            },
        }
        expected_result = {
            "stub1.e1": {
                "environment": "e1",
                "p1": "stub1.p1",
                "k1": "e1k1",
                "k2": "stub1.k2",
                "regions": [
                    {"r1": {"k1": "e1r1k1"}},
                    {"r2": {"k2": "e1r2k2"}},
                ],
            },
            "stub2": {
                "p1": "stub2.p1",
                "k2": "stub2.k2",
            },
        }
        result = _linearize_environments(mock_base)

        assert result == expected_result

    def test_empty_environments(self):
        mock_base = {
            "this.stub": {
                "p1": "bp1",
                "k2": "bk2",
                "environments": dict(),
            },
        }
        expected_result = {
            "this.stub": {
                "p1": "bp1",
                "k2": "bk2",
            },
        }
        result = _linearize_environments(mock_base)

        assert result == expected_result

    def test_environments_no_environment_regions(self):
        mock_base = {
            "this.stub": {
                "p1": "bp1",
                "k2": "bk2",
                "environments": {
                    "e1": {
                        "k1": "e1k1",
                    },
                },
            },
        }
        expected_result = {
            "this.stub.e1": {
                "environment": "e1",
                "p1": "bp1",
                "k1": "e1k1",
                "k2": "bk2",
            },
        }
        result = _linearize_environments(mock_base)

        assert result == expected_result

    def test_no_environments_no_regions(self):
        mock_base = {
            "this.stub": {
                "p1": "bp1",
                "k2": "bk2",
            },
        }
        expected_result = {
            "this.stub": {
                "p1": "bp1",
                "k2": "bk2",
            },
        }
        result = _linearize_environments(mock_base)

        assert result == expected_result

    def test_no_environments_no_regions_empty_base(self):
        mock_base = {
            "this.stub": dict(),
        }
        expected_result = {
            "this.stub": dict(),
        }
        result = _linearize_environments(mock_base)

        assert result == expected_result

    def test_environments_empty_base(self):
        mock_base = {
            "this.stub": {
                "environments": {
                    "e1": {
                        "k1": "e1k1",
                        "regions": [
                            {"r1": {"k1": "e1r1k1"}},
                            {"r2": {"k2": "e1r2k2"}},
                        ],
                    },
                },
            },
        }
        expected_result = {
            "this.stub.e1": {
                "environment": "e1",
                "k1": "e1k1",
                "regions": [
                    {"r1": {"k1": "e1r1k1"}},
                    {"r2": {"k2": "e1r2k2"}},
                ],
            },
        }
        result = _linearize_environments(mock_base)

        assert result == expected_result

    def test_none_environments(self):
        mock_base = {
            "this.stub": {
                "k1": "k1",
                "environments": {
                    "e1": None,
                },
            },
        }
        expected_result = {
            "this.stub.e1": {
                "environment": "e1",
                "k1": "k1",
            },
        }
        result = _linearize_environments(mock_base)

        assert result == expected_result
