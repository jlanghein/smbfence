import pytest
from pydantic import SecretStr

from smbfence.config import ShareConfig
from smbfence.errors import ShareConfigError


def complete(**overrides) -> ShareConfig:
    values = {
        "host": "fileserver",
        "share": "accounting",
        "user": "svc",
        "password": SecretStr("hunter2"),
        "_env_file": None,
    }
    return ShareConfig(**{**values, **overrides})


def test_a_complete_config_is_configured():
    assert complete().is_configured


@pytest.mark.parametrize("missing", ["host", "share", "user"])
def test_any_missing_field_leaves_it_unconfigured(missing: str):
    assert not complete(**{missing: ""}).is_configured


def test_an_empty_password_leaves_it_unconfigured():
    assert not complete(password=SecretStr("")).is_configured


def test_require_passes_when_complete():
    complete().require()


def test_require_raises_when_incomplete():
    with pytest.raises(ShareConfigError):
        complete(host="").require()


def test_the_password_does_not_appear_in_the_repr():
    assert "hunter2" not in repr(complete())


def test_the_default_port_is_the_smb_port():
    assert complete().port == 445
