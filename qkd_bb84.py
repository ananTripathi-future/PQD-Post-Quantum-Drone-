"""
Quantum Key Distribution (QKD) — BB84 Protocol Simulation
=========================================================
Simulates the BB84 Quantum Key Distribution protocol and the No-Cloning Theorem.

How it works:
1. Sender (Alice) sends photons in random quantum states.
2. If an attacker (Eve) tries to copy/intercept them, the No-Cloning Theorem enforces 
   that she CANNOT copy the quantum state perfectly.
3. Eve is forced to measure the photon, which alters its state (collapses the waveform).
4. Alice and Bob check for errors; Eve's measurements introduce a ~25% error rate.
5. If the error rate is high, eavesdropping is detected 🚨 and key exchange aborts!
"""

import random
import hashlib

class QKDBB84:
    def __init__(self, num_bits=512):
        self.num_bits = num_bits
        
    def generate_random_bits(self, length):
        return [random.choice([0, 1]) for _ in range(length)]
        
    def generate_random_bases(self, length):
        # 0 represents Rectilinear base (+), 1 represents Diagonal base (x)
        return [random.choice([0, 1]) for _ in range(length)]
        
    def encode_qubits(self, bits, bases):
        """Simulate sending polarized photons."""
        qubits = []
        for bit, base in zip(bits, bases):
            qubits.append({'bit': bit, 'base': base})
        return qubits
        
    def intercept_and_measure(self, qubits):
        """
        Simulate Eve intercepting the qubits.
        Due to No-cloning theorem, Eve cannot copy the qubits.
        She measures them using random bases, which alters the quantum state.
        """
        eve_bases = self.generate_random_bases(len(qubits))
        intercepted_qubits = []
        
        for i, qubit in enumerate(qubits):
            eve_base = eve_bases[i]
            if eve_base == qubit['base']:
                measured_bit = qubit['bit']
            else:
                measured_bit = random.choice([0, 1])
            intercepted_qubits.append({'bit': measured_bit, 'base': eve_base})
            
        return intercepted_qubits
        
    def measure_qubits(self, qubits, measurement_bases):
        """Simulate Bob measuring the received photons."""
        measured_bits = []
        for i, qubit in enumerate(qubits):
            if measurement_bases[i] == qubit['base']:
                measured_bits.append(qubit['bit'])
            else:
                measured_bits.append(random.choice([0, 1]))
        return measured_bits
        
    def filter_matching_bases(self, bases1, bases2, bits):
        """Keep only the bits where Alice and Bob used the same base."""
        return [bits[i] for i in range(len(bases1)) if bases1[i] == bases2[i]]
        
    def estimate_error_rate(self, alice_key, bob_key, sample_size):
        """Compare a subset of the key to detect eavesdropping."""
        if len(alice_key) < sample_size:
            sample_size = len(alice_key)
            
        if sample_size == 0:
            return 1.0
            
        errors = sum(1 for i in range(sample_size) if alice_key[i] != bob_key[i])
        return errors / sample_size

    def hash_key(self, key_bits):
        """Convert a list of bits into a 256-bit AES key (32 bytes)."""
        bit_string = ''.join(str(b) for b in key_bits)
        return hashlib.sha256(bit_string.encode()).digest()


def simulate_qkd_exchange(eve_present=False):
    qkd = QKDBB84(num_bits=1024)
    
    # 1. Alice generates bits and bases
    alice_bits = qkd.generate_random_bits(qkd.num_bits)
    alice_bases = qkd.generate_random_bases(qkd.num_bits)
    
    # 2. Alice encodes qubits
    qubits_sent = qkd.encode_qubits(alice_bits, alice_bases)
    print(f"  [QKD-Alice] Generated {qkd.num_bits} quantum bits (photons).")
    print(f"  [QKD-Alice] Transmitting via optical quantum channel...")
    
    # 3. Interception? 
    if eve_present:
        print(f"\n  [ALERT] Attacker (Eve) intercepted the quantum beam!")
        print(f"  [Attacker] Attempting to copy photons... FAILED (No-Cloning Theorem)")
        print(f"  [Attacker] Forced to measure photons, collapsing their quantum states.")
        qubits_received = qkd.intercept_and_measure(qubits_sent)
    else:
        qubits_received = qubits_sent
        
    # 4. Bob measures
    bob_bases = qkd.generate_random_bases(qkd.num_bits)
    bob_bits = qkd.measure_qubits(qubits_received, bob_bases)
    print(f"  [QKD-Bob] Received photons and measured using random bases.")
    
    # 5. Public discussion: compare bases
    print(f"  [QKD-Public] Alice and Bob compare measurement bases (sifting).")
    alice_sifted_key = qkd.filter_matching_bases(alice_bases, bob_bases, alice_bits)
    bob_sifted_key = qkd.filter_matching_bases(alice_bases, bob_bases, bob_bits)
    
    print(f"  [QKD-System] {len(alice_sifted_key)} bits kept after basis reconciliation.")
    
    # 6. Error estimation
    sample_size = min(100, len(alice_sifted_key) // 2)
    error_rate = qkd.estimate_error_rate(alice_sifted_key, bob_sifted_key, sample_size)
    print(f"  [QKD-System] Checking {sample_size} bits for Quantum Bit Error Rate (QBER)...")
    print(f"  [QKD-System] Error rate detected: {error_rate * 100:.1f}%")
    
    if error_rate > 0.11: # Standard BB84 threshold is ~11%
        print(f"  [CRITICAL] QKD COMPROMISED! Eavesdropping detected.")
        return False, None
    else:
        print(f"  [OK] Error rate is within safe limits (No eavesdropping).")
        
        # Hash the remaining bits to form a 256-bit AES key
        final_key = qkd.hash_key(alice_sifted_key[sample_size:])
        return True, final_key
