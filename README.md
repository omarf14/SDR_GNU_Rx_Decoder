
# SDRP GNU Rx

A GNU Radio-based BPSK receiver and PDU decoder system. This project handles symbol reception, ASM detection, PDU generation, and higher-layer decoding including Viterbi, FEC, and decryption.

---

## Requirements

* **GNU Radio Companion** (tested with v3.10.1.1)
* Python 3.x
* Required Python packages: see `requirements.txt`
* C++ compiler for FEC module

---

## Setup

1. **Install GNU Radio Companion** and all dependencies.
2. **Build FEC module**:

```bash
cd fec
make all
```

This generates the `bbfec.so` objects needed by the decoder.

---

## Usage

1. **Run the BPSK Receiver**
   This script syncs, detects the ASM, collects symbols, and packages them into PDUs. You can specify the RX source with the `--source` option:

```bash
# Use Pluto as the receiver (default)
python3 sdrp_bpsk_receiver.py --source pluto

# Use USRP as the receiver
python3 sdrp_bpsk_receiver.py --source usrp
```

2. **Run the PDU Decoder (UDP Server)**
   This script receives PDUs via UDP and applies decoding (Viterbi, FEC, decryption):

```bash
python3 sdrp_pdu_decoder.py
```

---

## Notes

* Ensure the receiver is running **before** the decoder server.
* Tested on GNU Radio v3.10.1.1 and Python 3.10.
* For modifications to FEC, rebuild using `make all` in the `fec` folder.

---
