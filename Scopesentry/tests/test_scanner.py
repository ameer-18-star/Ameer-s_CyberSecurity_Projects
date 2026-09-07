"""Tests for parse_airodump_csv / _normalize_encryption — pure parsing logic,
exercised with fixture text instead of real hardware."""

from core.scanner import _normalize_encryption, parse_airodump_csv

AP_HEADER = (
    "BSSID, First time seen, Last time seen, channel, Speed, Privacy, Cipher, "
    "Authentication, Power, # beacons, # IV, LAN IP, ID-length, ESSID, Key\n"
)
CLIENT_HEADER = (
    "Station MAC, First time seen, Last time seen, Power, # packets, BSSID, Probed ESSIDs\n"
)


def _csv(ap_rows: list[str], client_rows: list[str] | None = None) -> str:
    text = AP_HEADER + "".join(r + "\n" for r in ap_rows)
    if client_rows is not None:
        text += "\n" + CLIENT_HEADER + "".join(r + "\n" for r in client_rows)
    return text


# ---- _normalize_encryption --------------------------------------------------

def test_plain_wpa2_psk():
    assert _normalize_encryption("WPA2", "PSK") == "WPA2"


def test_wpa2_with_sae_is_actually_wpa3():
    assert _normalize_encryption("WPA2", "SAE") == "WPA3"


def test_explicit_wpa3():
    assert _normalize_encryption("WPA3", "SAE") == "WPA3"


def test_wep():
    assert _normalize_encryption("WEP", "") == "WEP"


def test_legacy_wpa():
    assert _normalize_encryption("WPA", "PSK") == "WPA"


def test_open_network_blank():
    assert _normalize_encryption("", "") == "OPN"


def test_open_network_explicit():
    assert _normalize_encryption("OPN", "") == "OPN"


def test_unrecognized_string_passed_through():
    assert _normalize_encryption("SOME-FUTURE-PROTOCOL", "") == "SOME-FUTURE-PROTOCOL"


def test_case_insensitive():
    assert _normalize_encryption("wpa2", "sae") == "WPA3"


# ---- parse_airodump_csv ------------------------------------------------------

def test_parses_single_ap_no_clients():
    content = _csv([
        "AA:BB:CC:11:22:33, 2026-06-24 09:00, 2026-06-24 09:05, 6, 54, WPA2, CCMP, PSK, -45, 10, 0, 0.0.0.0, 14, Acme-Corp-WiFi,",
    ])
    aps = parse_airodump_csv(content)
    assert len(aps) == 1
    ap = aps[0]
    assert ap.bssid == "AA:BB:CC:11:22:33"
    assert ap.essid == "Acme-Corp-WiFi"
    assert ap.channel == "6"
    assert ap.encryption == "WPA2"
    assert ap.signal == -45
    assert ap.clients == 0


def test_hidden_essid_labeled():
    content = _csv([
        "AA:BB:CC:11:22:33, t, t, 6, 54, WPA2, CCMP, PSK, -45, 10, 0, 0.0.0.0, 0, ,",
    ])
    aps = parse_airodump_csv(content)
    assert aps[0].essid == "(hidden)"


def test_client_count_attributed_to_correct_bssid():
    content = _csv(
        ap_rows=[
            "AA:BB:CC:11:22:33, t, t, 6, 54, WPA2, CCMP, PSK, -45, 10, 0, 0.0.0.0, 14, Acme-Corp-WiFi,",
            "AA:BB:CC:44:55:66, t, t, 1, 54, OPN, , , -60, 5, 0, 0.0.0.0, 11, Acme-Guest,",
        ],
        client_rows=[
            "11:11:11:11:11:11, t, t, -50, 100, AA:BB:CC:11:22:33, ",
            "22:22:22:22:22:22, t, t, -55, 50, AA:BB:CC:11:22:33, ",
            "33:33:33:33:33:33, t, t, -70, 20, AA:BB:CC:44:55:66, ",
        ],
    )
    aps = {ap.bssid: ap for ap in parse_airodump_csv(content)}
    assert aps["AA:BB:CC:11:22:33"].clients == 2
    assert aps["AA:BB:CC:44:55:66"].clients == 1


def test_unassociated_clients_not_counted():
    content = _csv(
        ap_rows=[
            "AA:BB:CC:11:22:33, t, t, 6, 54, WPA2, CCMP, PSK, -45, 10, 0, 0.0.0.0, 14, Acme-Corp-WiFi,",
        ],
        client_rows=[
            "11:11:11:11:11:11, t, t, -50, 100, (not associated), SomeProbedSSID",
        ],
    )
    aps = parse_airodump_csv(content)
    assert aps[0].clients == 0


def test_malformed_short_row_skipped():
    content = AP_HEADER + "AA:BB:CC:11:22:33, too, short\n"
    assert parse_airodump_csv(content) == []


def test_empty_content():
    assert parse_airodump_csv("") == []


def test_wpa3_transition_network_normalized():
    content = _csv([
        "AA:BB:CC:11:22:33, t, t, 6, 54, WPA2, CCMP, SAE, -45, 10, 0, 0.0.0.0, 14, Acme-Corp-WiFi,",
    ])
    aps = parse_airodump_csv(content)
    assert aps[0].encryption == "WPA3"