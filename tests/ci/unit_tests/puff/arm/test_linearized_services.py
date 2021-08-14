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
                "service": "s1",
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
                "service": "s1",
                "p1": "bp1",
                "p2": "s1p2",
            },
            "some-file.s2": {
                "service": "s2",
                "p1": "bp1",
                "p2": "s2p2",
            },
        }
        result = _linearize_services(mock_base)

        assert result == expected_result

    def test_services_environments2(self):
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
                "service": "s1",
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
                "service": "s1",
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
                "service": "s1",
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
                "service": "s1",
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

    def test_complex1_clean(self):
        mock_base = {
            "filestub": {
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
                                    },
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
                                    },
                                ],
                            },
                        },
                    },
                },
            },
        }
        expected_result = {
            "filestub.s1": {
                "service": "s1",
                "environments": {
                    "e1": {
                        "p1": "e1p1",
                        "e1p2": "e1p2",
                        "s1e1p2": "s1e1p2",
                        "regions": [
                            {"r1": {"e1r1p2": "e1r1p2"}},
                            {"r1": {"p1": "s1e1r1p1"}},
                        ],
                    },
                },
                "p1": "bp1",
                "bp2": "bp2",
                "s1p2": "s1p2",
            },
            "filestub.s2": {
                "service": "s2",
                "environments": {
                    "e1": {
                        "p1": "e1p1",
                        "e1p2": "e1p2",
                        "s2e1p2": "s2e1p2",
                        "regions": [
                            {"r1": {"e1r1p2": "e1r1p2"}},
                            {
                                "r1": {
                                    "p1": "s2e1r1p1",
                                },
                            },
                        ],
                    },
                },
                "p1": "bp1",
                "bp2": "bp2",
                "s2p2": "s2p2",
            },
        }
        result = _linearize_services(mock_base)

        assert result == expected_result
