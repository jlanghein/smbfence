import pytest
from pydantic import SecretStr
from smbprotocol.exceptions import SMBException

from smbfence.client import ShareClient, share_connection
from smbfence.config import ShareConfig
from smbfence.errors import (
    ConflictingContentError,
    PathNotAllowedError,
    ShareConfigError,
    ShareUnreachableError,
)
from tests.fakes import FakeBackend

BASE = r"\\fileserver\accounting"
ALLOWED = ("clients/acme",)


def client(files: dict[str, bytes] | None = None) -> tuple[ShareClient, FakeBackend]:
    backend = FakeBackend(files)
    return ShareClient(base=BASE, allowed=ALLOWED, backend=backend), backend


def test_listing_returns_matching_entries_sorted():
    sut, _ = client(
        {
            rf"{BASE}\clients\acme\b.sta": b"",
            rf"{BASE}\clients\acme\a.sta": b"",
            rf"{BASE}\clients\acme\notes.txt": b"",
        }
    )
    assert sut.list_files("clients/acme", suffix=".sta") == ["a.sta", "b.sta"]


def test_listing_skips_noise_and_excluded_prefixes():
    sut, _ = client(
        {
            rf"{BASE}\clients\acme\STA_1.sta": b"",
            rf"{BASE}\clients\acme\VMK_1.sta": b"",
            rf"{BASE}\clients\acme\.DS_Store": b"",
        }
    )
    assert sut.list_files("clients/acme", suffix=".sta", excluded_prefixes=["VMK_"]) == [
        "STA_1.sta"
    ]


def test_listing_outside_the_allowlist_is_refused():
    sut, _ = client()
    with pytest.raises(PathNotAllowedError):
        sut.list_files("clients/other")


def test_reading_returns_the_bytes():
    sut, _ = client({rf"{BASE}\clients\acme\a.sta": b"payload"})
    assert sut.read_file("clients/acme/a.sta") == b"payload"


def test_reading_outside_the_allowlist_is_refused():
    sut, _ = client()
    with pytest.raises(PathNotAllowedError):
        sut.read_file("clients/other/a.sta")


@pytest.mark.parametrize(
    "failure",
    [OSError("refused"), SMBException("negotiation"), ValueError("Failed to connect to 'x'")],
)
def test_every_backend_failure_surfaces_as_unreachable(failure: Exception):
    sut, backend = client()
    backend.fail_with = failure
    with pytest.raises(ShareUnreachableError):
        sut.list_files("clients/acme")


def test_a_write_lands_under_the_final_name():
    sut, backend = client()
    sut.write_file("clients/acme/invoice.pdf", b"whole")
    assert backend.files[rf"{BASE}\clients\acme\invoice.pdf"] == b"whole"


def test_a_write_leaves_no_partial_file_behind():
    sut, backend = client()
    sut.write_file("clients/acme/invoice.pdf", b"whole")
    assert not [name for name in backend.files if name.endswith(".partial")]


def test_rewriting_identical_bytes_is_success():
    sut, _ = client({rf"{BASE}\clients\acme\invoice.pdf": b"whole"})
    sut.write_file("clients/acme/invoice.pdf", b"whole")


def test_a_conflicting_file_is_never_overwritten():
    sut, backend = client({rf"{BASE}\clients\acme\invoice.pdf": b"someone else's"})
    with pytest.raises(ConflictingContentError):
        sut.write_file("clients/acme/invoice.pdf", b"mine")
    assert backend.files[rf"{BASE}\clients\acme\invoice.pdf"] == b"someone else's"


def test_writing_outside_the_allowlist_is_refused():
    sut, _ = client()
    with pytest.raises(PathNotAllowedError):
        sut.write_file("clients/other/invoice.pdf", b"x")


def configured(**overrides) -> ShareConfig:
    values = {
        "host": "fileserver",
        "share": "accounting",
        "user": "svc",
        "password": SecretStr("pw"),
        "allowed_paths": ALLOWED,
        "_env_file": None,
    }
    return ShareConfig(**{**values, **overrides})


def test_the_connection_is_dropped_after_use():
    backend = FakeBackend()
    with share_connection(configured(), backend):
        pass
    assert backend.resets == 1


def test_the_connection_is_dropped_even_when_the_caller_raises():
    backend = FakeBackend()
    with pytest.raises(RuntimeError), share_connection(configured(), backend):
        raise RuntimeError("caller exploded")
    assert backend.resets == 1


def test_an_unconfigured_share_is_not_attempted():
    backend = FakeBackend()
    with pytest.raises(ShareConfigError), share_connection(configured(host=""), backend):
        pass
    assert backend.sessions == []


def test_a_session_that_will_not_open_surfaces_as_unreachable():
    backend = FakeBackend()
    backend.fail_with = ValueError("Failed to connect to 'nope.invalid:445'")
    with pytest.raises(ShareUnreachableError), share_connection(configured(), backend):
        pass
