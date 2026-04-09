"""
Navigation Security Module — Anti-GPS Spoofing
================================================
Simulates countermeasures against GPS spoofing attacks on drones.

Defense layers:
  1. IMU Cross-Validation  — Compare GPS position with Inertial Measurement Unit dead-reckoning
  2. Signal Strength Check — Genuine GPS signals have consistent, low power levels
  3. Multi-Constellation   — Cross-reference GPS, GLONASS, Galileo, BeiDou
  4. Position Sanity Check — Reject physically impossible position jumps
  5. Geofence Enforcement  — Reject positions outside pre-defined mission boundaries
"""

import math
import time
import random


class GPSModule:
    """Simulated GPS module with anti-spoofing capabilities."""

    # Maximum plausible drone speed (m/s) — ~200 km/h for a military drone
    MAX_SPEED_MS = 55.0

    # Acceptable GPS signal strength range (dBm) — genuine signals are typically -125 to -165 dBm
    GENUINE_SIGNAL_RANGE = (-165, -125)

    # Spoofed signals are typically much stronger (closer to transmitter)
    SPOOF_SIGNAL_THRESHOLD = -100  # dBm — signals stronger than this are suspicious

    # Supported constellations for cross-referencing
    CONSTELLATIONS = ["GPS", "GLONASS", "GALILEO", "BEIDOU"]

    def __init__(self, mission_bounds: dict = None):
        """
        Args:
            mission_bounds: dict with keys 'lat_min', 'lat_max', 'lon_min', 'lon_max'
                           defining the geofence for this mission.
        """
        self.last_position = None
        self.last_time = None
        self.imu_position = None  # Dead-reckoning position from IMU
        self.spoof_alert_count = 0
        self.total_fixes = 0
        self.rejected_fixes = 0

        # Default mission bounds (India, roughly around Delhi)
        self.mission_bounds = mission_bounds or {
            "lat_min": 28.0,
            "lat_max": 29.0,
            "lon_min": 76.5,
            "lon_max": 78.0,
        }

        print("[NAV] Anti-GPS Spoofing Module Initialized")
        print(f"[NAV]   Max speed threshold: {self.MAX_SPEED_MS} m/s ({self.MAX_SPEED_MS * 3.6:.0f} km/h)")
        print(f"[NAV]   Signal strength window: {self.GENUINE_SIGNAL_RANGE[0]} to {self.GENUINE_SIGNAL_RANGE[1]} dBm")
        print(f"[NAV]   Spoof detection threshold: > {self.SPOOF_SIGNAL_THRESHOLD} dBm")
        print(f"[NAV]   Geofence: Lat [{self.mission_bounds['lat_min']}-{self.mission_bounds['lat_max']}], "
              f"Lon [{self.mission_bounds['lon_min']}-{self.mission_bounds['lon_max']}]")
        print(f"[NAV]   Multi-constellation: {', '.join(self.CONSTELLATIONS)}")

    def validate_gps_fix(self, lat: float, lon: float, alt: float,
                         signal_dbm: float, constellation_data: dict = None,
                         imu_lat: float = None, imu_lon: float = None) -> dict:
        """
        Validate a GPS fix against multiple anti-spoofing checks.

        Returns:
            dict with keys:
                'valid': bool — whether the fix passed all checks
                'checks': dict — result of each individual check
                'alerts': list — list of alert strings
        """
        self.total_fixes += 1
        current_time = time.time()
        alerts = []
        checks = {}

        # ── Check 1: Signal Strength ──
        signal_valid = self.GENUINE_SIGNAL_RANGE[0] <= signal_dbm <= self.GENUINE_SIGNAL_RANGE[1]
        signal_suspicious = signal_dbm > self.SPOOF_SIGNAL_THRESHOLD
        checks["signal_strength"] = {
            "passed": signal_valid and not signal_suspicious,
            "value_dbm": signal_dbm,
            "reason": ""
        }
        if signal_suspicious:
            checks["signal_strength"]["reason"] = (
                f"Signal too strong ({signal_dbm} dBm > {self.SPOOF_SIGNAL_THRESHOLD} dBm) — "
                f"possible spoofing transmitter nearby"
            )
            alerts.append(f"🛰️ SPOOF ALERT: Abnormally strong GPS signal ({signal_dbm} dBm)")

        # ── Check 2: Position Sanity (speed check) ──
        speed_valid = True
        computed_speed = 0.0
        if self.last_position and self.last_time:
            dt = current_time - self.last_time
            if dt > 0:
                dist = self._haversine(self.last_position[0], self.last_position[1], lat, lon)
                computed_speed = dist / dt
                if computed_speed > self.MAX_SPEED_MS:
                    speed_valid = False
                    alerts.append(
                        f"🛰️ SPOOF ALERT: Impossible speed detected ({computed_speed:.1f} m/s = "
                        f"{computed_speed * 3.6:.0f} km/h > {self.MAX_SPEED_MS * 3.6:.0f} km/h max)"
                    )
        checks["position_sanity"] = {
            "passed": speed_valid,
            "speed_ms": round(computed_speed, 2),
            "max_allowed_ms": self.MAX_SPEED_MS,
            "reason": "" if speed_valid else "Position jump exceeds maximum drone speed"
        }

        # ── Check 3: Geofence ──
        inside_fence = (
            self.mission_bounds["lat_min"] <= lat <= self.mission_bounds["lat_max"] and
            self.mission_bounds["lon_min"] <= lon <= self.mission_bounds["lon_max"]
        )
        checks["geofence"] = {
            "passed": inside_fence,
            "lat": lat,
            "lon": lon,
            "reason": "" if inside_fence else "Position outside mission geofence boundaries"
        }
        if not inside_fence:
            alerts.append(f"🛰️ SPOOF ALERT: GPS position ({lat}, {lon}) outside geofence!")

        # ── Check 4: IMU Cross-Validation ──
        imu_valid = True
        imu_deviation = 0.0
        if imu_lat is not None and imu_lon is not None:
            imu_deviation = self._haversine(imu_lat, imu_lon, lat, lon)
            # Allow up to 50m deviation between IMU and GPS
            if imu_deviation > 50.0:
                imu_valid = False
                alerts.append(
                    f"🛰️ SPOOF ALERT: GPS-IMU mismatch — deviation {imu_deviation:.1f}m (max 50m)"
                )
        checks["imu_cross_validation"] = {
            "passed": imu_valid,
            "deviation_m": round(imu_deviation, 2),
            "max_deviation_m": 50.0,
            "reason": "" if imu_valid else f"IMU deviation too large: {imu_deviation:.1f}m"
        }

        # ── Check 5: Multi-Constellation Agreement ──
        constellation_valid = True
        if constellation_data:
            agreeing = sum(1 for c in constellation_data.values() if c.get("available", False))
            total = len(constellation_data)
            if agreeing < 2:
                constellation_valid = False
                alerts.append(
                    f"🛰️ SPOOF ALERT: Only {agreeing}/{total} constellations available — "
                    f"possible selective spoofing"
                )
        checks["multi_constellation"] = {
            "passed": constellation_valid,
            "reason": "" if constellation_valid else "Insufficient constellation agreement"
        }

        # ── Final Verdict ──
        all_passed = all(c["passed"] for c in checks.values())
        if not all_passed:
            self.spoof_alert_count += 1
            self.rejected_fixes += 1

        # Update state for next check
        self.last_position = (lat, lon)
        self.last_time = current_time

        return {
            "valid": all_passed,
            "checks": checks,
            "alerts": alerts,
            "stats": {
                "total_fixes": self.total_fixes,
                "rejected_fixes": self.rejected_fixes,
                "spoof_alerts": self.spoof_alert_count,
            }
        }

    @staticmethod
    def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two GPS points in meters."""
        R = 6371000  # Earth radius in meters
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def demo_anti_gps_spoofing():
    """Demonstrate the Anti-GPS Spoofing system."""
    print("\n" + "=" * 60)
    print("  🛰️ ANTI-GPS SPOOFING DEFENSE DEMO")
    print("=" * 60)

    gps = GPSModule()

    # Test 1: Legitimate GPS fix
    print("\n--- Test 1: Legitimate GPS Fix ---")
    result = gps.validate_gps_fix(
        lat=28.5, lon=77.2, alt=350,
        signal_dbm=-135,
        imu_lat=28.5001, imu_lon=77.2001,
        constellation_data={
            "GPS": {"available": True}, "GLONASS": {"available": True},
            "GALILEO": {"available": True}, "BEIDOU": {"available": False},
        }
    )
    _print_result("Legitimate Fix", result)

    time.sleep(0.1)

    # Test 2: Spoofed signal (too strong)
    print("\n--- Test 2: Spoofed Signal (abnormally strong) ---")
    result = gps.validate_gps_fix(
        lat=28.501, lon=77.201, alt=350,
        signal_dbm=-50,  # Way too strong — spoofer is nearby
        imu_lat=28.501, imu_lon=77.201,
        constellation_data={
            "GPS": {"available": True}, "GLONASS": {"available": True},
            "GALILEO": {"available": True}, "BEIDOU": {"available": True},
        }
    )
    _print_result("Spoofed Signal", result)

    time.sleep(0.1)

    # Test 3: Position teleportation (impossible speed)
    print("\n--- Test 3: Position Teleportation Attack ---")
    result = gps.validate_gps_fix(
        lat=40.0, lon=77.2, alt=350,  # Jumped from 28.5 to 40.0 latitude instantly
        signal_dbm=-140,
        imu_lat=28.502, imu_lon=77.202,
    )
    _print_result("Teleportation Attack", result)

    time.sleep(0.1)

    # Test 4: Outside geofence
    print("\n--- Test 4: Geofence Violation ---")
    result = gps.validate_gps_fix(
        lat=35.0, lon=85.0, alt=350,  # Way outside mission area
        signal_dbm=-140,
        imu_lat=35.0, imu_lon=85.0,
    )
    _print_result("Geofence Violation", result)

    print(f"\n[NAV] Summary: {gps.total_fixes} fixes processed, "
          f"{gps.rejected_fixes} rejected, {gps.spoof_alert_count} spoof alerts")
    print("=" * 60)
    print("  ANTI-GPS SPOOFING DEMO COMPLETE")
    print("=" * 60)


def _print_result(test_name: str, result: dict):
    status = "[OK] ACCEPTED" if result["valid"] else "[X] REJECTED"
    print(f"  Result: {status}")
    for name, check in result["checks"].items():
        icon = "[OK]" if check["passed"] else "[X]"
        print(f"    {icon} {name}: {check.get('reason') or 'OK'}")
    for alert in result["alerts"]:
        print(f"    {alert}")
