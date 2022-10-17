from ipaddress import IPv4Address, IPv4Network

import pytest

from aiogram.webhook.security import IPFilter


class TestSecurity:
    def test_empty_init(self):
        ip_filter = IPFilter()
        assert not ip_filter._allowed_ips

    @pytest.mark.parametrize(
        "ip,result",
        [
            ("127.0.0.1", True),
            ("127.0.0.2", False),
            (IPv4Address("127.0.0.1"), True),
            (IPv4Address("127.0.0.2"), False),
            (IPv4Address("192.168.0.32"), True),
            ("192.168.0.33", False),
            ("10.111.0.5", True),
            ("10.111.0.100", True),
            ("10.111.1.100", False),
        ],
    )
    def test_check_ip(self, ip, result):
        ip_filter = IPFilter(
            ips=["127.0.0.1", IPv4Address("192.168.0.32"), IPv4Network("10.111.0.0/24")]
        )
        assert (ip in ip_filter) is result

    def test_default(self):
        ip_filter = IPFilter.default()
        assert isinstance(ip_filter, IPFilter)
        assert len(ip_filter._allowed_ips) == 5116
        assert "91.108.4.50" in ip_filter
        assert "149.154.160.20" in ip_filter
        assert "91.108.6.79" in ip_filter

    @pytest.mark.parametrize(
        "ip,ip_range",
        [
            ["127.0.0.1", {IPv4Address("127.0.0.1")}],
            ["91.108.4.0/22", set(IPv4Network("91.108.4.0/22").hosts())],
            [IPv4Address("91.108.4.5"), {IPv4Address("91.108.4.5")}],
            [IPv4Network("91.108.4.0/22"), set(IPv4Network("91.108.4.0/22").hosts())],
            [42, set()],
        ],
    )
    def test_allow_ip(self, ip, ip_range):
        ip_filter = IPFilter()
        if not ip_range:
            with pytest.raises(ValueError):
                ip_filter.allow_ip(ip)
        else:
            ip_filter.allow_ip(ip)
            assert ip_filter._allowed_ips == ip_range
