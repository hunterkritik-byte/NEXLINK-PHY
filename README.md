# NEXLINK-PHY

**Experimental wireless physical-layer research** focused on waveform design, modulation, packet framing, synchronization, and eventual software-defined-radio (SDR) testing.

> Status: early research prototype. The current code generates and decodes baseband IQ samples; it does not transmit radio signals by itself. No claim is made yet that the waveform is novel or superior to existing PHYs.

## What exists now

- A custom experimental binary-FSK baseband frame format.
- Complex64 IQ waveform generation.
- A first noncoherent tone-energy receiver with preamble/sync search.
- Payload length checking and CRC-16/CCITT-FALSE integrity validation.
- A software channel simulator for reproducible AWGN, carrier-frequency offset, gain, and sample-delay experiments.
- Unit tests for codec round trips, sample offsets, CRC, invalid input, corruption detection, and the channel harness.

Binary FSK and CRC are established techniques. The research goal is to build a working end-to-end PHY on real radio hardware, compare it against prior art, and only then assess whether any design contribution is meaningfully novel.

## Quick start

Python 3.10+ is recommended.

```bash
python3 -m pip install -e '.[dev]'
pytest
```

Encode a short message into raw complex64 IQ samples:

```bash
python3 nexlink_phy.py encode "hello NEXLINK" -o nexlink_frame.c64
```

Decode an IQ capture saved as complex64 samples at the configured sample rate:

```bash
python3 nexlink_phy.py decode nexlink_frame.c64
```

## Simulate a noisy channel

Run a reproducible packet-success sweep over a few signal-to-noise ratios:

```bash
python3 nexlink_channel.py --message "hello NEXLINK" --snr 30,20,15,10,5,0 --packets 100 --seed 2026
```

The output reports packet success and packet error rate (PER) at each SNR point. You can use this as a baseline while improving the receiver. The simulator currently models additive white Gaussian noise (AWGN), carrier-frequency offset, gain, and leading sample delay through its Python API; it does not yet model multipath fading, sample-clock drift, real receiver noise figures, or a complete RF chain. The sweep is a software experiment, not an over-the-air test.

The encode/decode commands are for baseband software development. Encoding then decoding the same file validates the codec, not over-the-air communication.

## Initial PHY parameters

| Parameter | Value |
|---|---:|
| Sample rate | 240,000 samples/s |
| Symbol rate | 2,000 symbols/s |
| Samples per symbol | 120 |
| Bit 0 tone | 10 kHz |
| Bit 1 tone | 20 kHz |
| Payload limit | 4,096 bytes |
| Integrity check | CRC-16/CCITT-FALSE |

See [docs/PHY-DESIGN.md](docs/PHY-DESIGN.md) for the frame layout, limitations, and RF safety checklist.

## Roadmap

1. **Baseband codec** — frame encoder, IQ generation, receiver, unit tests.
2. **Repeatable channel experiments** — SNR/PER sweeps and impairment regression tests.
3. **Receiver robustness** — timing recovery, carrier-frequency-offset estimation, preamble correlation, sample-clock mismatch and multipath tests.
4. **SDR integration** — support a specific compatible SDR and validate with captured IQ and conducted/over-the-air tests in a legally permitted setup.
5. **Measured comparison** — packet error rate, sensitivity, data rate, occupied bandwidth, and power/energy measurements against suitable baselines.
6. **Prior-art review** — document related PHYs and patent claims before making novelty or patentability claims.

## Hardware reality

Ordinary Wi-Fi/Bluetooth adapters generally do not expose arbitrary waveform control. Testing this PHY over the air will require suitable SDR hardware or a radio platform that exposes the required physical-layer controls. The repository currently contains no hardware driver and does not transmit RF.

Only transmit on frequencies, bandwidths, and power levels permitted by applicable local regulations. CRC is not encryption or authentication; sensitive messages need a reviewed security protocol.

## Contributing

Issues and reproducible test results are welcome. Please include hardware, sample rate, center frequency, gain settings, capture format, and exact steps for any RF test report.
