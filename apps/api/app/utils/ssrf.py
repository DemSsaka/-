import ipaddress
import socket
from urllib.parse import urlparse


BLOCKED_HOSTS = {"localhost", "127.0.0.1", "::1", "0.0.0.0"}


def _is_blocked_ip(ip_str: str) -> bool:
    ip = ipaddress.ip_address(ip_str)
    return (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    )


def validate_external_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("Only http/https URLs are allowed")

    if not parsed.hostname:
        raise ValueError("Invalid URL hostname")

    hostname = parsed.hostname.lower()
    if hostname in BLOCKED_HOSTS or hostname.endswith(".local"):
        raise ValueError("Local/internal hosts are not allowed")

    if parsed.port and parsed.port not in {80, 443}:
        raise ValueError("Only ports 80/443 are allowed")

    try:
        infos = socket.getaddrinfo(hostname, parsed.port or 80, proto=socket.IPPROTO_TCP)
    except socket.gaierror as exc:
        raise ValueError("Unable to resolve host") from exc

    for info in infos:
        ip_str = info[4][0]
        if _is_blocked_ip(ip_str):
            raise ValueError("Resolved IP is private/internal and blocked")
