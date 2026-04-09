"""
Communication Security Module — Frequency Hopping & Anti-Jamming
=================================================================
Simulates military-grade frequency hopping spread spectrum (FHSS) for
anti-jamming protection during drone communication.

How it works:
  1. Both transmitter and drone share a PRNG seed derived from the ML-KEM shared key
  2. The hopping sequence is deterministic (both sides compute the same sequence)
  3. Each transmission hops to a pseudo-random channel
  4. If a channel is detected as jammed, it skips to the next in the sequence
  5. An attacker would need the shared key to predict the sequence
"""

import hashlib
import time
import random


class FrequencyHopper:
    """
    Frequency Hopping Spread Spectrum (FHSS) simulation.

    Uses the post-quantum shared key as a seed to generate a deterministic
    hopping sequence. Both transmitter and drone compute the same sequence,
    so they always know which channel to use.
    """

    # Simulated frequency bands available (MHz)
    FREQ_BANDS = [
        902.1, 903.3, 904.7, 905.9, 907.2,
        908.5, 910.1, 911.4, 912.8, 914.0,
        915.3, 916.7, 918.0, 919.4, 920.6,
        921.9, 923.2, 924.5, 925.8, 927.1,
        928.3, 929.6, 930.9, 932.1, 933.4,
        934.7, 936.0, 937.3, 938.6, 939.9,
        941.2, 942.5, 943.8, 945.1, 946.4,
        947.7, 949.0, 950.3, 951.6, 952.9,
    ]

    # Hop rate: Number of hops per second (military typically 100-1000)
    HOP_RATE = 200  # hops/second

    def __init__(self, shared_key: bytes, label: str = "Node"):
        self.label = label
        # Derive a PRNG seed from the shared key
        seed_hash = hashlib.sha256(shared_key + b"FHSS_SEED").digest()
        self.seed = int.from_bytes(seed_hash[:8], 'big')
        self._rng = random.Random(self.seed)
        self._hop_index = 0
        self._hopping_sequence = self._generate_sequence(256)
        self._jammed_channels = set()

        print(f"[{self.label}] FHSS Initialized — Seed derived from post-quantum shared key")
        print(f"[{self.label}]   Bands available: {len(self.FREQ_BANDS)}")
        print(f"[{self.label}]   Hop rate: {self.HOP_RATE} hops/sec")
        print(f"[{self.label}]   Sequence length: {len(self._hopping_sequence)} channels")

    def _generate_sequence(self, length: int) -> list:
        """Generate a deterministic pseudo-random hopping sequence."""
        sequence = []
        for _ in range(length):
            idx = self._rng.randint(0, len(self.FREQ_BANDS) - 1)
            sequence.append(self.FREQ_BANDS[idx])
        return sequence

    def get_current_channel(self) -> float:
        """Get the current channel frequency based on the hopping sequence."""
        freq = self._hopping_sequence[self._hop_index % len(self._hopping_sequence)]

        # If current channel is jammed, skip to next
        attempts = 0
        while freq in self._jammed_channels and attempts < len(self.FREQ_BANDS):
            self._hop_index += 1
            freq = self._hopping_sequence[self._hop_index % len(self._hopping_sequence)]
            attempts += 1

        return freq

    def hop(self) -> float:
        """Advance to the next channel in the hopping sequence. Returns the new frequency."""
        self._hop_index += 1
        return self.get_current_channel()

    def report_jammed(self, frequency: float):
        """Report a channel as jammed — it will be skipped in future hops."""
        self._jammed_channels.add(frequency)
        print(f"[{self.label}] ⚠️ Channel {frequency} MHz reported JAMMED — Blacklisted")

    def clear_jam_reports(self):
        """Clear all jammed channel reports (periodic refresh)."""
        self._jammed_channels.clear()

    def get_status(self) -> dict:
        return {
            "hop_index": self._hop_index,
            "current_freq": self.get_current_channel(),
            "hop_rate": self.HOP_RATE,
            "total_bands": len(self.FREQ_BANDS),
            "jammed_count": len(self._jammed_channels),
            "jammed_channels": list(self._jammed_channels),
        }


class SecureTransmitter:
    """
    Secure transmission layer combining frequency hopping with
    transmission integrity checks.
    """

    def __init__(self, shared_key: bytes, label: str = "TX"):
        self.hopper = FrequencyHopper(shared_key, label)
        self.label = label
        self.tx_count = 0
        self._packet_hashes = set()  # Track sent packet hashes for dedup

    def transmit(self, payload_size: int) -> dict:
        """
        Simulate a secure transmission on the current hopping channel.
        Returns transmission metadata.
        """
        self.tx_count += 1
        channel = self.hopper.get_current_channel()

        # Compute transmission metadata
        tx_record = {
            "tx_id": self.tx_count,
            "channel_mhz": channel,
            "hop_index": self.hopper._hop_index,
            "payload_bytes": payload_size,
            "timestamp": time.time(),
            "protocol": "FHSS-OFDM",
            "modulation": "QPSK",
            "spread_factor": 128,
        }

        print(f"[{self.label}] TX #{self.tx_count} on {channel} MHz "
              f"({payload_size} bytes) — FHSS hop #{self.hopper._hop_index}")

        # Hop to next channel after transmission
        self.hopper.hop()

        return tx_record

    def receive(self, payload_size: int) -> dict:
        """Simulate receiving on the synchronized hopping channel."""
        channel = self.hopper.get_current_channel()

        rx_record = {
            "channel_mhz": channel,
            "hop_index": self.hopper._hop_index,
            "payload_bytes": payload_size,
            "timestamp": time.time(),
            "signal_strength_dbm": random.randint(-65, -30),
            "bit_error_rate": round(random.uniform(0.0, 0.001), 6),
        }

        print(f"[{self.label}] RX on {channel} MHz "
              f"({payload_size} bytes) — Signal: {rx_record['signal_strength_dbm']} dBm")

        # Hop to next channel after reception
        self.hopper.hop()

        return rx_record


def demo_frequency_hopping(shared_key: bytes):
    """Demonstrate the frequency hopping system."""
    print("\n" + "=" * 60)
    print("  📡 FREQUENCY HOPPING SPREAD SPECTRUM (FHSS) DEMO")
    print("=" * 60)

    tx = SecureTransmitter(shared_key, "Controller-TX")
    rx = SecureTransmitter(shared_key, "Drone-RX")

    print("\n--- Synchronized Hopping Sequence (first 10 hops) ---")
    for i in range(10):
        tx_ch = tx.hopper.get_current_channel()
        rx_ch = rx.hopper.get_current_channel()
        match = "[OK] SYNC" if tx_ch == rx_ch else "[X] MISMATCH"
        print(f"  Hop {i+1}: TX={tx_ch} MHz | RX={rx_ch} MHz | {match}")
        tx.hopper.hop()
        rx.hopper.hop()

    # Reset for demo
    tx = SecureTransmitter(shared_key, "Controller-TX")
    rx = SecureTransmitter(shared_key, "Drone-RX")

    print("\n--- Simulated Transmission (3 commands) ---")
    for i in range(3):
        size = random.randint(128, 512)
        tx_meta = tx.transmit(size)
        rx_meta = rx.receive(size)
        print(f"  -> TX channel: {tx_meta['channel_mhz']} MHz | "
              f"RX channel: {rx_meta['channel_mhz']} MHz\n")

    # Simulate jamming attack
    print("\n--- Jamming Attack Simulation ---")
    jam_freq = tx.hopper.get_current_channel()
    print(f"[Attacker] Jamming frequency {jam_freq} MHz...")
    tx.hopper.report_jammed(jam_freq)
    rx.hopper.report_jammed(jam_freq)
    new_ch = tx.hopper.get_current_channel()
    print(f"[System] Auto-hopped to {new_ch} MHz — Jamming evaded [OK]")

    print("\n" + "=" * 60)
    print("  FHSS DEMO COMPLETE — Anti-jamming active")
    print("=" * 60)
