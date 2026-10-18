import numpy as np
import pytest

from nexlink_phy import (
    SAMPLES_PER_SYMBOL,
    crc16_ccitt,
    decode_frame,
    encode_frame,
    frame_bits,
    modulate,
)


def test_crc16_ccitt_known_vector():
    assert crc16_ccitt(b"123456789") == 0x29B1


@pytest.mark.parametrize("payload", [b"", b"hello", bytes(range(256)), "NEXLINK PHY".encode()])
def test_frame_codec_round_trip(payload):
    assert decode_frame(encode_frame(payload)) == payload


def test_receiver_handles_leading_sample_offset():
    payload = b"offset test"
    captured = np.concatenate(
        [np.zeros(17, dtype=np.complex64), encode_frame(payload)]
    )
    assert decode_frame(captured) == payload


def test_receiver_rejects_corrupted_frame():
    iq = encode_frame(b"integrity check")
    # Flip a chunk of samples in a payload symbol; CRC should reject the frame.
    symbol_index = (24 + 16 + 16 + 8)  # preamble + sync + length + first payload byte
    start = symbol_index * SAMPLES_PER_SYMBOL
    iq[start:start + SAMPLES_PER_SYMBOL] *= -1
    with pytest.raises(ValueError):
        decode_frame(iq)


def test_modulator_rejects_invalid_bits():
    with pytest.raises(ValueError):
        modulate([0, 1, 2])


def test_frame_rejects_oversize_payload():
    with pytest.raises(ValueError):
        frame_bits(b"x" * 4097)
