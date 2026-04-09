import os
import time
import json
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from kyber_py.ml_kem import ML_KEM_512
from dilithium_py.ml_dsa import ML_DSA_44

class QRNG:
    """
    Simulated Quantum Random Number Generator (QRNG).
    Harvests entropy from simulated quantum states (e.g., photon phase timing)
    to generate true randomness.
    """
    @staticmethod
    def generate_true_random_bytes(length: int = 32) -> bytes:
        # In a real hardware system, this interfaces with the QRNG sensor.
        print(f"[QRNG] Harvesting {length} bytes of true quantum entropy...")
        return os.urandom(length)

class PQCrypto:
    @staticmethod
    def generate_dsa_keys():
        pk, sk = ML_DSA_44.keygen()
        return pk, sk

    @staticmethod
    def sign_message(sk, message: bytes):
        return ML_DSA_44.sign(sk, message)

    @staticmethod
    def verify_message(pk, message: bytes, signature: bytes):
        return ML_DSA_44.verify(pk, message, signature)

    @staticmethod
    def generate_kem_keys():
        pk, sk = ML_KEM_512.keygen()
        return pk, sk

    @staticmethod
    def kem_encapsulate(pk):
        k, c = ML_KEM_512.encaps(pk)
        return k, c

    @staticmethod
    def kem_decapsulate(sk, c):
        k = ML_KEM_512.decaps(sk, c)
        return k

class AESCipher:
    @staticmethod
    def encrypt(key: bytes, plaintext: bytes) -> bytes:
        # AES-GCM requires 16, 24, or 32 byte keys. ML-KEM-512 outputs a 32 byte key.
        aesgcm = AESGCM(key)
        nonce = os.urandom(12)
        ciphertext = aesgcm.encrypt(nonce, plaintext, None)
        return nonce + ciphertext

    @staticmethod
    def decrypt(key: bytes, ciphertext_with_nonce: bytes) -> bytes:
        aesgcm = AESGCM(key)
        nonce = ciphertext_with_nonce[:12]
        ciphertext = ciphertext_with_nonce[12:]
        return aesgcm.decrypt(nonce, ciphertext, None)
