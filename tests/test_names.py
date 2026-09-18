import pytest

from smbfence.names import is_noise, matches, select


@pytest.mark.parametrize(
    "name",
    [".DS_Store", ".ds_store", "Thumbs.db", "desktop.ini", "._STA_2026.sta", ".Trashes"],
)
def test_is_noise_catches_what_both_operating_systems_leave_behind(name: str):
    assert is_noise(name)


def test_is_noise_leaves_real_files_alone():
    assert not is_noise("STA_2026.sta")


def test_matches_on_suffix():
    assert matches("export.sta", suffix=".sta")
    assert not matches("export.pdf", suffix=".sta")


def test_matches_ignores_case_on_both_sides():
    assert matches("EXPORT.STA", suffix=".sta")
    assert matches("export.sta", suffix=".STA")


def test_matches_on_prefix():
    assert matches("STA_2026.sta", prefix="sta_")
    assert not matches("VMK_2026.sta", prefix="sta_")


def test_excluded_prefix_wins_over_a_matching_suffix():
    assert not matches("VMK_2026.sta", suffix=".sta", excluded_prefixes=["vmk_"])


def test_a_suffix_only_caller_still_does_not_receive_an_excluded_file():
    assert not matches("VMK_2026.sta", suffix=".sta", excluded_prefixes=["VMK_"])


def test_noise_is_rejected_even_when_the_suffix_matches():
    assert not matches("._export.sta", suffix=".sta")


def test_select_sorts_so_listing_order_cannot_leak_through():
    listing = ["b.sta", "a.sta", "c.sta"]
    assert select(listing, suffix=".sta") == ["a.sta", "b.sta", "c.sta"]


def test_select_filters_a_realistic_hand_filed_directory():
    listing = [
        "STA_12345_20260101_120000.sta",
        "VMK_12345_20260101_120000.sta",
        "._STA_12345_20260101_120000.sta",
        ".DS_Store",
        "Thumbs.db",
        "notes.txt",
    ]
    assert select(listing, suffix=".sta", excluded_prefixes=["VMK_"]) == [
        "STA_12345_20260101_120000.sta"
    ]


def test_select_with_no_criteria_returns_everything_that_is_not_noise():
    assert select(["a.txt", ".DS_Store", "b.txt"]) == ["a.txt", "b.txt"]
