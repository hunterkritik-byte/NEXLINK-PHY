import numpy as np
import pytest

from nexlink_channel import apply_channel, run_sweep
from nexlink_phy import decode_frame, encode_frame


def test_channel_without_impairments_preserves_frame_with_offset():
    payload = b"real-world step"
    received = apply_channel(encode_frame(payload), sample_offset=17, gain=0.5)
    assert decode_frame(received) == payload


@pytest.mark.parametrize("cfo_hz", [1000.0, 2000.0, -2000.0])
def test_receiver_handles_carrier_frequency_offset(cfo_hz):
    payload = b"frequency offset regression"
    received = apply_channel(
        encode_frame(payload),
        cfo_hz=cfo_hz,
        sample_offset=17,
        rng=np.random.default_rng(2026),
    )
    assert decode_frame(received) == payload


def test_channel_noise_is_reproducible_with_seeded_rng():
    iq = encode_frame(b"repeatable")
    a = apply_channel(iq, snr_db=20, rng=np.random.default_rng(7))
    b = apply_channel(iq, snr_db=20, rng=np.random.default_rng(7))
    np.testing.assert_array_equal(a, b)


def test_channel_rejects_invalid_parameters():
    with pytest.raises(ValueError):
        apply_channel(np.ones(8, dtype=np.complex64), sample_offset=-1)
    with pytest.raises(ValueError):
        apply_channel(np.ones(8, dtype=np.complex64), gain=-1)


def test_high_snr_sweep_decodes_reproducibly():
    result = run_sweep(b"NEXLINK", [40.0], packets=3, seed=123)
    assert result == [(40.0, 3, 3)]
