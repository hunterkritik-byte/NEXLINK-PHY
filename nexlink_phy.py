#!/usr/bin/env python3
"""NEXLINK-PHY v0.1: experimental binary-FSK IQ frame codec.

This generates/decodes baseband complex IQ samples. It does not access a
radio or transmit RF; connect it to a compatible SDR only after checking
local spectrum rules and the hardware's supported sample formats.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

SAMPLE_RATE = 240_000
SYMBOL_RATE = 2_000
SAMPLES_PER_SYMBOL = SAMPLE_RATE // SYMBOL_RATE
FREQ_ZERO = 10_000.0
FREQ_ONE = 20_000.0
PREAMBLE = tuple([1, 0] * 12)
SYNC_WORD = 0xD391
MAX_PAYLOAD = 4096
CRC_INIT = 0xFFFF
CRC_POLY = 0x1021


def crc16_ccitt(data: bytes) -> int:
    """CRC-16/CCITT-FALSE (poly 0x1021, init 0xffff, no reflection)."""
    crc = CRC_INIT
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            crc = ((crc << 1) ^ CRC_POLY) & 0xFFFF if crc & 0x8000 else (crc << 1) & 0xFFFF
    return crc


def bytes_to_bits(data: bytes) -> list[int]:
    return [(byte >> shift) & 1 for byte in data for shift in range(7, -1, -1)]


def bits_to_bytes(bits: list[int]) -> bytes:
    if len(bits) % 8:
        raise ValueError("bit count must be a multiple of 8")
    out = bytearray()
    for start in range(0, len(bits), 8):
        value = 0
        for bit in bits[start:start + 8]:
            value = (value << 1) | int(bit)
        out.append(value)
    return bytes(out)


def frame_bits(payload: bytes) -> list[int]:
    """Frame: alternating preamble, sync, 16-bit length, payload, CRC16."""
    if len(payload) > MAX_PAYLOAD:
        raise ValueError(f"payload exceeds {MAX_PAYLOAD} bytes")
    body = len(payload).to_bytes(2, "big") + payload
    checksum = crc16_ccitt(body).to_bytes(2, "big")
    return list(PREAMBLE) + bytes_to_bits(SYNC_WORD.to_bytes(2, "big")) + bytes_to_bits(body + checksum)


def modulate(bits: list[int] | np.ndarray) -> np.ndarray:
    """Noncoherent binary FSK, returned as normalized complex64 IQ samples."""
    bit_array = np.asarray(bits, dtype=np.uint8)
    if bit_array.ndim != 1 or np.any(bit_array > 1):
        raise ValueError("bits must be a one-dimensional sequence of 0 and 1")
    n = np.arange(SAMPLES_PER_SYMBOL, dtype=np.float64)
    t = n / SAMPLE_RATE
    tone0 = np.exp(2j * np.pi * FREQ_ZERO * t)
    tone1 = np.exp(2j * np.pi * FREQ_ONE * t)
    iq = np.empty(len(bit_array) * SAMPLES_PER_SYMBOL, dtype=np.complex64)
    for i, bit in enumerate(bit_array):
        start = i * SAMPLES_PER_SYMBOL
        iq[start:start + SAMPLES_PER_SYMBOL] = tone1 if bit else tone0
    return iq


def encode_frame(payload: bytes) -> np.ndarray:
    """Encode one framed payload to complex baseband IQ samples."""
    return modulate(frame_bits(payload))


def _demodulate_aligned(iq: np.ndarray) -> list[int]:
    count = len(iq) // SAMPLES_PER_SYMBOL
    if count == 0:
        return []
    blocks = np.asarray(iq[:count * SAMPLES_PER_SYMBOL]).reshape(count, SAMPLES_PER_SYMBOL)
    n = np.arange(SAMPLES_PER_SYMBOL, dtype=np.float64)
    t = n / SAMPLE_RATE
    tone0 = np.exp(2j * np.pi * FREQ_ZERO * t)
    tone1 = np.exp(2j * np.pi * FREQ_ONE * t)
    energy0 = np.abs(blocks @ np.conjugate(tone0)) ** 2
    energy1 = np.abs(blocks @ np.conjugate(tone1)) ** 2
    return (energy1 > energy0).astype(np.uint8).tolist()


def decode_frame(iq: np.ndarray) -> bytes:
    """Recover a frame from IQ samples with arbitrary leading sample offset.

    This first receiver supports a clean, single frame with nominal sample
    rate and no channel impairments. Real SDR captures need CFO/timing/channel
    robustness before this can be considered a field-ready modem.
    """
    samples = np.asarray(iq, dtype=np.complex64).reshape(-1)
    preamble_and_sync = list(PREAMBLE) + bytes_to_bits(SYNC_WORD.to_bytes(2, "big"))
    header_bits = len(preamble_and_sync) + 16
    for sample_offset in range(min(SAMPLES_PER_SYMBOL, len(samples))):
        bits = _demodulate_aligned(samples[sample_offset:])
        last_start = len(bits) - header_bits
        for start in range(max(0, last_start + 1)):
            if bits[start:start + len(PREAMBLE)] != list(PREAMBLE):
                continue
            sync_start = start + len(PREAMBLE)
            sync_bits = bits[sync_start:sync_start + 16]
            if bits_to_bytes(sync_bits) != SYNC_WORD.to_bytes(2, "big"):
                continue
            length_start = sync_start + 16
            length = int.from_bytes(bits_to_bytes(bits[length_start:length_start + 16]), "big")
            if length > MAX_PAYLOAD:
                continue
            end = length_start + 16 + (length + 2) * 8
            if end > len(bits):
                continue
            encoded = bits_to_bytes(bits[length_start + 16:end])
            payload, crc_bytes = encoded[:-2], encoded[-2:]
            # The transmitted CRC covers the 16-bit length field + payload.
            crc_input = length.to_bytes(2, "big") + payload
            if crc16_ccitt(crc_input) != int.from_bytes(crc_bytes, "big"):
                continue
            return payload
    raise ValueError("no valid NEXLINK frame found (sync/length/CRC check failed)")


def main() -> None:
    parser = argparse.ArgumentParser(description="NEXLINK-PHY IQ frame encoder/decoder")
    sub = parser.add_subparsers(dest="command", required=True)
    tx = sub.add_parser("encode", help="encode a payload into complex64 IQ samples")
    tx.add_argument("payload", help="UTF-8 text payload")
    tx.add_argument("-o", "--output", default="nexlink_frame.c64")
    rx = sub.add_parser("decode", help="decode a captured complex64 IQ file")
    rx.add_argument("input")
    args = parser.parse_args()

    if args.command == "encode":
        iq = encode_frame(args.payload.encode("utf-8"))
        Path(args.output).write_bytes(iq.astype(np.complex64).tobytes())
        print(f"Wrote {len(iq)} complex64 IQ samples to {args.output}")
        print(f"Sample rate: {SAMPLE_RATE} Hz; symbol rate: {SYMBOL_RATE} baud")
        print("Baseband only: no RF was transmitted.")
    else:
        iq = np.fromfile(args.input, dtype=np.complex64)
        payload = decode_frame(iq)
        print(payload.decode("utf-8", errors="replace"))


if __name__ == "__main__":
    main()
