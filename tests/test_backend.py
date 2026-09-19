"""The real backend must satisfy the Protocol the client depends on.

`smbclient` spreads its functions across two namespaces — `listdir` and
`open_file` on the module, `exists` on `smbclient.path` — so a backend that
looks complete can still fail on the first call that needs the other one. An
in-memory fake cannot catch that, because the fake is complete by construction.
"""

from smbfence.backend import SmbClientBackend
from smbfence.client import SmbBackend
from tests.fakes import FakeBackend


def test_the_real_backend_satisfies_the_protocol():
    assert isinstance(SmbClientBackend(), SmbBackend)


def test_the_fake_satisfies_the_same_protocol():
    assert isinstance(FakeBackend(), SmbBackend)


def test_every_protocol_method_resolves_on_the_real_backend():
    backend = SmbClientBackend()
    for name in SmbBackend.__protocol_attrs__:
        assert callable(getattr(backend, name)), f"{name} is not callable on the real backend"
