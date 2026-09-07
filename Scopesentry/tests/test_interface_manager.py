from core.interface_manager import parse_iw_dev

SAMPLE_OUTPUT = """\
phy#0
        Interface wlan0
                ifindex 3
                wdev 0x1
                addr aa:bb:cc:dd:ee:ff
                type managed
phy#1
        Interface wlan1mon
                ifindex 4
                wdev 0x2
                addr 11:22:33:44:55:66
                type monitor
"""


def test_parses_multiple_interfaces():
    assert parse_iw_dev(SAMPLE_OUTPUT) == ["wlan0", "wlan1mon"]


def test_empty_output():
    assert parse_iw_dev("") == []


def test_no_interfaces_present():
    assert parse_iw_dev("phy#0\n    something else\n") == []


def test_single_interface():
    assert parse_iw_dev("phy#0\n\tInterface wlan0\n\t\ttype managed\n") == ["wlan0"]