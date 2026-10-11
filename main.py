from sidecar_engine import SidecarEngine

if __name__ == "__main__":
    print("Initializing Sovereign Sidecar Engine...")
    engine = SidecarEngine("baseline.json")

    # Simulate and assert a clean data stream packet
    print("\n--- Testing Clean Stream Packet ---")
    clean_packet = {"id": 101, "status": "active", "value": 45}
    assert engine.inspect_stream_packet(clean_packet) is True, "Error: Clean packet failed verification!"

    # Simulate and assert a tampered/drifted packet (value outside allowed bounds)
    print("\n--- Testing Tampered Stream Packet ---")
    drift_packet = {"id": 102, "status": "active", "value": 999}
    assert engine.inspect_stream_packet(drift_packet) is False, "Error: Tampered packet was incorrectly marked clean!"

    print("\n[+] All verification assertions passed successfully. Sidecar protocol functioning as designed.")
