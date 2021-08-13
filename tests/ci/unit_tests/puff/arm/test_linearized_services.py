#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.


from foodx_devops_tools.puff.arm import _linearize_services


class TestLinearizedServices:
    def test_services_environments(self):
        mock_base = {
            "some-file": {
                "p1": "bp1",
                "p2": "bp2",
                "environments": {
                    "e1": {
                        "k1": "be1k1",
                        "k2": "be1k2",
                    },
                },
                "services": {
                    "s1": {
                        "p2": "s1p2",
                        "environments": {
                            "e1": {
                                "k1": "s1e1k1",
                            },
                        },
                    },
                },
            },
        }
        expected_result = {
            "some-file.s1": {
                "p1": "bp1",
                "p2": "s1p2",
                "environments": {
                    "e1": {
                        "k1": "s1e1k1",
                        "k2": "be1k2",
                    },
                },
            },
        }
        result = _linearize_services(mock_base)

        assert result == expected_result

    def test_multiple_services(self):
        mock_base = {
            "some-file": {
                "p1": "bp1",
                "p2": "bp2",
                "services": {
                    "s1": {
                        "p2": "s1p2",
                    },
                    "s2": {
                        "p2": "s2p2",
                    },
                },
            },
        }
        expected_result = {
            "some-file.s1": {
                "p1": "bp1",
                "p2": "s1p2",
            },
            "some-file.s2": {
                "p1": "bp1",
                "p2": "s2p2",
            },
        }
        result = _linearize_services(mock_base)

        assert result == expected_result

    def test_services_environments(self):
        mock_base = {
            "some-file": {
                "p1": "bp1",
                "p2": "bp2",
                "environments": {
                    "e1": {
                        "k1": "be1k1",
                        "k2": "be1k2",
                    },
                },
                "services": {
                    "s1": {
                        "p2": "s1p2",
                        "environments": {
                            "e1": {
                                "k1": "s1e1k1",
                            },
                        },
                    },
                },
            },
        }
        expected_result = {
            "some-file.s1": {
                "p1": "bp1",
                "p2": "s1p2",
                "environments": {
                    "e1": {
                        "k1": "s1e1k1",
                        "k2": "be1k2",
                    },
                },
            },
        }
        result = _linearize_services(mock_base)

        assert result == expected_result

    def test_empty_services(self):
        mock_base = {
            "some-file": {
                "p1": "bp1",
                "p2": "bp2",
                "environments": {
                    "e1": {
                        "k1": "be1k1",
                        "k2": "be1k2",
                    },
                },
                "services": dict(),
            },
        }
        expected_result = {
            "some-file": {
                "p1": "bp1",
                "p2": "bp2",
                "environments": {
                    "e1": {
                        "k1": "be1k1",
                        "k2": "be1k2",
                    },
                },
            },
        }
        result = _linearize_services(mock_base)

        assert result == expected_result

    def test_empty_service(self):
        mock_base = {
            "some-file": {
                "p1": "bp1",
                "p2": "bp2",
                "services": {
                    "s1": dict(),
                },
            },
        }
        expected_result = {
            "some-file.s1": {
                "p1": "bp1",
                "p2": "bp2",
            },
        }
        result = _linearize_services(mock_base)

        assert result == expected_result

    def test_none_service(self):
        mock_base = {
            "some-file": {
                "p1": "bp1",
                "p2": "bp2",
                "services": {
                    "s1": None,
                },
            },
        }
        expected_result = {
            "some-file.s1": {
                "p1": "bp1",
                "p2": "bp2",
            },
        }
        result = _linearize_services(mock_base)

        assert result == expected_result

    def test_no_services_no_environments(self):
        mock_base = {
            "some-file": {
                "p1": "bp1",
                "p2": "bp2",
                "services": dict(),
            },
        }
        expected_result = {
            "some-file": {
                "p1": "bp1",
                "p2": "bp2",
            },
        }
        result = _linearize_services(mock_base)

        assert result == expected_result

    def test_no_services_no_environments_empty_base(self):
        mock_base = {
            "some-file": dict(),
        }
        expected_result = mock_base
        result = _linearize_services(mock_base)

        assert result == expected_result

    def test_services_empty_base(self):
        mock_base = {
            "some-file": {
                "services": {
                    "s1": {
                        "p2": "s1p2",
                        "environments": {
                            "e1": {
                                "k1": "s1e1k1",
                            },
                        },
                    },
                },
            },
        }
        expected_result = {
            "some-file.s1": {
                "p2": "s1p2",
                "environments": {
                    "e1": {
                        "k1": "s1e1k1",
                    },
                },
            },
        }
        result = _linearize_services(mock_base)

        assert result == expected_result
