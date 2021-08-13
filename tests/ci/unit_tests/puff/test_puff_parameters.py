#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

import pydantic
import pytest

from foodx_devops_tools.puff._puff_parameters import (
    PuffEnvironment,
    PuffEnvironments,
    PuffParameterModel,
    PuffRegion,
    PuffRegions,
    PuffService,
    PuffServices,
)


class TestPuffRegion:
    def test_clean(self):
        under_test = PuffRegion.parse_obj(
            {
                "r1": {"n1": "v1", "n2": "v2"},
            }
        )

        assert under_test["r1"] == {"n1": "v1", "n2": "v2"}
        assert "r1" in under_test

    def test_multiple_names_raises(self):
        with pytest.raises(
            pydantic.ValidationError,
            match=r"must only specify a single name in a region entry",
        ):
            PuffRegion.parse_obj(
                {
                    "r1": {"n1": "v1", "n2": "v2"},
                    "r2": {"n2": "v3"},
                }
            )


class TestPuffRegions:
    def test_clean(self):
        under_test = PuffRegions.parse_obj(
            [
                {
                    "r1": {"n1": "v1", "n2": "v2"},
                },
                {
                    "r2": {"n2": "v3"},
                },
            ]
        )

        assert under_test[0]["r1"] == {"n1": "v1", "n2": "v2"}
        assert under_test[1]["r2"] == {"n2": "v3"}

    def test_empty_region(self):
        under_test = PuffRegions.parse_obj(
            [
                {
                    "r1": {},
                },
                {
                    "r2": {"n2": "v3"},
                },
            ]
        )

        assert "r1" in under_test[0]
        assert under_test[1]["r2"] == {"n2": "v3"}

    def test_none_region(self):
        under_test = PuffRegions.parse_obj(
            [
                {
                    "r1": None,
                },
                {
                    "r2": {"n2": "v3"},
                },
            ]
        )

        assert "r1" in under_test[0]
        assert under_test[1]["r2"] == {"n2": "v3"}

    def test_multiple_names_raises(self):
        with pytest.raises(
            pydantic.ValidationError,
            match=r"must only specify a single name in a region entry",
        ):
            PuffRegions.parse_obj(
                [
                    {
                        "r1": {"n1": "v1", "n2": "v2"},
                    },
                    {
                        "r1": {"n1": "v1", "n2": "v2"},
                        "r2": {"n2": "v3"},
                    },
                ]
            )


class TestPuffEnvironment:
    def test_clean_regions_present(self):
        under_test = PuffEnvironment.parse_obj(
            {
                "n1": "v1",
                "regions": [
                    {
                        "r1": {
                            "n2": "v2",
                        },
                    },
                ],
            }
        )
        assert under_test["n1"] == "v1"
        assert under_test["regions"][0]["r1"]["n2"] == "v2"
        assert "n1" in under_test

    def test_clean_regions_absent(self):
        under_test = PuffEnvironment.parse_obj(
            {
                "n1": "v1",
            }
        )
        assert under_test["n1"] == "v1"
        assert "regions" not in under_test

    def test_bad_regions_raises(self):
        with pytest.raises(pydantic.ValidationError):
            PuffEnvironment.parse_obj(
                {
                    "n1": "v1",
                    # regions is not a list
                    "regions": {
                        "n2": "v2",
                    },
                }
            )


class TestPuffEnvironments:
    def test_clean(self):
        under_test = PuffEnvironments.parse_obj(
            {
                "e1": {
                    "n1": "v1",
                    "regions": [
                        {
                            "r1": {
                                "n2": "v2",
                            },
                        }
                    ],
                },
                "e2": {
                    "regions": [
                        {
                            "r1": {
                                "n2": "v3",
                            },
                        }
                    ]
                },
            }
        )

        assert under_test["e1"]["n1"] == "v1"
        assert "n1" not in under_test["e2"]
        assert "e1" in under_test

    def test_empty_environment(self):
        under_test = PuffEnvironments.parse_obj(
            {
                "e1": dict(),
                "e2": {
                    "regions": [
                        {
                            "r1": {
                                "n2": "v3",
                            },
                        }
                    ]
                },
            }
        )

        assert "n1" not in under_test["e2"]
        assert "e1" in under_test

    def test_none_environment(self):
        under_test = PuffEnvironments.parse_obj(
            {
                "e1": None,
                "e2": {
                    "regions": [
                        {
                            "r1": {
                                "n2": "v3",
                            },
                        }
                    ]
                },
            }
        )

        assert "n1" not in under_test["e2"]
        assert "e1" in under_test


class TestPuffService:
    def test_clean(self):
        under_test = PuffService.parse_obj(
            {
                "n1": "v1",
                "environments": {
                    "e1": {
                        "n1": "v2",
                        "regions": {
                            "n2": "v3",
                        },
                    },
                },
            }
        )

        assert under_test["n1"] == "v1"
        assert under_test["environments"]["e1"]["n1"] == "v2"
        assert "environments" in under_test


class TestPuffServices:
    def test_clean(self):
        under_test = PuffServices.parse_obj(
            {
                "s1": {
                    "n1": "v1",
                    "environments": {
                        "e1": {
                            "n1": "v3",
                            "regions": {
                                "n2": "v2",
                            },
                        },
                    },
                },
                "s2": {
                    "n1": "v5",
                    "environments": {
                        "e2": {
                            "regions": {
                                "n2": "v3",
                            },
                        },
                    },
                },
            }
        )

        assert under_test["s1"]["n1"] == "v1"
        assert under_test["s2"]["n1"] == "v5"
        assert "s1" in under_test


class TestPuffParameterModel:
    def test_clean(self):
        under_test = PuffParameterModel.parse_obj(
            {
                "name": "some-name",
                "k1": "v1",
                "environments": {
                    "e1": {
                        "n1": "v1",
                        "regions": [
                            {
                                "r1": {
                                    "n2": "v2",
                                },
                            }
                        ],
                    },
                    "e2": {
                        "regions": [
                            {
                                "r1": {
                                    "n2": "v3",
                                },
                            }
                        ]
                    },
                },
                "services": {
                    "s1": {
                        "n1": "v1",
                        "environments": {
                            "e1": {
                                "n1": "v3",
                                "regions": [
                                    {
                                        "r1": {
                                            "n2": "v2",
                                        },
                                    }
                                ],
                            },
                        },
                    },
                    "s2": {
                        "n1": "v5",
                        "environments": {
                            "e2": {
                                "regions": [
                                    {
                                        "r1": {
                                            "n2": "v3",
                                        },
                                    }
                                ],
                            },
                        },
                    },
                },
            },
        )

    def test_empty_environments(self):
        under_test = PuffParameterModel.parse_obj(
            {
                "name": "some-name",
                "environments": dict(),
            },
        )

        assert "environments" in under_test
