import os
import time
import json
import base64
import hashlib
from crypto_utils import PQCrypto, AESCipher
from secure_hardware import SecureEnclave
from comm_security import SecureTransmitter


class Controller:
    def __init__(self, drone_public_keys):
        print("=" * 60)
        print("  CONTROLLER INITIALIZATION — SECURE BOOT SEQUENCE")
        print("=" * 60)

        self.drone_kem_pk = drone_public_keys["kem_pk"]
        self.drone_dsa_pk = drone_public_keys["dsa_pk"]

        # ── Secure Hardware (TPM/HSM) ──
        print("\n[Controller] Phase 1: Initializing Secure Hardware Enclave...")
        self.hsm = SecureEnclave("CTRL-001")

        # Secure boot measurement
        self.hsm.measure_boot_component("bootloader", b"ctrl_boot_v1.3")
        self.hsm.measure_boot_component("os_kernel", b"ctrl_os_v2.0")
        self.hsm.measure_boot_component("crypto_engine", b"pqc_crypto_v1.0")
        self.hsm.validate_boot_chain()

        # ── ML-DSA Key Generation ──
        print("\n[Controller] Phase 2: Generating ML-DSA keypair for authentication...")
        self.dsa_pk, self.dsa_sk = PQCrypto.generate_dsa_keys()

        # Store DSA private key in HSM
        self.hsm.store_key("dsa_private", self.dsa_sk, "ML-DSA-44")

        # ── Communication Security ──
        self.comm = None  # Initialized after key exchange

        # Shared secret key placeholder
        self.shared_key = None
        self.nonce_counter = 0

        print("\n" + "=" * 60)
        print("  CONTROLLER INITIALIZATION COMPLETE")
        print("=" * 60)

    def get_public_key(self):
        return self.dsa_pk

    def establish_session(self, eve_present=False):
        print("\n=== STEP 0: Quantum Key Distribution (QKD) BB84 ===")
        print("[Controller] Initiating optical QKD link...")
        from qkd_bb84 import simulate_qkd_exchange
        qkd_success, qkd_key = simulate_qkd_exchange(eve_present=eve_present)

        if not qkd_success:
            print("[Controller] [ALERT] QKD Compromised! No-Cloning Theorem detected an attacker.")
            print("[Controller] Aborting Hybrid Key Exchange.")
            return None

        print("\n=== STEP 1: Key Exchange (Post-Quantum) ===")
        print("[Controller] Encapsulating shared secret using Drone's ML-KEM public key...")
        kem_shared_key, kem_ciphertext = PQCrypto.kem_encapsulate(self.drone_kem_pk)

        print("[Controller] Deriving HYBRID Master Key: SHA-256(QKD_Key + ML-KEM_Key)")
        self.shared_key = hashlib.sha256(qkd_key + kem_shared_key).digest()

        # Store shared key in HSM
        self.hsm.store_key("session_shared_key", self.shared_key, "AES-256")

        # Initialize FHSS communication with shared key
        print("[Controller] Initializing Frequency Hopping (FHSS) with hybrid key...")
        self.comm = SecureTransmitter(self.shared_key, "Controller-TX")

        return kem_ciphertext, qkd_key

    def verify_handshake_response(self, encrypted_response):
        """
        Verifies the Drone's response to complete the 2-way handshake.
        """
        print("\n[Controller] >>> Phase 3: Verifying Drone Handshake Response (2-Way Handshake)...")
        try:
            # Decrypt the response using the derived shared key
            print("[Controller] Decrypting Drone response using Master Key...")
            decrypted_payload = AESCipher.decrypt(self.shared_key, encrypted_response)
            
            # Find the split points using the 4-byte length header
            ack_len = int.from_bytes(decrypted_payload[:4], 'big')
            ack_bytes = decrypted_payload[4:4+ack_len]
            signature = decrypted_payload[4+ack_len:]
            
            ack_message = json.loads(ack_bytes.decode('utf-8'))
            print(f"[Controller] Handshake JSON Received: {ack_message}")
            
            # Verify Signature
            print("[Controller] Verifying Drone's ML-DSA signature...")
            if PQCrypto.verify_message(self.drone_dsa_pk, ack_bytes, signature):
                print("[Controller] [OK] 2-Way Handshake VERIFIED. Mutual Authentication Established.")
                return True
            else:
                print("[Controller] ❌ 2-Way Handshake FAILED: Invalid Drone Signature.")
                return False
        except Exception as e:
            print(f"[Controller] ❌ 2-Way Handshake FAILED: {str(e)}")
            return False

    def send_command(self, action: str, require_human_auth: bool = True):
        if not self.shared_key:
            raise ValueError("[Controller] Session not established yet!")

        # Check HSM tamper status before any operation
        tamper = self.hsm.check_tamper_status()
        if not tamper["all_sensors_ok"]:
            print("[Controller] ❌ HSM TAMPER DETECTED — Cannot send commands")
            return None

        if require_human_auth:
            print(f"\n[Ground Station Console] [!!] PENDING COMMAND AUTHORIZATION [!!]")
            print(f"Target Action: {action}")
            auth = input("Operator, do you authorize this transmission? (y/n): ").strip().lower()
            if auth != 'y':
                print("[Controller] Command transmission ABORTED by human operator.")
                return None

        self.nonce_counter += 1
        timestamp = int(time.time())

        command_dict = {
            "action": action,
            "nonce": self.nonce_counter,
            "timestamp": timestamp
        }
        command_bytes = json.dumps(command_dict).encode('utf-8')

        print("\n=== STEP 2: Command Signing ===")
        print(f"[Controller] Signing command: {command_dict}")
        # Retrieve DSA key from HSM for signing
        dsa_key = self.hsm.get_key("dsa_private")
        signature = PQCrypto.sign_message(dsa_key, command_bytes)

        # Package data (command + signature)
        # Using a simple structure: | len(cmd) 4 bytes | cmd | signature |
        cmd_len = len(command_bytes).to_bytes(4, 'big')
        payload = cmd_len + command_bytes + signature

        print("\n=== STEP 3: Encryption ===")
        print("[Controller] [QRNG] Generating 1-time random intermediate session key...")
        from crypto_utils import QRNG
        intermediate_key = QRNG.generate_true_random_bytes(32)
        
        print("[Controller] Encrypting Command+Signature using the random intermediate key (AES-GCM)...")
        encrypted_inner_payload = AESCipher.encrypt(intermediate_key, payload)
        
        print("[Controller] Encrypting the intermediate key using the Post-Quantum Shared Master Key (from HSM)...")
        session_key = self.hsm.get_key("session_shared_key")
        encrypted_intermediate_key = AESCipher.encrypt(session_key, intermediate_key)
        
        # Package outer envelope
        # format: | len(encrypted_intermediate_key) 4 bytes | encrypted_intermediate_key | encrypted_inner_payload |
        enc_key_len = len(encrypted_intermediate_key).to_bytes(4, 'big')
        encrypted_payload = enc_key_len + encrypted_intermediate_key + encrypted_inner_payload

        print("\n=== STEP 4: Secure Transmission (FHSS) ===")
        if self.comm:
            tx_meta = self.comm.transmit(len(encrypted_payload))
            print(f"[Controller] Transmitted via FHSS — Channel: {tx_meta['channel_mhz']} MHz, "
                  f"Protocol: {tx_meta['protocol']}")
        else:
            print("[Controller] Sending Encrypted Payload to Drone...")

        return encrypted_payload

    def process_drone_response(self, encrypted_response: bytes):
        """
        Receives, decrypts, and verifies a secure response from the Drone.
        """
        if not encrypted_response:
            print("[Controller] No response received from Drone.")
            return False

        print("\n=== STEP 12: Receive & Verify Drone Response (Bi-directional) ===")
        
        # 1. Receive Metadata (FHSS)
        if self.comm:
            self.comm.receive(len(encrypted_response))
            
        try:
            # 2. Decrypt with Shared Master Key
            print("[Controller] Decrypting Drone response using Post-Quantum Master Key...")
            packet = AESCipher.decrypt(self.shared_key, encrypted_response)
            
            # 3. Unpack [len(telemetry) | telemetry | signature]
            tele_len = int.from_bytes(packet[:4], 'big')
            telemetry_bytes = packet[4:4+tele_len]
            signature = packet[4+tele_len:]
            
            # 4. Verify Drone's ML-DSA Signature
            print("[Controller] Verifying Drone's ML-DSA signature...")
            if not PQCrypto.verify_message(self.drone_dsa_pk, telemetry_bytes, signature):
                print("[Controller] ❌ SECURE RESPONSE VERIFICATION FAILED (Invalid Signature)")
                return False
                
            telemetry = json.loads(telemetry_bytes.decode('utf-8'))
            print(f"[Controller] [OK] SECURE TELEMETRY RECEIVED: {telemetry}")
            return True
            
        except Exception as e:
            print(f"[Controller] ❌ SECURE RESPONSE VERIFICATION FAILED: {str(e)}")
            return False
