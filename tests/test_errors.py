import pytest

from smbfence.errors import (
    ConflictingContentError,
    PathNotAllowedError,
    ShareConfigError,
    ShareError,
    ShareUnreachableError,
)


@pytest.mark.parametrize(
    "error",
    [ShareConfigError, PathNotAllowedError, ShareUnreachableError, ConflictingContentError],
)
def test_every_error_is_catchable_as_the_base(error: type[ShareError]):
    with pytest.raises(ShareError):
        raise error("boom")
