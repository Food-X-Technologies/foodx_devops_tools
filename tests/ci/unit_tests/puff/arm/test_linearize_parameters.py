#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

from ruamel.yaml import YAML

from foodx_devops_tools.puff.arm import _linearize_parameters


class TestLinearizeParameters:
    def test_name(self):
        mock_base = {
            "name": "some-name",
            "p1": "bp1",
            "k2": "bk2",
            "environments": {
                "e1": dict(),
            },
        }
        expected_result = {
            "some-name.e1": {
                "environment": "e1",
                "p1": "bp1",
                "k2": "bk2",
            },
        }
        result = _linearize_parameters(mock_base, "this.stub")

        assert result == expected_result

    def test_default_name(self):
        mock_base = {
            "name": "file-name",
            "default": {"name": "name-variable-value"},
            "p1": "bp1",
            "k2": "bk2",
            "environments": {
                "e1": dict(),
            },
        }
        expected_result = {
            "file-name.e1": {
                "environment": "e1",
                "name": "name-variable-value",
                "p1": "bp1",
                "k2": "bk2",
            },
        }
        result = _linearize_parameters(mock_base, "this.stub")

        assert result == expected_result

    def test_empty_environment(self):
        mock_base = {
            "p1": "bp1",
            "k2": "bk2",
            "environments": {
                "e1": dict(),
            },
        }
        expected_result = {
            "this.stub.e1": {
                "environment": "e1",
                "p1": "bp1",
                "k2": "bk2",
            },
        }
        result = _linearize_parameters(mock_base, "this.stub")

        assert result == expected_result

    def test_environment_empty_region(self):
        mock_base = {
            "p1": "bp1",
            "k2": "bk2",
            "environments": {
                "e1": {
                    "p1": "e1p1",
                    "regions": [
                        {
                            "r1": dict(),
                        }
                    ],
                },
            },
        }
        expected_result = {
            "this.stub.e1.r1": {
                "environment": "e1",
                "region": "r1",
                "p1": "e1p1",
                "k2": "bk2",
            },
        }
        result = _linearize_parameters(mock_base, "this.stub")

        assert result == expected_result

    def test_environment_none_region(self):
        mock_base = {
            "p1": "bp1",
            "k2": "bk2",
            "environments": {
                "e1": {
                    "p1": "e1p1",
                    "regions": [
                        {
                            "r1": None,
                        }
                    ],
                },
            },
        }
        expected_result = {
            "this.stub.e1.r1": {
                "environment": "e1",
                "region": "r1",
                "p1": "e1p1",
                "k2": "bk2",
            },
        }
        result = _linearize_parameters(mock_base, "this.stub")

        assert result == expected_result

    def test_environment_empty_region_empty_base(self):
        mock_base = {
            "environments": {
                "e1": {
                    "p1": "e1p1",
                    "regions": [
                        {
                            "r1": dict(),
                        }
                    ],
                },
            },
        }
        expected_result = {
            "this.stub.e1.r1": {
                "environment": "e1",
                "region": "r1",
                "p1": "e1p1",
            },
        }
        result = _linearize_parameters(mock_base, "this.stub")

        assert result == expected_result

    def test_environment_none_region_empty_base(self):
        mock_base = {
            "environments": {
                "e1": {
                    "p1": "e1p1",
                    "regions": [
                        {
                            "r1": None,
                        }
                    ],
                },
            },
        }
        expected_result = {
            "this.stub.e1.r1": {
                "environment": "e1",
                "region": "r1",
                "p1": "e1p1",
            },
        }
        result = _linearize_parameters(mock_base, "this.stub")

        assert result == expected_result

    def test_from_yaml(self):
        mock_data = """services:
  s1:
    p1: s1p1
    environments:
      e1:
        p1: s1e1p1
        regions:
          - r1:
              p1: s1e1r1p1
              p2:
                reference: 
                  keyVault:
                    id: idv
                  secretName: sn
        """
        expected_result = {
            "this.stub.s1.e1.r1": {
                "service": "s1",
                "environment": "e1",
                "region": "r1",
                "p1": "s1e1r1p1",
                "p2": {
                    "reference": {
                        "keyVault": {"id": "idv"},
                        "secretName": "sn",
                    },
                },
            },
        }
        yaml = YAML(typ="safe")
        yaml_data = yaml.load(mock_data)

        result = _linearize_parameters(yaml_data, "this.stub")

        assert result == expected_result

    def test_complex1_clean(self):
        mock_base = {
            "p1": "bp1",
            "bp2": "bp2",
            "environments": {
                "e1": {
                    "p1": "e1p1",
                    "e1p2": "e1p2",
                    "regions": [
                        {
                            "r1": dict(),
                        }
                    ],
                },
            },
            "services": {
                "s1": {
                    "s1p2": "s1p2",
                    "environments": {
                        "e1": {
                            "s1e1p2": "s1e1p2",
                            "regions": [
                                {
                                    "r1": {
                                        "p1": "s1e1r1p1",
                                    },
                                }
                            ],
                        },
                    },
                },
            },
        }
        expected_result = {
            "filestub.s1.e1.r1": {
                "service": "s1",
                "environment": "e1",
                "region": "r1",
                "p1": "s1e1r1p1",
                "bp2": "bp2",
                "e1p2": "e1p2",
                "s1p2": "s1p2",
                "s1e1p2": "s1e1p2",
            },
        }
        result = _linearize_parameters(mock_base, "filestub")

        assert result == expected_result

    def test_complex2_clean(self):
        mock_base = {
            "p1": "bp1",
            "bp2": "bp2",
            "environments": {
                "e1": {
                    "p1": "e1p1",
                    "e1p2": "e1p2",
                    "regions": [
                        {
                            "r1": dict(),
                        }
                    ],
                },
            },
            "services": {
                "s1": {
                    "s1p2": "s1p2",
                    "environments": {
                        "e1": {
                            "s1e1p2": "s1e1p2",
                            "regions": [
                                {
                                    "r1": {
                                        "p1": "s1e1r1p1",
                                    },
                                }
                            ],
                        },
                    },
                },
                "s2": {
                    "s2p2": "s2p2",
                    "environments": {
                        "e1": {
                            "s2e1p2": "s2e1p2",
                            "regions": [
                                {
                                    "r1": {
                                        "p1": "s2e1r1p1",
                                    },
                                }
                            ],
                        },
                    },
                },
            },
        }
        expected_result = {
            "filestub.s1.e1.r1": {
                "service": "s1",
                "environment": "e1",
                "region": "r1",
                "p1": "s1e1r1p1",
                "bp2": "bp2",
                "e1p2": "e1p2",
                "s1p2": "s1p2",
                "s1e1p2": "s1e1p2",
            },
            "filestub.s2.e1.r1": {
                "service": "s2",
                "environment": "e1",
                "region": "r1",
                "p1": "s2e1r1p1",
                "bp2": "bp2",
                "e1p2": "e1p2",
                "s2p2": "s2p2",
                "s2e1p2": "s2e1p2",
            },
        }
        result = _linearize_parameters(mock_base, "filestub")

        assert result == expected_result

    def test_complex3_clean(self):
        mock_base = {
            "p1": "bp1",
            "bp2": "bp2",
            "environments": {
                "e1": {
                    "p1": "e1p1",
                    "e1p2": "e1p2",
                    "regions": [
                        {
                            "r1": {
                                "e1r1p2": "e1r1p2",
                            },
                        }
                    ],
                },
            },
            "services": {
                "s1": {
                    "s1p2": "s1p2",
                    "environments": {
                        "e1": {
                            "s1e1p2": "s1e1p2",
                            "regions": [
                                {
                                    "r1": {
                                        "p1": "s1e1r1p1",
                                    },
                                }
                            ],
                        },
                    },
                },
                "s2": {
                    "s2p2": "s2p2",
                    "environments": {
                        "e1": {
                            "s2e1p2": "s2e1p2",
                            "regions": [
                                {
                                    "r1": {
                                        "p1": "s2e1r1p1",
                                    },
                                }
                            ],
                        },
                    },
                },
            },
        }
        expected_result = {
            "filestub.s1.e1.r1": {
                "service": "s1",
                "environment": "e1",
                "region": "r1",
                "p1": "s1e1r1p1",
                "bp2": "bp2",
                "e1r1p2": "e1r1p2",
                "e1p2": "e1p2",
                "s1p2": "s1p2",
                "s1e1p2": "s1e1p2",
            },
            "filestub.s2.e1.r1": {
                "service": "s2",
                "environment": "e1",
                "region": "r1",
                "p1": "s2e1r1p1",
                "bp2": "bp2",
                "e1r1p2": "e1r1p2",
                "e1p2": "e1p2",
                "s2p2": "s2p2",
                "s2e1p2": "s2e1p2",
            },
        }
        result = _linearize_parameters(mock_base, "filestub")

        assert result == expected_result

    def test_complex4_clean(self):
        mock_base = {
            "p1": "bp1",
            "bp2": "bp2",
            "environments": {
                "e1": {
                    "p1": "e1p1",
                    "e1p2": "e1p2",
                    "regions": [
                        {
                            # None region specified.
                            "r1": None,
                        }
                    ],
                },
            },
            "services": {
                "s1": {
                    "s1p2": "s1p2",
                    "environments": {
                        "e1": {
                            "s1e1p2": "s1e1p2",
                            "regions": [
                                {
                                    "r1": {
                                        "p1": "s1e1r1p1",
                                    },
                                }
                            ],
                        },
                    },
                },
                "s2": {
                    "s2p2": "s2p2",
                    "environments": {
                        "e1": {
                            "s2e1p2": "s2e1p2",
                            "regions": [
                                {
                                    "r1": {
                                        "p1": "s2e1r1p1",
                                    },
                                }
                            ],
                        },
                    },
                },
            },
        }
        expected_result = {
            "filestub.s1.e1.r1": {
                "service": "s1",
                "environment": "e1",
                "region": "r1",
                "p1": "s1e1r1p1",
                "bp2": "bp2",
                "e1p2": "e1p2",
                "s1p2": "s1p2",
                "s1e1p2": "s1e1p2",
            },
            "filestub.s2.e1.r1": {
                "service": "s2",
                "environment": "e1",
                "region": "r1",
                "p1": "s2e1r1p1",
                "bp2": "bp2",
                "e1p2": "e1p2",
                "s2p2": "s2p2",
                "s2e1p2": "s2e1p2",
            },
        }
        result = _linearize_parameters(mock_base, "filestub")

        assert result == expected_result

    def test_complex5_clean(self):
        mock_base = {
            "p1": "bp1",
            "bp2": "bp2",
            "environments": {
                "e1": {
                    "p1": "e1p1",
                    "e1p2": "e1p2",
                    "regions": [
                        {
                            "r1": {
                                "p1": "s1e1r1p1",
                            },
                        }
                    ],
                },
            },
            "services": {
                "s1": {
                    "s1p2": "s1p2",
                    "environments": {
                        "e1": {
                            "s1e1p2": "s1e1p2",
                            "regions": [
                                {
                                    "r1": None,
                                }
                            ],
                        },
                    },
                },
                "s2": {
                    "s2p2": "s2p2",
                    "environments": {
                        "e1": {
                            "s2e1p2": "s2e1p2",
                            "regions": [
                                {
                                    "r1": {
                                        "p1": "s2e1r1p1",
                                    },
                                }
                            ],
                        },
                    },
                },
            },
        }
        expected_result = {
            "filestub.s1.e1.r1": {
                "service": "s1",
                "environment": "e1",
                "region": "r1",
                "p1": "s1e1r1p1",
                "bp2": "bp2",
                "e1p2": "e1p2",
                "s1p2": "s1p2",
                "s1e1p2": "s1e1p2",
            },
            "filestub.s2.e1.r1": {
                "service": "s2",
                "environment": "e1",
                "region": "r1",
                "p1": "s2e1r1p1",
                "bp2": "bp2",
                "e1p2": "e1p2",
                "s2p2": "s2p2",
                "s2e1p2": "s2e1p2",
            },
        }
        result = _linearize_parameters(mock_base, "filestub")

        assert result == expected_result
