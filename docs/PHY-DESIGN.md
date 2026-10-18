# NEXLINK-PHY v0.1 design notes

## Status

Research prototype. This is a custom experimental baseband frame format, not a
standard, not a validated new radio technology, and not yet a field-ready modem.
The initial binary-FSK waveform is a baseline for hardware bring-up, not a claim
of novelty. FSK itself is established prior art.

## Initial parameters

- Complex baseband sample rate: 240,000 samples/s
- Symbol rate: 2,000 symbols/s
- Samples per symbol: 120
- Bit 0: 10 kHz complex tone
- Bit 1: 20 kHz complex tone
- Detection: noncoherent tone-energy comparison
- Frame preamble: 24 alternating bits (1010 repeated 12 times)
- Sync word: 0xD391
- Length: 16-bit unsigned big-endian payload length
- Payload: 0–4096 bytes
- Integrity: CRC-16/CCITT-FALSE over length + payload

## Frame layout

`preamble | sync(16) | length(16) | payload(length bytes) | crc16(16)`

The CRC detects accidental corruption; it is not authentication or encryption.

## Run

Install dependencies:

```bash
python3 -m pip install -e '.[dev]'
```

Encode a text payload into interleaved complex64 IQ samples:

```bash
python3 nexlink_phy.py encode "hello NEXLINK" -o frame.c64
```

Decode a compatible IQ capture:

```bash
python3 nexlink_phy.py decode frame.c64
```

The decode command expects raw complex64 IQ samples at the configured sample
rate. It currently assumes nominal sample-rate alignment and a clean capture.
It is not a channel simulator; the round-trip tests validate the codec and
framing logic on generated samples only.

## Before over-the-air use

1. Obtain compatible SDR hardware and confirm its IQ sample format.
2. Add gain control, carrier-frequency-offset estimation, timing recovery,
   preamble correlation, packet error-rate measurement, and robust channel tests.
3. Check local radio regulations and use a permitted band, power level, and
   appropriate test setup. Do not connect the IQ file directly to a transmitter
   without understanding the SDR's scaling, center frequency, and RF output.
4. Compare with established PHYs and document any measurable advantage.
5. Use a reviewed authentication/encryption protocol if transmitting sensitive
   data; CRC alone provides no security.

## Prior-art starting points

- Bluetooth SIG, Bluetooth Mesh: https://www.bluetooth.com/specifications/specs/mesh-protocol/
- IETF RFC 9171, Bundle Protocol Version 7: https://www.rfc-editor.org/rfc/rfc9171.html
- GNU Radio: https://www.gnuradio.org/
- Search academic literature and patent claims for binary FSK, chirp spread
  spectrum, packet synchronization, noncoherent detection, and low-complexity
  SDR modems before making novelty or patentability claims.
