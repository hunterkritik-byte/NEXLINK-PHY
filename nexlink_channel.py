#!/usr/bin/env python3
"""NEXLINK-PHY baseband channel simulator (no RF hardware or transmission)."""
from __future__ import annotations

import argparse
import math

import numpy as np

from nexlink_phy import SAMPLE_RATE, decode_frame, encode_frame


def apply_channel(
    iq: np.ndarray,
    *,
    snr_db: float = math.inf,
    cfo_hz: float = 0.0,
    sample_offset: int = 0,
    gain: float = 1.0,
    rng: np.random.Generator | None = None,
) -> np.ndarray:
    """Apply a simple deterministic impairment model to complex64 baseband IQ.

    SNR is measured against the input signal power. CFO is carrier-frequency
    offset in Hz; sample_offset prepends zero-valued samples; gain scales IQ.
    This is a basic lab model, not a full fading, multipath, or RF model.
    """
    samples = np.asarray(iq, dtype=np.complex64).reshape(-1)
    if sample_offset < 0:
        raise ValueError("sample_offset must be >= 0")
    if not math.isinf(snr_db) and not math.isfinite(snr_db):
        raise ValueError("snr_db must be finite or positive infinity")
    if math.isinf(snr_db) and snr_db < 0:
        raise ValueError("snr_db must be finite or positive infinity")
    if not math.isfinite(cfo_hz):
        raise ValueError("cfo_hz must be finite")
    if not math.isfinite(gain) or gain < 0:
        raise ValueError("gain must be finite and >= 0")

    out = samples.astype(np.complex128) * gain
    if cfo_hz:
        t = np.arange(len(out), dtype=np.float64) / SAMPLE_RATE
        out *= np.exp(2j * np.pi * cfo_hz * t)
    if not math.isinf(snr_db):
        generator = rng if rng is not None else np.random.default_rng()
        signal_power = float(np.mean(np.abs(out) ** 2)) if out.size else 0.0
        noise_power = signal_power / (10.0 ** (snr_db / 10.0))
        noise = (generator.standard_normal(len(out)) + 1j * generator.standard_normal(len(out)))
        out += noise * math.sqrt(noise_power / 2.0)
    if sample_offset:
        out = np.concatenate((np.zeros(sample_offset, dtype=np.complex128), out))
    return out.astype(np.complex64)


def run_sweep(payload: bytes, snr_values: list[float], packets: int, seed: int) -> list[tuple[float, int, int]]:
    """Return (SNR dB, successful packets, packet count) for a reproducible sweep."""
    if packets < 1:
        raise ValueError("packets must be >= 1")
    results = []
    root_rng = np.random.default_rng(seed)
    frame = encode_frame(payload)
    for snr in snr_values:
        success = 0
        for _ in range(packets):
            channel_rng = np.random.default_rng(int(root_rng.integers(0, 2**32 - 1)))
            received = apply_channel(frame, snr_db=snr, rng=channel_rng)
            try:
                if decode_frame(received) == payload:
                    success += 1
            except ValueError:
                pass
        results.append((snr, success, packets))
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--message", default="NEXLINK over a simulated channel")
    parser.add_argument("--snr", default="30,20,15,10,5,0", help="comma-separated SNR values in dB")
    parser.add_argument("--packets", type=int, default=20, help="packets per SNR point")
    parser.add_argument("--seed", type=int, default=2026, help="random seed for reproducible results")
    args = parser.parse_args()
    try:
        snr_values = [float(value.strip()) for value in args.snr.split(",")]
        if not snr_values or any(not math.isfinite(value) for value in snr_values):
            raise ValueError("SNR values must be finite numbers")
        results = run_sweep(args.message.encode("utf-8"), snr_values, args.packets, args.seed)
    except ValueError as exc:
        parser.error(str(exc))
    print("NEXLINK-PHY channel simulation (software only; no RF transmitted)")
    print(f"message={args.message!r} | packets/SNR={args.packets} | seed={args.seed}")
    print(f"{'SNR (dB)':>10} {'Success':>10} {'PER':>10}")
    for snr, success, total in results:
        print(f"{snr:>10.1f} {success:>5}/{total:<4} {1 - success / total:>9.1%}")


if __name__ == "__main__":
    main()
