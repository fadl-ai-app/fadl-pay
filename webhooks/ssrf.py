# ============================================================
# FADL PAY — SSRF PROTECTION
# ============================================================

import ipaddress
import socket
from urllib.parse import urlparse


ALLOWED_SCHEMES = {"http", "https"}

BLOCKED_HOSTNAMES = {
    "localhost",
    "localhost.localdomain",
    "ip6-localhost",
    "ip6-loopback",
    "metadata.google.internal",
    "metadata",
}

BLOCKED_IPS = {
    "0.0.0.0",
    "127.0.0.1",
    "::",
    "::1",
    "169.254.169.254",
}


def _is_blocked_ip(ip):
    try:
        address = ipaddress.ip_address(ip)

        # Covers:
        # loopback
        # private networks
        # link-local
        # multicast
        # unspecified
        # reserved
        # benchmarking
        # IPv4-mapped IPv6
        if address.is_loopback:
            return True

        if address.is_private:
            return True

        if address.is_link_local:
            return True

        if address.is_multicast:
            return True

        if address.is_unspecified:
            return True

        if address.is_reserved:
            return True

        if address.is_global is False:
            return True

        return False

    except ValueError:
        return True


def _resolve_and_validate_host(hostname):
    hostname = hostname.strip().lower().rstrip(".")

    if not hostname:
        raise ValueError("Webhook hostname is required")

    if hostname in BLOCKED_HOSTNAMES:
        raise ValueError(
            "Webhook hostname is not allowed"
        )

    # Reject obvious local/internal hostname forms.
    if (
        hostname.endswith(".local")
        or hostname.endswith(".localhost")
        or hostname.endswith(".internal")
    ):
        raise ValueError(
            "Internal webhook hostname is not allowed"
        )

    # Direct IP address supplied as hostname.
    try:
        address = ipaddress.ip_address(hostname)

        if _is_blocked_ip(str(address)):
            raise ValueError(
                "Webhook IP address is not allowed"
            )

        return [str(address)]

    except ValueError:
        # Not an IP literal; continue with DNS resolution.
        pass

    try:
        results = socket.getaddrinfo(
            hostname,
            None,
            socket.AF_UNSPEC,
            socket.SOCK_STREAM,
        )
    except socket.gaierror as error:
        raise ValueError(
            "Webhook hostname could not be resolved"
        ) from error

    resolved_ips = []

    for result in results:
        sockaddr = result[4]
        ip = sockaddr[0]

        if _is_blocked_ip(ip):
            raise ValueError(
                "Webhook hostname resolves to a blocked IP address"
            )

        resolved_ips.append(ip)

    if not resolved_ips:
        raise ValueError(
            "Webhook hostname has no usable IP address"
        )

    return sorted(set(resolved_ips))


def validate_webhook_url(webhook_url):
    if not isinstance(webhook_url, str):
        raise ValueError(
            "Webhook URL must be a string"
        )

    webhook_url = webhook_url.strip()

    if not webhook_url:
        raise ValueError(
            "Webhook URL is required"
        )

    parsed = urlparse(webhook_url)

    if parsed.scheme.lower() not in ALLOWED_SCHEMES:
        raise ValueError(
            "Webhook URL must use HTTP or HTTPS"
        )

    if not parsed.hostname:
        raise ValueError(
            "Invalid Webhook URL"
        )

    # Userinfo in URLs can hide or confuse the real destination.
    if parsed.username is not None or parsed.password is not None:
        raise ValueError(
            "Webhook URL must not contain username or password"
        )

    # Fragments are never sent to the server and are unnecessary.
    if parsed.fragment:
        raise ValueError(
            "Webhook URL must not contain a fragment"
        )

    hostname = parsed.hostname.lower().rstrip(".")

    _resolve_and_validate_host(hostname)

    return True
