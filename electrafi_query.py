#!/usr/bin/env python3
"""
ElectraFi API Query Tool
Query and control your Rivian vehicle through the ElectraFi API.
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

try:
    import requests
except ImportError:
    print("ERROR: 'requests' library not found. Install with: pip install requests")
    sys.exit(1)

try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False


class ElectraFiAPI:
    """ElectraFi API client for Rivian vehicles."""
    
    BASE_URL = "https://www.electrafi.com/feed.php"
    
    def __init__(self, api_token: str, cache_dir: Optional[str] = None):
        """
        Initialize the ElectraFi API client.
        
        Args:
            api_token: Your ElectraFi API token
            cache_dir: Optional directory to cache responses
        """
        self.api_token = api_token
        self.cache_dir = Path(cache_dir) if cache_dir else None
        if self.cache_dir:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _make_request(self, command: str = "", use_bearer: bool = True) -> Dict[str, Any]:
        """
        Make a request to the ElectraFi API.
        
        Args:
            command: Optional command to send (empty for data query)
            use_bearer: Use Bearer token in header (recommended) vs query param
            
        Returns:
            JSON response as dictionary
        """
        try:
            if use_bearer:
                headers = {"Authorization": f"Bearer {self.api_token}"}
                params = {"command": command} if command else {}
                response = requests.get(self.BASE_URL, headers=headers, params=params, timeout=30)
            else:
                params = {"token": self.api_token, "command": command}
                response = requests.get(self.BASE_URL, params=params, timeout=30)
            
            response.raise_for_status()
            data = response.json()
            
            # Cache the response if caching is enabled
            if self.cache_dir:
                self._cache_response(data, command)
            
            return data
            
        except requests.exceptions.Timeout:
            raise Exception("Request timed out. The vehicle may be asleep.")
        except requests.exceptions.HTTPError as e:
            raise Exception(f"HTTP error: {e}")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Request failed: {e}")
        except json.JSONDecodeError:
            raise Exception("Invalid JSON response from API")
    
    def _cache_response(self, data: Dict[str, Any], command: str = ""):
        """Cache API response to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        cmd_suffix = f"_{command}" if command else "_data"
        filename = f"response{cmd_suffix}_{timestamp}.json"
        filepath = self.cache_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def get_vehicle_data(self) -> Dict[str, Any]:
        """
        Get all current vehicle data.
        
        Returns:
            Full vehicle data dictionary
        """
        return self._make_request()
    
    def send_command(self, command: str, dry_run: bool = True) -> Dict[str, Any]:
        """
        Send a command to the vehicle.
        
        Args:
            command: Command string to send
            dry_run: If True, only simulate the command (don't actually send)
            
        Returns:
            Command response dictionary
        """
        if dry_run:
            print(f"[DRY RUN] Would send command: {command}")
            return {"dry_run": True, "command": command}
        
        return self._make_request(command)


class VehicleDataExtractor:
    """Helper class to extract and format vehicle data."""
    
    def __init__(self, data: Dict[str, Any]):
        self.data = data
    
    def get_battery_status(self) -> Dict[str, Any]:
        """Extract battery-related information."""
        return {
            "battery_level": self.data.get("battery_level"),
            "usable_battery_level": self.data.get("usable_battery_level"),
            "battery_range_mi": self.data.get("battery_range"),
            "battery_range_km": self._mi_to_km(self.data.get("battery_range")),
            "est_battery_range_mi": self.data.get("est_battery_range"),
            "est_battery_range_km": self._mi_to_km(self.data.get("est_battery_range")),
            "charge_limit_soc": self.data.get("charge_limit_soc"),
        }
    
    def get_charging_status(self) -> Dict[str, Any]:
        """Extract charging-related information."""
        return {
            "charging_state": self.data.get("charging_state"),
            "charger_power_kw": self.data.get("charger_power"),
            "charger_phases": self.data.get("charger_phases"),
            "charge_current_request_a": self.data.get("charge_current_request"),
            "time_to_full_charge_h": self.data.get("time_to_full_charge"),
            "scheduled_charging_start_time": self.data.get("scheduled_charging_start_time"),
        }
    
    def get_location(self) -> Dict[str, Any]:
        """Extract location information."""
        return {
            "location_name": self.data.get("location"),
            "latitude": self.data.get("latitude"),
            "longitude": self.data.get("longitude"),
            "speed_kmh": self.data.get("speed"),
        }
    
    def get_thermal_status(self) -> Dict[str, Any]:
        """Extract temperature and climate information."""
        return {
            "inside_temp_c": self.data.get("inside_temp"),
            "outside_temp_c": self.data.get("outside_temp"),
            "driver_temp_setting_c": self.data.get("driver_temp_setting"),
            "seat_heater_left": self.data.get("seat_heater_left"),
            "seat_heater_right": self.data.get("seat_heater_right"),
            "seat_heater_rear_left": self.data.get("seat_heater_rear_left"),
            "seat_heater_rear_center": self.data.get("seat_heater_rear_center"),
            "seat_heater_rear_right": self.data.get("seat_heater_rear_right"),
            "steering_wheel_heater": self.data.get("steering_wheel_heater"),
        }
    
    def get_vehicle_info(self) -> Dict[str, Any]:
        """Extract basic vehicle information."""
        return {
            "display_name": self.data.get("display_name"),
            "vin": self.data.get("vin"),
            "state": self.data.get("state"),
            "car_state": self.data.get("carState"),
            "car_version": self.data.get("car_version"),
            "new_version": self.data.get("newVersion"),
            "new_version_status": self.data.get("newVersionStatus"),
            "odometer_mi": self.data.get("odometer"),
            "odometer_km": self._mi_to_km(self.data.get("odometer")),
            "last_update": self.data.get("Date"),
        }
    
    def get_command_counters(self) -> Optional[Dict[str, Any]]:
        """Extract command usage counters (only present in command responses)."""
        if "tesla_request_counter" in self.data:
            return self.data["tesla_request_counter"]
        return None
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of key vehicle metrics."""
        return {
            "vehicle": self.get_vehicle_info(),
            "battery": self.get_battery_status(),
            "charging": self.get_charging_status(),
            "location": self.get_location(),
            "thermal": self.get_thermal_status(),
            "command_counters": self.get_command_counters(),
        }
    
    @staticmethod
    def _mi_to_km(miles: Optional[float]) -> Optional[float]:
        """Convert miles to kilometers."""
        if miles is None:
            return None
        return round(float(miles) * 1.60934, 2)


class CommandBuilder:
    """Helper class to build and validate API commands."""
    
    @staticmethod
    def start_hvac() -> str:
        """Start HVAC system."""
        return "auto_conditioning_start"
    
    @staticmethod
    def stop_hvac() -> str:
        """Stop HVAC system."""
        return "auto_conditioning_stop"
    
    @staticmethod
    def set_temperature(temp_c: float) -> str:
        """
        Set cabin temperature.
        
        Args:
            temp_c: Temperature in Celsius (15-28)
        """
        if not 15 <= temp_c <= 28:
            raise ValueError("Temperature must be between 15 and 28 degrees Celsius")
        return f"set_temps&temp={temp_c}"
    
    @staticmethod
    def start_charging() -> str:
        """Start charging."""
        return "charge_start"
    
    @staticmethod
    def stop_charging() -> str:
        """Stop charging."""
        return "charge_stop"
    
    @staticmethod
    def set_charge_limit(percent: int) -> str:
        """
        Set charge limit.
        
        Args:
            percent: Charge limit percentage (50-100)
        """
        if not 50 <= percent <= 100:
            raise ValueError("Charge limit must be between 50 and 100 percent")
        return f"set_charge_limit&charge_limit_soc={percent}"
    
    @staticmethod
    def set_charge_amps(amps: int) -> str:
        """
        Set charging current.
        
        Args:
            amps: Charging current in amps (5-32)
        """
        if not 5 <= amps <= 32:
            raise ValueError("Charging current must be between 5 and 32 amps")
        return f"set_charging_amps&charging_amps={amps}"
    
    @staticmethod
    def set_seat_heater(seat: str, level: int) -> str:
        """
        Set seat heater level.
        
        Args:
            seat: Seat position (driver, passenger, rear_left, rear_center, rear_right)
            level: Heater level (0-3, 0 is off)
        """
        seat_map = {
            "driver": 0,
            "passenger": 1,
            "rear_left": 2,
            "rear_center": 4,
            "rear_right": 5,
        }
        
        if seat not in seat_map:
            raise ValueError(f"Invalid seat position. Must be one of: {', '.join(seat_map.keys())}")
        if not 0 <= level <= 3:
            raise ValueError("Heater level must be between 0 and 3")
        
        heater_id = seat_map[seat]
        return f"seat_heater&heater={heater_id}&level={level}"


def load_api_token() -> Optional[str]:
    """Load API token from environment or .env file."""
    # Try to load from .env file
    if DOTENV_AVAILABLE:
        load_dotenv()
    
    # Get token from environment
    return os.getenv("ELECTRAFI_API_TOKEN")


def main():
    parser = argparse.ArgumentParser(
        description="Query and control your Rivian vehicle through the ElectraFi API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument(
        "--token",
        help="ElectraFi API token (or set ELECTRAFI_API_TOKEN env var)",
    )
    parser.add_argument(
        "--cache-dir",
        default="./api_cache",
        help="Directory to cache API responses (default: ./api_cache)",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Disable response caching",
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Data query commands
    subparsers.add_parser("data", help="Get all vehicle data")
    subparsers.add_parser("battery", help="Get battery status")
    subparsers.add_parser("charging", help="Get charging status")
    subparsers.add_parser("location", help="Get location")
    subparsers.add_parser("thermal", help="Get thermal/climate status")
    subparsers.add_parser("info", help="Get vehicle info")
    subparsers.add_parser("summary", help="Get summary of key metrics")
    
    # HVAC commands
    hvac_start = subparsers.add_parser("hvac-start", help="Start HVAC")
    hvac_start.add_argument("--dry-run", action="store_true", default=True, help="Dry run mode (default)")
    hvac_start.add_argument("--execute", action="store_true", help="Actually execute the command")
    
    hvac_stop = subparsers.add_parser("hvac-stop", help="Stop HVAC")
    hvac_stop.add_argument("--dry-run", action="store_true", default=True, help="Dry run mode (default)")
    hvac_stop.add_argument("--execute", action="store_true", help="Actually execute the command")
    
    set_temp = subparsers.add_parser("set-temp", help="Set cabin temperature")
    set_temp.add_argument("temperature", type=float, help="Temperature in Celsius (15-28)")
    set_temp.add_argument("--dry-run", action="store_true", default=True, help="Dry run mode (default)")
    set_temp.add_argument("--execute", action="store_true", help="Actually execute the command")
    
    # Charging commands
    charge_start = subparsers.add_parser("charge-start", help="Start charging")
    charge_start.add_argument("--dry-run", action="store_true", default=True, help="Dry run mode (default)")
    charge_start.add_argument("--execute", action="store_true", help="Actually execute the command")
    
    charge_stop = subparsers.add_parser("charge-stop", help="Stop charging")
    charge_stop.add_argument("--dry-run", action="store_true", default=True, help="Dry run mode (default)")
    charge_stop.add_argument("--execute", action="store_true", help="Actually execute the command")
    
    set_limit = subparsers.add_parser("set-charge-limit", help="Set charge limit")
    set_limit.add_argument("percent", type=int, help="Charge limit percentage (50-100)")
    set_limit.add_argument("--dry-run", action="store_true", default=True, help="Dry run mode (default)")
    set_limit.add_argument("--execute", action="store_true", help="Actually execute the command")
    
    set_amps = subparsers.add_parser("set-charge-amps", help="Set charging current")
    set_amps.add_argument("amps", type=int, help="Charging current in amps (5-32)")
    set_amps.add_argument("--dry-run", action="store_true", default=True, help="Dry run mode (default)")
    set_amps.add_argument("--execute", action="store_true", help="Actually execute the command")
    
    # Seat heater command
    seat_heat = subparsers.add_parser("set-seat-heater", help="Set seat heater level")
    seat_heat.add_argument("seat", choices=["driver", "passenger", "rear_left", "rear_center", "rear_right"])
    seat_heat.add_argument("level", type=int, choices=[0, 1, 2, 3], help="Heater level (0=off, 3=max)")
    seat_heat.add_argument("--dry-run", action="store_true", default=True, help="Dry run mode (default)")
    seat_heat.add_argument("--execute", action="store_true", help="Actually execute the command")
    
    args = parser.parse_args()
    
    # Get API token
    api_token = args.token or load_api_token()
    if not api_token:
        print("ERROR: No API token provided. Set ELECTRAFI_API_TOKEN environment variable or use --token")
        sys.exit(1)
    
    # Initialize API client
    cache_dir = None if args.no_cache else args.cache_dir
    api = ElectraFiAPI(api_token, cache_dir)
    
    try:
        if not args.command:
            parser.print_help()
            sys.exit(0)
        
        # Handle data query commands
        if args.command in ["data", "battery", "charging", "location", "thermal", "info", "summary"]:
            data = api.get_vehicle_data()
            extractor = VehicleDataExtractor(data)
            
            if args.command == "data":
                result = data
            elif args.command == "battery":
                result = extractor.get_battery_status()
            elif args.command == "charging":
                result = extractor.get_charging_status()
            elif args.command == "location":
                result = extractor.get_location()
            elif args.command == "thermal":
                result = extractor.get_thermal_status()
            elif args.command == "info":
                result = extractor.get_vehicle_info()
            elif args.command == "summary":
                result = extractor.get_summary()
            
            print(json.dumps(result, indent=2))
        
        # Handle control commands
        else:
            dry_run = not args.execute
            
            if dry_run:
                print("=" * 60)
                print("DRY RUN MODE - No commands will be sent to the vehicle")
                print("Use --execute flag to actually send the command")
                print("=" * 60)
            else:
                print("=" * 60)
                print("WARNING: Sending command to vehicle!")
                print("This may wake the vehicle and consume API credits.")
                print("=" * 60)
                confirm = input("Are you sure you want to proceed? (yes/no): ")
                if confirm.lower() != "yes":
                    print("Command cancelled.")
                    sys.exit(0)
            
            # Build command
            cmd_builder = CommandBuilder()
            
            if args.command == "hvac-start":
                command = cmd_builder.start_hvac()
            elif args.command == "hvac-stop":
                command = cmd_builder.stop_hvac()
            elif args.command == "set-temp":
                command = cmd_builder.set_temperature(args.temperature)
            elif args.command == "charge-start":
                command = cmd_builder.start_charging()
            elif args.command == "charge-stop":
                command = cmd_builder.stop_charging()
            elif args.command == "set-charge-limit":
                command = cmd_builder.set_charge_limit(args.percent)
            elif args.command == "set-charge-amps":
                command = cmd_builder.set_charge_amps(args.amps)
            elif args.command == "set-seat-heater":
                command = cmd_builder.set_seat_heater(args.seat, args.level)
            
            result = api.send_command(command, dry_run=dry_run)
            print(json.dumps(result, indent=2))
            
    except ValueError as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
