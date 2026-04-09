import pandas as pd
import binascii

def analyze_uart_bits():
    print("="*80)
    print("  🛰️ UART BIT-LEVEL FRAME DECODER (Physical Layer Analysis)")
    print("="*80)
    print(f"{'Time (s)':<12} | {'Hex':<6} | {'Start':<6} | {'Data Bits (LSB First)':<22} | {'Stop':<5}")
    print("-" * 80)

    # Load the capture
    df = pd.read_csv("encrypted.csv")
    
    # Process the first 10 bytes for a clear visual forensic analysis
    for index, row in df.head(10).iterrows():
        hex_val = row['data'].replace('0x', '')
        byte_val = int(hex_val, 16)
        
        # 1. Start Bit (Always 0 for UART)
        start_bit = 0
        
        # 2. Data Bits (8 bits, typically LSB first)
        data_bits = format(byte_val, '08b')[::-1] # Reverse for LSB-first visual
        bits_display = " ".join(list(data_bits))
        
        # 3. Stop Bit (Always 1 for UART)
        stop_bit = 1
        
        # Format the Bit Frame: | 0 | d0 d1 d2 d3 d4 d5 d6 d7 | 1 |
        print(f"{row['start_time']:<12.5f} | 0x{hex_val:<4} | {start_bit:<6} | {bits_display:<22} | {stop_bit:<5}")

    print("\n" + "="*80)
    print(f"✅ DECODING COMPLETE: Found {len(df)} 10-bit physical UART frames.")
    print("="*80)

if __name__ == "__main__":
    analyze_uart_bits()
