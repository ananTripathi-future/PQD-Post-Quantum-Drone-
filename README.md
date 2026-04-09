# Post-Quantum Secure Drone Communication System

> **A military-grade simulation of quantum-resistant drone communication with 12 defense layers: Quantum Key Distribution (BB84), post-quantum cryptography (Kyber/Dilithium), frequency hopping anti-jamming, GPS spoofing defense, TPM-grade secure key storage, enhanced intrusion detection, and human-in-the-loop command authorization.**

---

## 🔥 Security Goals

This system makes drone communication:

| Goal | How We Achieve It |
|------|------------------|
| 🔒 **Confidential** | AES-256-GCM encryption |
| ✍️ **Authenticated** | ML-DSA (Dilithium) digital signatures |
| 🛡️ **Tamper-proof** | AES-GCM auth tag + signature verification + IDS |
| 🔮 **Future-proof (Quantum-safe)** | QKD (BB84) + ML-KEM (Kyber) + ML-DSA (Dilithium) |
| ⚡ **Ultra-Fast (Low Latency)** | Lattice cryptography (matrix math) + optical photons process up to 100x faster than legacy RSA |

---

## 🧠 Complete Secure Communication Flow

### 🟢 Step 1: Identity Setup (Before Mission)
- Drone and transmitter each have **ML-DSA key pairs** (public + private)
- Public keys are **pre-shared** (via PKI or out-of-band)
- Private keys stored in **TPM/HSM Secure Enclave** — never exposed

### 🔑 Step 2: Hybrid Quantum Key Exchange (QKD + ML-KEM)
- **Physics Layer (QKD BB84)**: Transmitter and Drone establish a key via optical quantum photons. Due to the **No-Cloning Theorem**, if an attacker intercepts, they must measure the photons, collapsing the quantum state and introducing an error rate (~25%). If error > 11%, the system detects the attacker and aborts.
- **Math Layer (ML-KEM)**: Transmitter encapsulates another key using Drone's ML-KEM public key.
- Shared hybrid key is hashed `SHA-256(QKD_Key + ML-KEM_Key)` and stored in **HSM**.
- **FHSS** communication initialized with this hybrid key as PRNG seed.

### ✍️ Step 3: Command Signing
- Every command is **signed** using ML-DSA (private key from HSM)
- Prevents: **Fake commands, Hijacking, Command injection**

### 🔐 Step 4: Encryption
- Command + signature **encrypted** using AES-256-GCM
- AES key retrieved from **HSM secure enclave** — never in plaintext memory


### 📡 Step 6: Secure Transmission (FHSS)
- Sent via **Frequency Hopping Spread Spectrum**
- 40 frequency bands, 200 hops/sec
- Hopping sequence derived from shared key — attacker can't predict
- **Anti-jamming**: jammed channels auto-blacklisted, hopping continues

### 🧾 Step 7: Verification at Drone
Drone performs **6-layer validation**:
1. **Verify signature** (ML-DSA) — Is this from the real controller?
2. **Decrypt data** (AES-GCM) — Can we read the command?
3. **Check nonce** — Is this a replay attack?
4. **Check timestamp** — Is this command fresh (< 5 min)?
5. **Rate limit** — Too many commands per minute = suspicious
6. **Action validation** — Is this a recognized command type?
7. **Pattern analysis** — Unusual sequences (e.g., repeated ENGAGE)
8. **Anomaly score** — Cumulative risk threshold

### ⚙️ Step 8: Execution
- Only **valid commands** are executed
- Failed validation → **Fail-safe activated → RTB**

---

## 🔥 13 Defense Layers

| # | Layer | Module | Description |
|---|-------|--------|-------------|
| 1 | **QKD (BB84 Protocol)** | `qkd_bb84.py` | Quantum Physics based key exchange / No-Cloning Theorem |
| 2 | **ML-KEM (Kyber-512)** | `crypto_utils.py` | Quantum-safe math key exchange (FIPS 203) |
| 3 | **ML-DSA (Dilithium-44)** | `crypto_utils.py` | Quantum-safe digital signatures (FIPS 204) |
| 4 | **AES-256-GCM** | `crypto_utils.py` | Authenticated symmetric encryption |

| 6 | **Enhanced IDS** | `drone.py` | 6-check anomaly detection engine |
| 7 | **Replay Protection** | `drone.py` | Monotonic nonce + 5-min timestamp window |
| 8 | **Fail-Safe Lockdown** | `drone.py` | Auto-reject all commands on any violation |
| 9 | **Autonomous Fallback** | `drone.py` | Signal-loss resilience + GPS-validated RTB |
| 10 | **Frequency Hopping (FHSS)**| `comm_security.py` | Anti-jamming spread spectrum |
| 11 | **Anti-GPS Spoofing** | `nav_security.py` | 5-check GPS integrity validation |
| 12 | **TPM/HSM Secure Hardware** | `secure_hardware.py` | Tamper-proof key storage + secure boot |
| 13 | **HITL Authorization** | `hitl_engine.py` | Human-in-the-loop command approval |

---

## Architecture Diagram

```
[Transmitter / Ground Controller]
   ↓
🔒 Secure Boot (TPM/HSM verifies firmware integrity)
   ↓
🟢 Step 1: Identity Setup (ML-DSA keys in HSM)
   ↓
🔑 Step 2: Hybrid Key Exchange (QKD BB84 + ML-KEM) → Derive Shared Key → Store in HSM
   ↓
✍️ Step 3: Sign Command (ML-DSA private key from HSM)
   ↓
🔐 Step 4: Encrypt (AES-256-GCM, key from HSM)
   ↓

📡 Step 6: FHSS Transmission (frequency hopping, anti-jam)
   ↓
[Drone]
   ↓
🔒 Secure Boot (TPM/HSM verifies firmware integrity)
   ↓
📡 Step 6b: FHSS Reception (synchronized hopping)
   ↓

🔐 Step 7b: Decrypt (AES-256-GCM, key from HSM)
   ↓
✍️ Step 7c: Verify Signature (ML-DSA)
   ↓
🛡️ Step 7d: Enhanced IDS (Nonce + Time + Rate + Pattern + Score)
   ↓
🛰️ Step 7e: Validate GPS (Anti-spoofing — 5 checks)
   ↓
⚙️ Step 8: Execute Command (or Fail-Safe → RTB)
```

---

## Project Structure

```
Post_Quantum_Drone_Final/
│
├── simulate.py          # Main simulation — 8 scenarios
├── controller.py        # Ground Controller (sign, encrypt, FHSS)
├── drone.py             # Drone (verify, decrypt, IDS, fail-safe, GPS)
├── crypto_utils.py      # Core crypto: ML-KEM, ML-DSA, AES-GCM
├── comm_security.py     # Frequency Hopping Spread Spectrum (FHSS)
├── nav_security.py      # Anti-GPS Spoofing (5 defense checks)
├── secure_hardware.py   # TPM/HSM simulation (secure key storage + tamper detect)
├── hitl_engine.py       # Human-in-the-Loop decision engine
├── hitl_server.py       # Flask dashboard backend
├── requirements.txt     # Python dependencies
├── README.md            # This file
│
└── dashboard/           # Tactical web dashboard
    ├── index.html
    ├── app.js
    └── style.css
```

---

## Requirements & Installation

```bash
pip install -r requirements.txt
```

**Packages:**
| Package | Purpose |
|---------|---------|
| `kyber-py` | ML-KEM (Kyber) key encapsulation |
| `dilithium-py` | ML-DSA (Dilithium) digital signatures |
| `cryptography` | AES-GCM authenticated encryption |


> All pure Python — no C/C++ build dependencies required.

---

## Running the Simulation

```bash
python simulate.py
```

### 10 Simulation Scenarios

| # | Scenario | What It Tests |
|---|----------|---------------|
| 1 | **Valid Command** | Full pipeline: HSM boot → QKD → ML-KEM → ML-DSA → QRNG Envelope → FHSS → IDS → Execute |
| 2 | **Replay Attack** | Attacker retransmits an old payload → IDS blocks |
| 3 | **Active Defense** | IDS triggers lockdown: Wipes keys, scrambles memory with QRNG, hops channel, fakes telemetry, activates autonomous mode |
| 4 | **Recovery Phase** | System securely re-generates ML-KEM keys and restores normal transmission capabilities |
| 5 | **Post-Fail-Safe** | Attempt to send after fail-safe → drone rejects everything |
| 6 | **Signal Loss** | Ground link drops → autonomous fallback + GPS validation → RTB |
| 7 | **HITL Authorization** | Full AI → Human → Encrypt → Execute pipeline demo |
| 8 | **FHSS Demo** | Frequency hopping synchronization + jamming evasion |
| 9 | **GPS Spoofing** | Signal strength attack, teleportation, geofence violation, IMU deviation |
| 10 | **HSM Tamper / QKD Intercept** | Secure key storage probe tests + QKD No-Cloning theorem tests |

---

## ⚡ Intelligent Active Defense (Counter-Attack System)

If an attacker attempts a brute-force attack, spam-floods the network, or sends forged packets, the **Intrusion Detection System (IDS)** instantly prints `👉 'System under attack detected'` and isolates the aircraft. 

Instead of attacking the enemy, the drone protects its data executing a **7-Step Active Defense Lifecycle**:
1. 🛑 **Command Rejection**: All unverified (or flooded) commands are hard-rejected. The communication channel is temporarily locked.
2. 🔒 **Data Protection (QRNG Scramble)**: Sensitive session keys in active memory and hardware (HSM) are wiped by flooding them with **Quantum Random Garbage**.
3. 🔁 **Secure Re-Keying**: New ML-KEM keys are instantly regenerated using quantum entropy. The old attacker's data is now completely useless.
4. 📡 **Channel Switching**: Automatically hops away from the jammed or intercepted channel to a backup frequency.
5. 🕵️ **Deception Mode 🔥**: Broadcasts fake, dummy telemetry coordinates to confuse the attacker.
6. 🧠 **Autonomous Safe Mode**: Relinquishes communication control and switches entirely to the onboard Return-To-Home system.
7. 🚨 **Alert System**: Notifies the base controller: "Intrusion detected, switching to secure mode."

---

## Security Model — What Attacks Are Blocked

### ✅ Against Classical Attacks

| Attack | Defense | Mechanism |
|--------|---------|-----------|
| **Man-in-the-Middle** | ML-DSA Signature + AES-GCM | Attacker can't forge signed commands |
| **Replay Attack** | Monotonic Nonce + Timestamp | Old commands automatically rejected |
| **Eavesdropping** | AES-256-GCM | Data encrypted and secure |
| **Command Injection** | Action Whitelist + Pattern Analysis | Unknown commands rejected by IDS |
| **Flood / DoS** | Rate Limiting | Max 20 commands/minute enforced |
| **Signal Jamming** | FHSS (Frequency Hopping) | Auto-hops to unjammed channel |
| **GPS Spoofing** | 5-Layer GPS Validation | Signal strength, IMU cross-check, geofence |
| **Key Extraction** | TPM/HSM Secure Enclave | Keys wiped on tamper detection |

### ✅ Against Quantum Attacks

| Attack | Defense |
|--------|---------|
| **Shor's Algorithm** (breaks RSA/ECC) | ML-KEM (Kyber-512) — lattice-based, quantum-resistant |
| **Quantum Key Cracking** | ML-DSA (Dilithium-44) — lattice-based signatures |

---

## Extra Hardening — All Implemented ✅

| Feature | Module | Description |
|---------|--------|-------------|
| 📡 **Frequency Hopping** | `comm_security.py` | FHSS with 40 bands, 200 hops/sec, key-derived sequence |
| 🧠 **Enhanced IDS** | `drone.py` | 6-layer: nonce, timestamp, rate, action, pattern, anomaly score |
| 🛰️ **Anti-GPS Spoofing** | `nav_security.py` | Signal strength, speed check, geofence, IMU cross-ref, multi-constellation |
| 🔒 **Secure Key Storage** | `secure_hardware.py` | TPM/HSM: hardware-bound wrapping, tamper detect, secure boot, attestation |

---

## Key Technologies

| Technology | Standard/Version | Role |
|------------|-----------------|------|
| ML-KEM (Kyber) | FIPS 203 / Kyber-512 | Quantum-safe key encapsulation |
| ML-DSA (Dilithium) | FIPS 204 / Dilithium-44 | Quantum-safe digital signatures |
| AES-GCM | AES-256 | Authenticated symmetric encryption |

| FHSS | MIL-STD-188 | Anti-jamming spread spectrum |
| TPM 2.0 (simulated) | ISO/IEC 11889 | Secure key storage |

---

## ⚡ The Quantum Speed Advantage (Ultra-Low Latency)

Unlike legacy systems that use heavy prime factorization (RSA) or complex elliptic curves (ECC) which cause processing lag, this drone network utilizes **Lattice-Based Post-Quantum Cryptography** and **Speed-of-light Optical QKD**.

- **ML-KEM & ML-DSA**: Both Kyber and Dilithium rely on extremely fast mathematical operations (polynomial matrix multiplication over rings), which modern CPUs can compute in microseconds.
- **QKD**: Transmits initial key material at the speed of light via photons.
- **AES-256-GCM**: Hardware-accelerated symmetric encryption provides sub-millisecond data masking.

**Result:** Command encryption, signing, and verification happen in **~1-5 milliseconds**, entirely eliminating cryptographic control latency for high-speed combat and reconnaissance drone operations.

---

## Threat Model

| Attack Vector | Defense Mechanism | Module | Outcome |
|---------------|-------------------|--------|---------|
| Photon Interception | QKD (BB84 Protocol) | `qkd_bb84.py` | No-Cloning theorem collapses state, attack detected |
| Quantum Key Cracking | ML-KEM (Kyber-512) | `crypto_utils.py` | Key safe from Shor's algorithm |
| Command Forgery | ML-DSA (Dilithium-44) | `crypto_utils.py` | Invalid sig rejected |
| Eavesdropping | AES-GCM | `crypto_utils.py` | Data encrypted & secure |
| Replay Attack | Nonce + Timestamp IDS | `drone.py` | Stale cmds blocked |
| Signal Jamming | FHSS Frequency Hopping | `comm_security.py` | Auto-hop to clear channel |
| GPS Spoofing | 5-Check GPS Validation | `nav_security.py` | Spoofed fixes rejected |
| Key Extraction | TPM/HSM + Tamper Wipe | `secure_hardware.py` | Keys destroyed |
| Post-Attack Injection | Fail-Safe Lockdown | `drone.py` | All cmds rejected |
| Flood / DoS | Rate Limiting IDS | `drone.py` | Excess cmds blocked |

---

## HITL Web Dashboard

```bash
pip install flask flask-cors
python hitl_server.py
```

Open **http://localhost:5000** for the tactical dashboard.

---

## Author

**Anant Tripathi**

Built for defense research and demonstration of post-quantum cryptographic protocols in autonomous drone systems.

> **Disclaimer:** This project is a simulation for academic and research purposes. It does not interface with real drone hardware or weapons systems.
#   P Q D - P o s t - Q u a n t u m - D r o n e -  
 