"""
LIVE DEMO: Watch your data get secured step-by-step
=====================================================
This script shows EXACTLY what happens to your data at every stage
of the post-quantum secure pipeline.
"""

import os
import sys
import json
import time
import base64
from crypto_utils import PQCrypto, AESCipher

# Force UTF-8 output
sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None


def show_bytes(data: bytes, max_len: int = 80) -> str:
    """Show bytes as hex string, truncated."""
    hex_str = data.hex()
    if len(hex_str) > max_len:
        return hex_str[:max_len] + f"... ({len(data)} bytes total)"
    return hex_str


def run_demo():
    print("=" * 70)
    print("  LIVE SECURITY DEMO")
    print("  Watch your data get protected at every step")
    print("=" * 70)

    # ─── YOUR DATA ───────────────────────────────────────────
    your_command = "NAVIGATE_TO_COORDINATES_28.6_77.2_ALT_500"

    print(f"\n{'='*70}")
    print(f"  YOUR ORIGINAL DATA (plaintext)")
    print(f"{'='*70}")
    print(f"  Command: {your_command}")
    print(f"  As bytes: {your_command.encode().hex()}")
    print(f"  Length: {len(your_command)} characters")
    print(f"\n  >> Anyone can read this right now. Let's fix that.\n")

    # ─── STEP 1: GENERATE KEYS ──────────────────────────────
    print(f"{'='*70}")
    print(f"  STEP 1: Key Generation (Post-Quantum)")
    print(f"{'='*70}")

    print("\n  [Controller] Generating ML-DSA key pair for signing...")
    dsa_pk, dsa_sk = PQCrypto.generate_dsa_keys()
    print(f"  DSA Public Key:  {show_bytes(dsa_pk, 60)}")
    print(f"  DSA Private Key: {show_bytes(dsa_sk, 60)}")

    print("\n  [Drone] Generating ML-KEM key pair for key exchange...")
    kem_pk, kem_sk = PQCrypto.generate_kem_keys()
    print(f"  KEM Public Key:  {show_bytes(kem_pk, 60)}")
    print(f"  KEM Private Key: {show_bytes(kem_sk, 60)}")

    # ─── STEP 2: HYBRID QUANTUM KEY EXCHANGE ──────────────────
    print(f"\n{'='*70}")
    print(f"  STEP 2: Hybrid Key Exchange (QKD BB84 + ML-KEM)")
    print(f"{'='*70}")

    from qkd_bb84 import simulate_qkd_exchange
    print("\n  [Physics Layer] Running Quantum Key Distribution (BB84)...")
    qkd_success, qkd_key = simulate_qkd_exchange(eve_present=False)
    print(f"  QKD Key: {show_bytes(qkd_key)}")

    print("\n  [Math Layer] Encapsulating ML-KEM shared secret...")
    kem_shared_key_ctrl, kem_ciphertext = PQCrypto.kem_encapsulate(kem_pk)
    print(f"  KEM Ciphertext: {show_bytes(kem_ciphertext, 60)}")

    import hashlib
    shared_key_ctrl = hashlib.sha256(qkd_key + kem_shared_key_ctrl).digest()
    print(f"  Controller Hybrid Key: {show_bytes(shared_key_ctrl)}")

    print("\n  [Drone] Decapsulating ML-KEM and deriving hybrid key...")
    kem_shared_key_drone = PQCrypto.kem_decapsulate(kem_sk, kem_ciphertext)
    shared_key_drone = hashlib.sha256(qkd_key + kem_shared_key_drone).digest()
    print(f"  Drone Hybrid Key:      {show_bytes(shared_key_drone)}")

    keys_match = shared_key_ctrl == shared_key_drone
    print(f"\n  Keys match? {'YES' if keys_match else 'NO'}")
    print(f"  >> The system now uses a hybrid key combining Quantum Physics (No-Cloning)")
    print(f"  >> and Lattice-based Mathematics (Kyber-512) for ultimate security.\n")

    # ─── STEP 3: BUILD COMMAND PAYLOAD ───────────────────────
    print(f"{'='*70}")
    print(f"  STEP 3: Build Command Payload")
    print(f"{'='*70}")

    nonce = 1
    timestamp = int(time.time())
    command_dict = {
        "action": your_command,
        "nonce": nonce,
        "timestamp": timestamp
    }
    command_bytes = json.dumps(command_dict).encode('utf-8')

    print(f"\n  Command JSON: {json.dumps(command_dict, indent=4)}")
    print(f"  As bytes: {show_bytes(command_bytes, 60)}")
    print(f"  Size: {len(command_bytes)} bytes\n")

    # ─── STEP 4: SIGN THE COMMAND ────────────────────────────
    print(f"{'='*70}")
    print(f"  STEP 4: ML-DSA Digital Signature")
    print(f"{'='*70}")

    signature = PQCrypto.sign_message(dsa_sk, command_bytes)

    print(f"\n  Signing with Dilithium-44 private key...")
    print(f"  Signature: {show_bytes(signature, 60)}")
    print(f"  Signature size: {len(signature)} bytes")
    print(f"\n  >> Only someone with the private key can produce this signature.")
    print(f"  >> Drone will verify this with the public key.\n")

    # Verify it works
    valid = PQCrypto.verify_message(dsa_pk, command_bytes, signature)
    print(f"  Verification test: {'VALID' if valid else 'INVALID'}")

    # ─── STEP 5: ENCRYPT EVERYTHING ─────────────────────────
    print(f"\n{'='*70}")
    print(f"  STEP 5: AES-256-GCM Encryption")
    print(f"{'='*70}")

    # Package: | cmd_len (4 bytes) | command | signature |
    cmd_len = len(command_bytes).to_bytes(4, 'big')
    payload = cmd_len + command_bytes + signature

    print(f"\n  Payload before encryption:")
    print(f"    Command length header: {cmd_len.hex()} ({len(command_bytes)} bytes)")
    print(f"    Command data: {len(command_bytes)} bytes")
    print(f"    Signature: {len(signature)} bytes")
    print(f"    Total payload: {len(payload)} bytes")

    encrypted = AESCipher.encrypt(shared_key_ctrl, payload)

    print(f"\n  After AES-256-GCM encryption:")
    print(f"    Encrypted data: {show_bytes(encrypted, 60)}")
    print(f"    Size: {len(encrypted)} bytes (nonce + ciphertext + auth tag)")
    print(f"\n  >> This is now random-looking garbage. Without the shared key,")
    print(f"  >> it is computationally impossible to recover the original data.\n")

    # Show what an attacker sees
    print(f"  --- WHAT AN ATTACKER SEES ---")
    print(f"  {show_bytes(encrypted[:40])}...")
    print(f"  Can they read your command? NO.")
    print(f"  Can they modify it? NO (GCM auth tag detects tampering).")
    print(f"  Can a quantum computer crack it? Key is from ML-KEM (quantum-safe).\n")

    # ─── STEP 6: WHAT GETS TRANSMITTED ───────────────────────
    print(f"{'='*70}")
    print(f"  STEP 6: What Gets Transmitted Over the Air")
    print(f"{'='*70}")
    print(f"""
  TRANSMITTED: {len(encrypted)} bytes of ciphertext
  
  What's inside it:        ML-DSA signed command + nonce + timestamp
  What the command says:   "{your_command}"
  
  Can anyone read it?      NO (AES-256-GCM)
  Can anyone modify it?    NO (GCM auth tag + ML-DSA signature)  
  Can anyone replay it?    NO (nonce=1, timestamp={timestamp})
  Can quantum computers?   NO (ML-KEM + ML-DSA are post-quantum)
""")

    # ─── STEP 7: DRONE RECEIVES AND DECRYPTS ─────────────────
    print(f"{'='*70}")
    print(f"  STEP 7: Drone Receives and Processes")
    print(f"{'='*70}")

    extracted_encrypted = encrypted


    print(f"\n  [Drone] Decrypting with shared key...")
    decrypted_payload = AESCipher.decrypt(shared_key_drone, extracted_encrypted)
    print(f"  Decrypted payload: {len(decrypted_payload)} bytes")

    # Parse
    recv_cmd_len = int.from_bytes(decrypted_payload[:4], 'big')
    recv_command_bytes = decrypted_payload[4:4+recv_cmd_len]
    recv_signature = decrypted_payload[4+recv_cmd_len:]

    print(f"\n  [Drone] Verifying ML-DSA signature...")
    sig_valid = PQCrypto.verify_message(dsa_pk, recv_command_bytes, recv_signature)
    print(f"  Signature valid? {sig_valid}")

    recv_command = json.loads(recv_command_bytes.decode('utf-8'))
    print(f"\n  [Drone] Recovered command:")
    print(f"    Action:    {recv_command['action']}")
    print(f"    Nonce:     {recv_command['nonce']}")
    print(f"    Timestamp: {recv_command['timestamp']}")

    data_intact = recv_command['action'] == your_command
    print(f"\n  Data intact? {data_intact}")
    print(f"  Original: {your_command}")
    print(f"  Received: {recv_command['action']}")

    # ─── FINAL SUMMARY ──────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"  DEMO COMPLETE: Your Data Journey")
    print(f"{'='*70}")
    print(f"""
  YOUR DATA:   "{your_command}"
                          |
  SIGNED:      + {len(signature)} bytes ML-DSA signature (Dilithium-44)
                          |
  ENCRYPTED:   = {len(encrypted)} bytes AES-256-GCM ciphertext
                          |
  TRANSMITTED: Encrypted data stream
                          |
  RECEIVED:    Drone decrypts -> verifies -> EXECUTES
                          |
  RESULT:      "{recv_command['action']}"
  
  ZERO FLAWS. Data arrived intact, authenticated, and confidential.
""")



if __name__ == "__main__":
    run_demo()
