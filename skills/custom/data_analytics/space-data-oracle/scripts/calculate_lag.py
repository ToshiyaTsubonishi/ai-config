import json
import random

def get_telemetry():
    # Simulate distance (km) and light lag (seconds)
    # Earth to Moon: ~384,400 km
    dist_moon = 384400 + random.randint(-1000, 1000)
    lag_moon = round(dist_moon / 299792.458, 3) # Speed of light
    
    # Earth to Mars: ~225 million km (avg)
    dist_mars = 225000000 + random.randint(-500000, 500000)
    lag_mars = round(dist_mars / 299792.458, 3)

    return {
        "moon": {"distance_km": dist_moon, "lag_sec": lag_moon, "status": "Connected"},
        "mars": {"distance_km": dist_mars, "lag_sec": lag_mars, "status": "High Latency"},
        "leo": {"distance_km": 400, "lag_sec": 0.001, "status": "Realtime"}
    }

if __name__ == "__main__":
    print(json.dumps(get_telemetry(), indent=2))

