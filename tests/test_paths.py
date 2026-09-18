from smbfence.paths import is_within, normalise, to_windows, unc


def test_normalise_accepts_either_separator():
    assert normalise(r"clients\acme\bank") == "clients/acme/bank"
    assert normalise("clients/acme/bank") == "clients/acme/bank"


def test_normalise_strips_surrounding_separators():
    assert normalise(r"\clients\acme\\") == "clients/acme"
    assert normalise("/clients/acme/") == "clients/acme"


def test_to_windows_round_trips():
    assert to_windows("clients/acme") == r"clients\acme"
    assert to_windows(r"\clients\acme\\") == r"clients\acme"


def test_unc_builds_the_prefix():
    assert unc("fileserver", "accounting") == r"\\fileserver\accounting"


def test_is_within_matches_the_root_itself():
    assert is_within("clients/acme", ["clients/acme"])


def test_is_within_matches_below_the_root():
    assert is_within("clients/acme/bank/2026", ["clients/acme"])


def test_is_within_ignores_separator_spelling():
    assert is_within(r"\clients\acme\bank", ["clients/acme"])


def test_is_within_rejects_a_sibling_the_root_merely_prefixes():
    assert not is_within("clients/acme-holdings", ["clients/acme"])


def test_is_within_rejects_a_path_outside_every_root():
    assert not is_within("clients/other", ["clients/acme", "clients/beta"])


def test_is_within_rejects_everything_when_no_root_is_allowed():
    assert not is_within("clients/acme", [])
