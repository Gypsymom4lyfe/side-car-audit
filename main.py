from sidecar_engine import SidecarEngine


if __name__ == "__main__":
    print("Initializing Sovereign Sidecar Engine...")
    engine = SidecarEngine("baseline.json")

    print("\n--- Testing Clean Stream Packet ---")
    engine.inspect_stream_packet({"id": 101, "status": "active", "value": 45})

    print("\n--- Testing Tampered Stream Packet ---")
    engine.inspect_stream_packet({"id": 102, "status": "active", "value": 999})
