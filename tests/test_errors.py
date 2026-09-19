import pytest
from smbprotocol.exceptions import SMBException

from smbfence.errors import (
    ConflictingContentError,
    PathNotAllowedError,
    ShareConfigError,
    ShareError,
    ShareUnreachableError,
    translated,
)


@pytest.mark.parametrize(
    "error",
    [ShareConfigError, PathNotAllowedError, ShareUnreachableError, ConflictingContentError],
)
def test_every_error_is_catchable_as_the_base(error: type[ShareError]):
    with pytest.raises(ShareError):
        raise error("boom")


@pytest.mark.parametrize(
    "raised",
    [
        OSError("connection refused"),
        SMBException("negotiation failed"),
        ValueError("Failed to connect to 'nope.invalid:445'"),
    ],
)
def test_every_smb_failure_mode_becomes_one_error(raised: Exception):
    with pytest.raises(ShareUnreachableError), translated("listing"):
        raise raised


def test_the_original_cause_is_preserved():
    with pytest.raises(ShareUnreachableError) as caught, translated("listing"):
        raise OSError("connection refused")
    assert isinstance(caught.value.__cause__, OSError)


def test_the_context_names_what_was_attempted():
    with pytest.raises(ShareUnreachableError, match="listing"), translated("listing"):
        raise OSError("boom")
