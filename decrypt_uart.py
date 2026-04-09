import pandas as pd
import json
import binascii
from drone import Drone
from crypto_utils import AESCipher, PQCrypto

def run_decryption_scan():
    print("="*60)
    print("  🛰️ POST-QUANTUM UART DECRYPTION ENGINE")
    print("="*60)

    # 1. Initialize the Drone (Loads HSM and PQC Keys)
    drone = Drone()
    
    # 2. Load the Captured Dataset
    print("\n[Step 1] Loading UART Capture (encrypted.csv)...")
    df = pd.read_csv("encrypted.csv")
    raw_hex = df['data'].str.replace('0x', '').tolist()
    raw_bytes = binascii.unhexlify("".join(raw_hex))

    # 3. Packet Slicing (Based on your detected fixed header)
    # The Capture looks fragmented. We look for the envelope start.
    print(f"[Step 2] Slicing {len(raw_bytes)} bytes into encrypted envelopes...")
    
    # In your Qore capture, let's assume each command packet is 64 bytes
    packet_size = 64 
    packets = [raw_bytes[i:i+packet_size] for i in range(0, len(raw_bytes), packet_size)]

    print(f"[Step 3] Processing {len(packets)} potential command packets...")

    for i, packet in enumerate(packets[:5]):  # Process first 5 for the demo
        print(f"\n--- Packet #{i+1} [Offset: {i*packet_size}] ---")
        try:
            # Attempting full 12-layer decryption and verification
            # Note: This requires the session key to match the one used during capture.
            result = drone.process_command(packet)
            
            if result:
                print(f"✅ DECRYPTION SUCCESSFUL: Command authorized and executed.")
            else:
                print(f"❌ DECRYPTION FAILED: Invalid signature or session key mismatch.")
        except Exception as e:
            print(f"⚠️ PACKET ERROR: {str(e)}")

    print("\n" + "="*60)
    print("  DECRYPTION SCAN COMPLETE")
    print("="*60)

if __name__ == "__main__":
    run_decryption_scan()
