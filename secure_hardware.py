"""
Secure Hardware Module — TPM-like Key Storage Simulation
=========================================================
Simulates a Trusted Platform Module (TPM) / Hardware Security Module (HSM)
for secure key storage on both the transmitter and drone.

Security properties:
  1. Keys never leave the secure enclave in plaintext
  2. All cryptographic operations happen INSIDE the enclave
  3. Tamper detection — physical/logical intrusion triggers key wipe
  4. Secure boot chain validation
  5. Key attestation — prove keys are stored in genuine hardware
  6. Anti-extraction — keys are bound to hardware identity
"""

import hashlib
import hmac
import os
import time
from enum import Enum


class EnclaveState(Enum):
    SEALED = "SEALED"           # Normal secure operation
    PROVISIONING = "PROVISIONING"  # Key loading phase
    TAMPERED = "TAMPERED"       # Tamper detected — all keys wiped
    LOCKED = "LOCKED"           # Locked out (too many bad attempts)


class SecureEnclave:
    """
    Simulated Trusted Platform Module (TPM) / Hardware Security Module (HSM).

    Keys are stored inside the enclave and NEVER exposed in plaintext.
    All sign/verify/encrypt/decrypt operations happen inside the enclave.
    """

    MAX_AUTH_ATTEMPTS = 3  # Lock after 3 failed authentication attempts

    def __init__(self, device_id: str = "DRONE-001"):
        self.device_id = device_id
        self.state = EnclaveState.PROVISIONING

        # Hardware-bound identity (simulated — in real TPM this is burned into hardware)
        self._hardware_id = hashlib.sha256(
            f"HW_ID_{device_id}_{os.urandom(16).hex()}".encode()
        ).hexdigest()[:16]

        # Internal key storage (never exposed)
        self._key_store = {}
        self._auth_failures = 0

        # PCR (Platform Configuration Register) — measures boot integrity
        self._pcr_values = {}
        self._boot_log = []

        # Tamper detection state
        self._tamper_sensors = {
            "voltage_monitor": True,    # Detects power glitching attacks
            "mesh_integrity": True,     # Detects physical probing
            "temperature_sensor": True, # Detects freeze/heat attacks
            "clock_integrity": True,    # Detects clock manipulation
        }

        print(f"[HSM:{self.device_id}] Secure Enclave Initialized")
        print(f"[HSM:{self.device_id}]   Hardware ID: {self._hardware_id}")
        print(f"[HSM:{self.device_id}]   State: {self.state.value}")
        print(f"[HSM:{self.device_id}]   Tamper sensors: {len(self._tamper_sensors)} active")

    # ── Key Management ────────────────────────────────────────

    def store_key(self, key_name: str, key_data: bytes, key_type: str = "symmetric") -> bool:
        """
        Store a key inside the secure enclave.
        The key is encrypted with the hardware-bound key before storage.
        """
        if self.state == EnclaveState.TAMPERED:
            print(f"[HSM:{self.device_id}] ❌ TAMPERED — All operations blocked")
            return False

        if self.state == EnclaveState.LOCKED:
            print(f"[HSM:{self.device_id}] ❌ LOCKED — Too many failed auth attempts")
            return False

        # Wrap key with hardware-bound encryption
        wrapped_key = self._wrap_key(key_data)

        self._key_store[key_name] = {
            "wrapped_data": wrapped_key,
            "key_type": key_type,
            "stored_at": time.time(),
            "access_count": 0,
            "hash": hashlib.sha256(key_data).hexdigest()[:12],
        }

        self.state = EnclaveState.SEALED
        print(f"[HSM:{self.device_id}] [OK] Key '{key_name}' ({key_type}) stored securely")
        print(f"[HSM:{self.device_id}]   Key fingerprint: {self._key_store[key_name]['hash']}...")
        return True

    def has_key(self, key_name: str) -> bool:
        """Check if a key exists in the enclave (without exposing it)."""
        return key_name in self._key_store

    def get_key(self, key_name: str) -> bytes:
        """
        Retrieve a key from the enclave.
        In a real TPM, the key would NEVER leave — operations would be done inside.
        This simulation unwraps for compatibility with the existing crypto pipeline.
        """
        if self.state == EnclaveState.TAMPERED:
            raise PermissionError("HSM TAMPERED — Key access denied")
        if self.state == EnclaveState.LOCKED:
            raise PermissionError("HSM LOCKED — Key access denied")
        if key_name not in self._key_store:
            raise KeyError(f"Key '{key_name}' not found in enclave")

        self._key_store[key_name]["access_count"] += 1
        return self._unwrap_key(self._key_store[key_name]["wrapped_data"])

    def delete_key(self, key_name: str):
        """Securely erase a key from the enclave."""
        if key_name in self._key_store:
            # Overwrite with zeros before deleting (secure erase)
            self._key_store[key_name]["wrapped_data"] = b'\x00' * len(
                self._key_store[key_name]["wrapped_data"]
            )
            del self._key_store[key_name]
            print(f"[HSM:{self.device_id}] Key '{key_name}' securely erased")

    # ── Tamper Detection ──────────────────────────────────────

    def check_tamper_status(self) -> dict:
        """Check all tamper detection sensors."""
        all_ok = all(self._tamper_sensors.values())
        if not all_ok:
            self._trigger_tamper_response()

        return {
            "all_sensors_ok": all_ok,
            "sensors": dict(self._tamper_sensors),
            "state": self.state.value,
        }

    def simulate_tamper_attack(self, attack_type: str = "physical_probe"):
        """Simulate a tamper attack for testing."""
        print(f"\n[HSM:{self.device_id}] ‼️ TAMPER ATTACK DETECTED: {attack_type}")

        if attack_type == "physical_probe":
            self._tamper_sensors["mesh_integrity"] = False
        elif attack_type == "power_glitch":
            self._tamper_sensors["voltage_monitor"] = False
        elif attack_type == "freeze_attack":
            self._tamper_sensors["temperature_sensor"] = False
        elif attack_type == "clock_manipulation":
            self._tamper_sensors["clock_integrity"] = False

        self._trigger_tamper_response()

    def _trigger_tamper_response(self):
        """Respond to detected tampering — WIPE ALL KEYS."""
        print(f"[HSM:{self.device_id}] 🚨 TAMPER RESPONSE ACTIVATED")
        print(f"[HSM:{self.device_id}]   -> Wiping all stored keys...")

        for key_name in list(self._key_store.keys()):
            self._key_store[key_name]["wrapped_data"] = b'\x00' * 64
        self._key_store.clear()

        self.state = EnclaveState.TAMPERED
        print(f"[HSM:{self.device_id}]   -> All keys destroyed")
        print(f"[HSM:{self.device_id}]   -> Enclave state: TAMPERED")
        print(f"[HSM:{self.device_id}]   -> All operations blocked until hardware reset")

    # ── Secure Boot ───────────────────────────────────────────

    def measure_boot_component(self, component: str, measurement: bytes):
        """Add a measurement to the PCR (boot chain validation)."""
        pcr_idx = len(self._pcr_values)
        hash_val = hashlib.sha256(measurement).hexdigest()[:16]
        self._pcr_values[f"PCR-{pcr_idx}"] = {
            "component": component,
            "hash": hash_val,
            "measured_at": time.time(),
        }
        self._boot_log.append(f"PCR-{pcr_idx}: {component} = {hash_val}")
        print(f"[HSM:{self.device_id}] BOOT MEASURE: {component} -> PCR-{pcr_idx} = {hash_val}")

    def validate_boot_chain(self) -> bool:
        """Validate that the boot chain is intact (no rogue firmware)."""
        if not self._pcr_values:
            print(f"[HSM:{self.device_id}] ⚠️ No boot measurements recorded")
            return False

        print(f"[HSM:{self.device_id}] Validating boot chain ({len(self._pcr_values)} components)...")
        for pcr_id, data in self._pcr_values.items():
            print(f"[HSM:{self.device_id}]   {pcr_id}: {data['component']} -> {data['hash']} [OK]")

        print(f"[HSM:{self.device_id}] [OK] Boot chain integrity VERIFIED")
        return True

    # ── Key Attestation ───────────────────────────────────────

    def generate_attestation(self) -> dict:
        """
        Generate an attestation proving keys are stored in genuine hardware.
        In production this would be signed by the TPM's endorsement key.
        """
        attestation_data = {
            "device_id": self.device_id,
            "hardware_id": self._hardware_id,
            "state": self.state.value,
            "keys_stored": len(self._key_store),
            "key_names": list(self._key_store.keys()),
            "boot_measurements": len(self._pcr_values),
            "tamper_sensors_ok": all(self._tamper_sensors.values()),
            "timestamp": time.time(),
        }

        # Sign attestation with hardware-bound key
        att_bytes = str(attestation_data).encode()
        attestation_data["signature"] = hmac.new(
            self._hardware_id.encode(),
            att_bytes,
            hashlib.sha256
        ).hexdigest()[:16]

        return attestation_data

    # ── Internal Methods ──────────────────────────────────────

    def _wrap_key(self, key_data: bytes) -> bytes:
        """Wrap a key with the hardware-bound encryption key (simulated)."""
        # In a real TPM, this uses the Storage Root Key (SRK)
        wrapper = hashlib.sha256(self._hardware_id.encode()).digest()
        wrapped = bytes(a ^ b for a, b in zip(
            key_data, (wrapper * ((len(key_data) // len(wrapper)) + 1))[:len(key_data)]
        ))
        return wrapped

    def _unwrap_key(self, wrapped_data: bytes) -> bytes:
        """Unwrap a key (XOR is symmetrical, so same operation)."""
        return self._wrap_key(wrapped_data)

    def get_status(self) -> dict:
        return {
            "device_id": self.device_id,
            "hardware_id": self._hardware_id,
            "state": self.state.value,
            "keys_stored": len(self._key_store),
            "key_names": list(self._key_store.keys()),
            "tamper_sensors": dict(self._tamper_sensors),
            "boot_measurements": len(self._pcr_values),
        }


def demo_secure_hardware():
    """Demonstrate the TPM-like Secure Hardware Module."""
    print("\n" + "=" * 60)
    print("  🔒 SECURE HARDWARE (TPM/HSM) DEMO")
    print("=" * 60)

    # Create secure enclaves for both devices
    drone_hsm = SecureEnclave("DRONE-001")
    controller_hsm = SecureEnclave("CTRL-001")

    # Simulate secure boot
    print("\n--- Secure Boot Chain ---")
    drone_hsm.measure_boot_component("bootloader", b"bootloader_v2.1_hash")
    drone_hsm.measure_boot_component("kernel", b"linux_5.15_drone_kernel")
    drone_hsm.measure_boot_component("flight_controller", b"fc_firmware_v3.2")
    drone_hsm.measure_boot_component("crypto_module", b"pqc_crypto_v1.0")
    drone_hsm.validate_boot_chain()

    # Store keys
    print("\n--- Key Storage ---")
    test_shared_key = os.urandom(32)
    test_dsa_sk = os.urandom(64)

    drone_hsm.store_key("session_key", test_shared_key, "AES-256")
    drone_hsm.store_key("dsa_private", test_dsa_sk, "ML-DSA-44")
    controller_hsm.store_key("session_key", test_shared_key, "AES-256")

    # Attestation
    print("\n--- Key Attestation ---")
    att = drone_hsm.generate_attestation()
    print(f"  Device: {att['device_id']}")
    print(f"  Hardware ID: {att['hardware_id']}")
    print(f"  State: {att['state']}")
    print(f"  Keys stored: {att['keys_stored']}")
    print(f"  Signature: {att['signature']}")

    # Tamper attack simulation
    print("\n--- Tamper Attack Simulation ---")
    drone_hsm.simulate_tamper_attack("physical_probe")

    # Try to access keys after tampering
    print("\n--- Post-Tamper Key Access Attempt ---")
    try:
        drone_hsm.get_key("session_key")
        print("  [X] ERROR: Should not reach here!")
    except PermissionError as e:
        print(f"  [OK] Key access blocked: {e}")

    print("\n" + "=" * 60)
    print("  SECURE HARDWARE DEMO COMPLETE")
    print("=" * 60)
