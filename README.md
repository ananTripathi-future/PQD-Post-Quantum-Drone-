# 🚀 Post-Quantum Secure Drone Communication System

> A **military-grade simulation** of quantum-resistant drone communication with **13 advanced defense layers**, including Quantum Key Distribution (BB84), Post-Quantum Cryptography (Kyber/Dilithium), Frequency Hopping Anti-Jamming, GPS Spoofing Defense, and Secure Hardware Key Storage.

---

## 🔥 Overview

This project demonstrates a **next-generation secure communication system** for drones that is:

* 🔒 **Confidential**
* ✍️ **Authenticated**
* 🛡️ **Tamper-proof**
* 🔮 **Quantum-resistant**
* ⚡ **Ultra-low latency**

It integrates **quantum physics + lattice cryptography + embedded security principles** to simulate real-world defense-grade systems.

---

## 🎯 Security Goals

| Goal               | Implementation                     |
| ------------------ | ---------------------------------- |
| 🔒 Confidentiality | AES-256-GCM Encryption             |
| ✍️ Authentication  | ML-DSA (Dilithium) Signatures      |
| 🛡️ Integrity      | AES-GCM + Signature Verification   |
| 🔮 Quantum Safety  | QKD (BB84) + ML-KEM (Kyber)        |
| ⚡ Performance      | Lattice Cryptography + Optical QKD |

---

## 🧠 System Workflow

### 🟢 Step 1: Identity Setup

* ML-DSA key pairs generated
* Public keys pre-shared
* Private keys stored in **TPM/HSM secure enclave**

### 🔑 Step 2: Hybrid Key Exchange

* **QKD (BB84)** → quantum key generation
* **ML-KEM (Kyber)** → secure encapsulation
* Combined key:

```
SHA-256(QKD_Key + ML-KEM_Key)
```

### ✍️ Step 3: Command Signing

* Commands signed using ML-DSA

### 🔐 Step 4: Encryption

* AES-256-GCM encryption with secure key access

### 📡 Step 5: Secure Transmission

* Frequency Hopping Spread Spectrum (FHSS)
* Anti-jamming with dynamic hopping

### 🧾 Step 6: Drone Verification

* Signature verification
* Decryption
* Replay protection (nonce + timestamp)
* IDS anomaly detection

### ⚙️ Step 7: Execution

* Valid commands executed
* Invalid → **Fail-safe (Return-To-Base)**

---

## 🛡️ 13 Defense Layers

* Quantum Key Distribution (BB84)
* ML-KEM (Kyber-512)
* ML-DSA (Dilithium-44)
* AES-256-GCM Encryption
* Intrusion Detection System (IDS)
* Replay Protection
* Fail-Safe Lockdown
* Autonomous Recovery
* Frequency Hopping (FHSS)
* Anti-GPS Spoofing
* TPM/HSM Secure Storage
* Human-in-the-Loop (HITL)
* Secure Boot & Attestation

---

## 🗂️ Project Structure

```
Post_Quantum_Drone_Final/
│
├── simulate.py
├── controller.py
├── drone.py
├── crypto_utils.py
├── comm_security.py
├── nav_security.py
├── secure_hardware.py
├── hitl_engine.py
├── hitl_server.py
├── requirements.txt
└── dashboard/
    ├── index.html
    ├── app.js
    └── style.css
```

---

## ⚙️ Installation

```bash
pip install -r requirements.txt
```

### Required Packages

* kyber-py
* dilithium-py
* cryptography

---

## ▶️ Running the Simulation

```bash
python simulate.py
```

---

## 🧪 Simulation Scenarios

1. ✅ Valid Command Execution
2. 🔁 Replay Attack Detection
3. 🚨 Active Defense Trigger
4. 🔄 Recovery Phase
5. 🛑 Fail-Safe Mode
6. 📡 Signal Loss Handling
7. 👨‍💻 HITL Authorization
8. 📶 FHSS Anti-Jamming
9. 🛰️ GPS Spoofing Defense
10. 🔐 HSM Tampering Detection

---

## ⚡ Active Defense System

When an attack is detected, the system:

* 🛑 Rejects all commands
* 🔒 Wipes sensitive keys (QRNG scramble)
* 🔁 Regenerates secure keys
* 📡 Switches communication channels
* 🕵️ Sends fake telemetry (deception mode)
* 🧠 Activates autonomous safe mode
* 🚨 Alerts base controller

---

## 🔐 Security Coverage

### Classical Attacks

* Man-in-the-Middle → ❌ Blocked
* Replay Attack → ❌ Blocked
* Signal Jamming → ❌ Blocked
* GPS Spoofing → ❌ Blocked

### Quantum Attacks

* Shor’s Algorithm → ❌ Ineffective
* Quantum Key Breaking → ❌ Prevented

---

## ⚡ Performance Advantage

* ⚡ **1–5 ms execution latency**
* ⚡ Faster than RSA/ECC systems
* ⚡ Hardware-accelerated AES encryption
* ⚡ Quantum + lattice-based efficiency

---

## 🌐 HITL Dashboard

```bash
pip install flask flask-cors
python hitl_server.py
```

Open:

```
http://localhost:5000
```

---

## 👨‍💻 Author

**Anant Tripathi**

* Cybersecurity Enthusiast
* Quantum Computing Explorer
* Hackathon Winner 🏆

---

## ⚠️ Disclaimer

This project is developed for:

* 🎓 Academic learning
* 🔬 Research demonstration
* 🛡️ Cybersecurity simulation

It does **NOT** control real drones or weapons.

---

## ⭐ Project Tag

**#PostQuantum #CyberSecurity #DroneSecurity #QuantumComputing #EthicalHacking**
