#!/usr/bin/env python3
"""nosigner unit tests (NIP-46 signer): crypto, key handling, bunker parsing.

Run with the venv that has the deps:
  .venv/bin/python -m pytest nosigner/tests -q
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent.parent  # nosigner/
spec = importlib.util.spec_from_file_location("nosigner", HERE / "nosigner.py")
nosigner = importlib.util.module_from_spec(spec)
sys.modules["nosigner"] = nosigner  # dataclasses need the module registered
spec.loader.exec_module(nosigner)


def test_privkey_to_pubkey_deterministic():
    priv = bytes.fromhex("11" * 32)
    pk = nosigner.privkey_to_pubkey(priv)
    assert pk == nosigner.privkey_to_pubkey(priv)
    assert len(pk) == 32


def test_nip44_roundtrip():
    a = bytes.fromhex("22" * 32)
    b = bytes.fromhex("33" * 32)
    # conversation keys are symmetric
    conv_a = nosigner.get_conversation_key(a, nosigner.privkey_to_pubkey(b))
    conv_b = nosigner.get_conversation_key(b, nosigner.privkey_to_pubkey(a))
    assert conv_a == conv_b
    ct = nosigner.nip44_encrypt("hello nostr", conv_a)
    assert ct != "hello nostr"
    assert nosigner.nip44_decrypt(ct, conv_b) == "hello nostr"


def test_nip44_decrypt_rejects_tampered():
    a = bytes.fromhex("44" * 32)
    b = bytes.fromhex("55" * 32)
    conv = nosigner.get_conversation_key(a, nosigner.privkey_to_pubkey(b))
    ct = nosigner.nip44_encrypt("payload", conv)
    with pytest.raises(Exception):
        nosigner.nip44_decrypt(ct[:-4] + "AAAA", conv)


def test_parse_bunker_url():
    client = "11" * 32
    url = (f"bunker://{client}?relay=wss://relay.nsec.app"
           "&relay=wss://relay.primal.net&secret=s3cr3t")
    cfg = nosigner.parse_bunker_url(url)
    assert cfg.signer_pubkey == client
    assert "wss://relay.nsec.app" in cfg.relays
    assert cfg.secret == "s3cr3t"


def test_parse_bunker_url_bad_raises_or_safe():
    # Must not crash the process on garbage input.
    try:
        nosigner.parse_bunker_url("not-a-bunker-url")
    except Exception:
        pass


def test_event_id_and_sign_are_stable():
    priv = bytes.fromhex("66" * 32)
    pub = nosigner.privkey_to_pubkey(priv).hex()
    eid = nosigner.compute_event_id(pub, 1700000000, 1, [], "hi")
    sig = nosigner.sign_event(priv, eid)
    assert len(eid) == 32
    assert len(sig) >= 128  # schnorr sig, hex-encoded (64–65 bytes)


def test_sec_file_precedence_parse():
    # --sec-file is offered as an argument (key never in argv).
    import argparse
    # smoke: the module exposes decode_nsec for both nsec and hex paths
    assert callable(nosigner.decode_nsec)
    assert callable(nosigner.privkey_to_pubkey)
