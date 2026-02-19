import pytest

from app.utils.ssrf import validate_external_url


@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1/test",
        "http://localhost/test",
        "http://10.0.0.1/test",
        "http://192.168.1.1/test",
        "ftp://example.com/file",
    ],
)
def test_ssrf_blocking(url: str) -> None:
    with pytest.raises(ValueError):
        validate_external_url(url)
