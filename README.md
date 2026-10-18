# NEXLINK-PHY

**NEXLINK-PHY is an open research project for developing and validating an experimental wireless physical layer (PHY).** The long-term goal is a reproducible, documented system that can move data between compatible radio devices—not merely produce waveform files.

> **Current status: early software prototype.** The repository implements an experimental binary-FSK baseband waveform, packet framing, a basic receiver, and a software channel simulator. It has not yet demonstrated over-the-air communication, production reliability, a performance advantage, or a novel/patentable invention.

- Repository: https://github.com/hunterkritik-byte/NEXLINK-PHY
- Language: Python 3.10+
- Current focus: make the software measurable and robust before adding radio hardware.
- License: see the repository's license file (if present); check the repository before redistributing.

## 1. Design overview

The intended data path is:

```text
Application message
      |
      v
Payload bytes
      |
      v
Frame builder: preamble | sync | length | payload | CRC
      |
      v
Binary-FSK modulator -> complex baseband IQ samples
      |
      v
[Simulated channel now] -> [SDR transmitter/real channel later]
      |
      v
Receiver: detect preamble/sync -> estimate symbols -> validate length/CRC
      |
      v
Recovered payload bytes
```

The first version deliberately uses familiar, simple techniques as a baseline. Binary FSK and CRC are established methods; combining them in this prototype is not, by itself, evidence of a new PHY. The research contribution—if any—must be established by prior-art review and repeatable measurements.

### Current experimental parameters

| Parameter | Current value |
|---|---:|
| Complex baseband sample rate | 240,000 samples/s |
| Symbol rate | 2,000 symbols/s |
| Samples per symbol | 120 |
| Bit 0 tone | 10 kHz |
| Bit 1 tone | 20 kHz |
| Preamble | 24 alternating bits |
| Sync word | 0xD391 (16 bits) |
| Payload length field | 16-bit unsigned, big-endian |
| Maximum payload | 4,096 bytes |
| Integrity check | CRC-16/CCITT-FALSE over length + payload |
| Receiver | Initial noncoherent tone-energy detector |

These are software-prototype settings, not a finalized radio specification. They do not establish a supported RF center frequency, legal operating band, link budget, range, throughput guarantee, or compatibility with existing radios.

### Frame format

```text
+----------+----------+-------------+----------------+----------+
| Preamble | Sync     | Length      | Payload        | CRC-16   |
| 24 bits  | 16 bits  | 16 bits     | 0–4096 bytes   | 16 bits  |
+----------+----------+-------------+----------------+----------+
```

The receiver searches for the synchronization pattern, checks the declared payload length, and validates the CRC. CRC helps detect accidental corruption; it does **not** provide authentication, confidentiality, replay protection, or protection against deliberate tampering.

## 2. What works today—and what does not

### Implemented in software

- Experimental binary-FSK baseband frame encoding and decoding.
- Complex64 IQ sample generation.
- Preamble/sync search and noncoherent tone-energy detection.
- Payload-length checks and CRC-16/CCITT-FALSE integrity validation.
- A reproducible software channel harness for additive white Gaussian noise (AWGN), carrier-frequency offset, gain scaling, and leading sample delay.
- Unit tests for frame round trips, CRC, sample offsets, invalid inputs, corruption detection, and channel-harness behavior.

### Not yet implemented or demonstrated

- A transmitter or receiver driver for SDR hardware.
- Verified transmission and reception between two separate devices.
- Reliable timing recovery and carrier-frequency-offset estimation.
- Sample-clock mismatch, realistic multipath/fading, interference, and RF front-end characterization.
- Measured range, sensitivity, throughput, occupied bandwidth, energy consumption, or comparison against a baseline.
- Production-grade security, interoperability, certification, or a stable public release.

An encode-then-decode round trip proves only that software can recover its own generated frame under that test. A channel simulation is useful engineering evidence, but it is not a real radio test.

## 3. Quick start

Python 3.10+ is recommended.

```bash
git clone https://github.com/hunterkritik-byte/NEXLINK-PHY.git
cd NEXLINK-PHY

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
python -m pytest -q
```

Encode a message into a raw complex64 IQ file:

```bash
python nexlink_phy.py encode "hello NEXLINK" -o nexlink_frame.c64
```

Decode a compatible complex64 IQ capture at the configured sample rate:

```bash
python nexlink_phy.py decode nexlink_frame.c64
```

The IQ file is a baseband data file. It is **not** a radio transmission.

## 4. Simulate a noisy channel

Run a repeatable packet-success sweep:

```bash
python nexlink_channel.py \
  --message "hello NEXLINK" \
  --snr 30,20,15,10,5,0 \
  --packets 100 \
  --seed 2026
```

The simulator reports successful packets and packet error rate (PER) for each signal-to-noise ratio (SNR). Use the same seed and parameters when comparing receiver changes. Record the command, software revision, and results.

Current model limitations: the harness is not a full RF/channel model. It does not yet reproduce multipath fading, sample-clock drift, real receiver noise figures, nonlinearities, antenna behavior, or a complete transmitter/receiver chain. Results must be labeled as simulation.

## 5. Roadmap to a public, real-world release

The release goal is a **reproducible experimental wireless link with evidence**, not a claim that a new global standard has been created. Every phase should produce artifacts, tests, and documented pass/fail criteria. Do not mark a phase complete merely because code was written.

### Phase 0 — Reproducible software baseline

- [ ] Make installation work on supported Python versions and clean environments.
- [ ] Get all unit tests and GitHub Actions CI passing; keep regression tests for every fixed bug.
- [ ] Validate package metadata, CLI usage, error messages, and empty/maximum-size payload handling.
- [ ] Add a documented frame-format specification and versioning policy.
- [ ] Add deterministic test vectors for encoded frames and CRC.
- [ ] Test malformed frames, truncated captures, random input, and length/CRC edge cases.

**Exit gate:** a clean checkout installs with the documented commands, and CI passes on every supported environment.

### Phase 1 — Robust baseband receiver

- [ ] Implement correlation-based preamble detection and quantify false detections.
- [ ] Add symbol timing recovery rather than relying on nominal sample alignment.
- [ ] Estimate and compensate carrier-frequency offset.
- [ ] Test gain variation, noise, frequency offset, sample-rate mismatch, bursts, and truncated/overlapping frames.
- [ ] Add multipath/fading and interference models with documented assumptions.
- [ ] Run statistically meaningful SNR/PER sweeps with enough packets and confidence intervals.
- [ ] Publish baseline results and known limitations.

**Exit gate:** repeatable test reports show receiver behavior across declared channel conditions, including failures and confidence bounds.

### Phase 2 — Define the radio and test setup

- [ ] Choose a specific, affordable SDR platform compatible with the host computer and Linux drivers.
- [ ] Confirm transmit/receive capabilities, supported sample rates, frequency range, and driver/API requirements from manufacturer documentation.
- [ ] Separate PHY logic from device-specific I/O using a clear sample-stream interface.
- [ ] Define IQ format, scaling, sample rate, center-frequency configuration, gain controls, buffering, and error handling.
- [ ] Add a simulated or file-backed radio backend so development can continue without hardware.
- [ ] Document a receive-only bring-up procedure before enabling transmission.
- [ ] Check applicable Nepal and test-location radio rules; select only authorized frequencies, power, bandwidth, and test conditions.

**Exit gate:** a reproducible hardware plan, driver integration, and legal test procedure exist. No over-the-air transmission until the setup is authorized.

### Phase 3 — First real device-to-device link

- [ ] Integrate SDR transmit and receive paths behind explicit configuration and safe defaults.
- [ ] Validate with recorded IQ files before any RF test.
- [ ] Begin with a permitted conducted/cabled setup using appropriate attenuation and power limits, where supported; protect receiver inputs from excessive power.
- [ ] Send known test payloads between two separate endpoints and verify byte-for-byte recovery.
- [ ] Record device models, software versions, sample rate, center frequency, gains, antenna/cable setup, environment, and test commands.
- [ ] Measure packet success/PER, effective data rate, startup/acquisition behavior, and disconnect/recovery behavior.
- [ ] Only then conduct a lawful, low-risk over-the-air test and record the setup and results.

**Exit gate:** independently repeatable communication between separate devices with raw logs and measured results. Simulation alone does not satisfy this gate.

### Phase 4 — Security, reliability, and usability

- [ ] Define a threat model and document what the PHY does and does not protect.
- [ ] Keep CRC for accidental-error detection; use a reviewed, standard authenticated-encryption protocol at a higher layer if sensitive data is carried.
- [ ] Specify peer identity, key management, replay handling, and message-size limits if the product supports secure messaging.
- [ ] Fuzz frame parsing and test malformed/noisy input, resource limits, and recovery after errors.
- [ ] Handle device removal, I/O timeouts, partial frames, and configuration failures safely.
- [ ] Add clear diagnostics, configuration validation, logs, and troubleshooting documentation.
- [ ] Review dependencies and provide a security reporting/contact process.

**Exit gate:** security boundaries are documented, parser tests are robust, and no custom cryptography is being marketed as secure without review.

### Phase 5 — Performance and prior-art evaluation

- [ ] Define target use cases and constraints before tuning the design.
- [ ] Compare against relevant established PHYs using equivalent hardware, channels, bandwidth limits, payloads, and power conditions where practical.
- [ ] Measure PER versus SNR, net throughput, occupied bandwidth, sensitivity, latency, and energy use; document methodology and uncertainty.
- [ ] Search relevant papers, standards, open-source implementations, and patent claims.
- [ ] Publish raw data, scripts, configuration, hardware details, and reproducible analysis.
- [ ] Make novelty or superiority claims only when evidence supports them; obtain qualified advice before making patentability claims.

**Exit gate:** a transparent benchmark report supports every performance claim and discusses trade-offs.

### Phase 6 — Public release candidate (v1.0)

- [ ] Freeze and document the wire/frame format, parameter defaults, compatibility policy, and known limitations.
- [ ] Pass CI, regression, fuzz, and long-running stability tests.
- [ ] Test on the documented hardware/OS matrix and record unsupported configurations.
- [ ] Add an installation guide, quick-start, troubleshooting, hardware setup, RF safety, and developer documentation.
- [ ] Choose and add an explicit open-source license after confirming project ownership and intended terms.
- [ ] Publish versioned source releases, checksums, release notes, and reproducible test results.
- [ ] Include an honest statement of regulatory status; do not imply certification or approval that has not been obtained.
- [ ] Gather external feedback and fix release-blocking issues before tagging v1.0.

**Exit gate:** a new contributor can reproduce the software tests; a supported hardware user can follow the guide to reproduce the demonstrated link; limitations and safety requirements are explicit.

## 6. Hardware, cost, and safety

Software development and simulation can start without purchasing hardware. A genuine device-to-device radio demonstration will eventually require compatible radio hardware (typically two SDR endpoints, or an appropriate alternative platform), suitable host connections, and a compliant test setup. Exact cost depends on hardware choice; no specific device or price is assumed here.

Do not transmit on arbitrary frequencies or connect an SDR transmitter to an antenna before understanding frequency, gain, power, bandwidth, and local rules. Prefer receive-only checks and appropriately attenuated conducted tests where suitable. Follow the radio regulations applicable to the country and location of testing.

## 7. Research integrity

- Binary FSK, packet framing, preambles, CRCs, and SDRs are established concepts.
- A new repository or custom packet format does not automatically make a novel PHY.
- Simulation, cabled testing, and over-the-air testing are different evidence levels; report them separately.
- Do not claim range, reliability, security, certification, or performance until measured.
- CRC is not encryption or authentication.
- Do not send sensitive information over an experimental link without a separately reviewed security layer.

## 8. Contributing and reporting results

Reproducible bug reports and test results are welcome. Include the commit/release, operating system, Python version, command, random seed, expected and actual output, and a minimal test case. For radio tests, additionally include hardware and driver versions, sample rate, center frequency, bandwidth, gain, test setup, and applicable authorization. Do not publish sensitive keys or private data.

See [docs/PHY-DESIGN.md](docs/PHY-DESIGN.md) for the initial frame details and [GitHub Actions](https://github.com/hunterkritik-byte/NEXLINK-PHY/actions) for automated test status.
