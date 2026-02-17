#!/usr/bin/env python3
"""
ElectraFi Charging History Analyzer
Analyze historical charging data from ElectraFi API
"""

import argparse
import json
import sys
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from typing import Optional, Dict, Any, List

try:
    import requests
except ImportError:
    print("ERROR: 'requests' library not found. Install with: pip install requests")
    sys.exit(1)

try:
    from dotenv import load_dotenv
    import os
    load_dotenv()
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False
    import os


class ChargingHistoryAPI:
    """ElectraFi Charging History API client."""
    
    HISTORY_URL = "https://www.electrafi.com/history.php"
    
    def __init__(self, api_token: str):
        self.api_token = api_token
    
    def get_charges(self, date_from: str, date_to: str) -> Dict[str, Any]:
        """
        Get charging history for a date range.
        
        Args:
            date_from: Start date (YYYY-MM-DD)
            date_to: End date (YYYY-MM-DD)
            
        Returns:
            JSON response with charging data
        """
        headers = {"Authorization": f"Bearer {self.api_token}"}
        params = {
            "command": "charges",
            "dateFrom": date_from,
            "dateTo": date_to
        }
        
        try:
            response = requests.get(self.HISTORY_URL, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"API request failed: {e}")
        except json.JSONDecodeError:
            raise Exception("Invalid JSON response from API")


class ChargingAnalyzer:
    """Analyze charging session data."""
    
    def __init__(self, data: Dict[str, Any]):
        self.data = data
        self.results = data.get("results", [])
    
    def filter_home_charges(self) -> List[Dict[str, Any]]:
        """Filter for home charging sessions only."""
        return [charge for charge in self.results if charge.get("homeChargeFlag") == 1]
    
    def calculate_home_summary(self) -> Dict[str, Any]:
        """Calculate summary statistics for home charging."""
        home_charges = self.filter_home_charges()
        
        if not home_charges:
            return {
                "total_sessions": 0,
                "total_kwh": 0,
                "total_cost": 0,
                "final_odometer_mi": None,
                "final_odometer_km": None,
                "date_from": self.data.get("dateFrom"),
                "date_to": self.data.get("dateTo"),
            }
        
        total_kwh = sum(float(charge.get("totalEnergyAdded", 0) or 0) for charge in home_charges)
        total_cost = sum(float(charge.get("homeCost", 0) or 0) for charge in home_charges)
        
        # Sort by date to get the last charge
        sorted_charges = sorted(home_charges, key=lambda x: x.get("date", ""))
        last_charge = sorted_charges[-1] if sorted_charges else None
        
        final_odo_mi = float(last_charge.get("odometer", 0)) if last_charge else None
        final_odo_km = final_odo_mi * 1.60934 if final_odo_mi else None
        
        return {
            "total_sessions": len(home_charges),
            "total_kwh": round(total_kwh, 2),
            "total_cost": round(total_cost, 2),
            "avg_cost_per_kwh": round(total_cost / total_kwh, 4) if total_kwh > 0 else 0,
            "final_odometer_mi": round(final_odo_mi, 1) if final_odo_mi else None,
            "final_odometer_km": round(final_odo_km, 1) if final_odo_km else None,
            "last_charge_date": last_charge.get("date") if last_charge else None,
            "date_from": self.data.get("dateFrom"),
            "date_to": self.data.get("dateTo"),
        }
    
    def calculate_all_charging_summary(self) -> Dict[str, Any]:
        """Calculate summary for all charging (home + away)."""
        if not self.results:
            return {
                "total_sessions": 0,
                "home_sessions": 0,
                "away_sessions": 0,
            }
        
        home_charges = self.filter_home_charges()
        away_charges = [c for c in self.results if c.get("homeChargeFlag") != 1]
        
        total_kwh_all = sum(float(c.get("totalEnergyAdded", 0) or 0) for c in self.results)
        total_kwh_home = sum(float(c.get("totalEnergyAdded", 0) or 0) for c in home_charges)
        total_kwh_away = sum(float(c.get("totalEnergyAdded", 0) or 0) for c in away_charges)
        
        total_cost_home = sum(float(c.get("homeCost", 0) or 0) for c in home_charges)
        total_cost_super = sum(float(c.get("superCost", 0) or 0) for c in self.results)
        total_cost_travel = sum(float(c.get("travelCost", 0) or 0) for c in self.results)
        
        return {
            "total_sessions": len(self.results),
            "home_sessions": len(home_charges),
            "away_sessions": len(away_charges),
            "total_kwh_all": round(total_kwh_all, 2),
            "total_kwh_home": round(total_kwh_home, 2),
            "total_kwh_away": round(total_kwh_away, 2),
            "total_cost_home": round(total_cost_home, 2),
            "total_cost_super": round(total_cost_super, 2),
            "total_cost_travel": round(total_cost_travel, 2),
            "total_cost_all": round(total_cost_home + total_cost_super + total_cost_travel, 2),
        }
    
    def get_charging_details(self, home_only: bool = False) -> List[Dict[str, Any]]:
        """Get detailed list of charging sessions."""
        charges = self.filter_home_charges() if home_only else self.results
        
        details = []
        for charge in charges:
            details.append({
                "date": charge.get("date"),
                "location": charge.get("locationName"),
                "kwh_added": float(charge.get("totalEnergyAdded", 0) or 0),
                "cost": float(charge.get("homeCost", 0) or 0) if charge.get("homeChargeFlag") == 1 else 
                        float(charge.get("superCost", 0) or 0) + float(charge.get("travelCost", 0) or 0),
                "start_percent": float(charge.get("startPercent", 0) or 0),
                "charge_percent": charge.get("chargePercent"),
                "duration_min": charge.get("totalMinutes"),
                "avg_power_kw": float(charge.get("avgChargerPower", 0) or 0),
                "odometer_mi": round(float(charge.get("odometer", 0)), 1),
                "is_home": charge.get("homeChargeFlag") == 1,
            })
        
        return details


def get_last_complete_month() -> tuple[str, str]:
    """Get the first and last day of the previous month."""
    today = date.today()
    # First day of current month
    first_of_this_month = date(today.year, today.month, 1)
    # Last day of previous month
    last_of_last_month = first_of_this_month - relativedelta(days=1)
    # First day of previous month
    first_of_last_month = date(last_of_last_month.year, last_of_last_month.month, 1)
    
    return first_of_last_month.strftime("%Y-%m-%d"), last_of_last_month.strftime("%Y-%m-%d")


def main():
    parser = argparse.ArgumentParser(
        description="Analyze ElectraFi charging history",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument(
        "--token",
        help="ElectraFi API token (or set ELECTRAFI_API_TOKEN env var)",
    )
    parser.add_argument(
        "--from",
        dest="date_from",
        help="Start date (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--to",
        dest="date_to",
        help="End date (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--last-month",
        action="store_true",
        help="Analyze last complete month",
    )
    parser.add_argument(
        "--month",
        help="Analyze specific month (YYYY-MM, e.g., 2026-01)",
    )
    parser.add_argument(
        "--home-only",
        action="store_true",
        help="Show only home charging",
    )
    parser.add_argument(
        "--details",
        action="store_true",
        help="Show detailed list of charging sessions",
    )
    parser.add_argument(
        "--all-stats",
        action="store_true",
        help="Show all charging statistics (home + away)",
    )
    
    args = parser.parse_args()
    
    # Get API token
    api_token = args.token or os.getenv("ELECTRAFI_API_TOKEN")
    if not api_token:
        print("ERROR: No API token provided. Set ELECTRAFI_API_TOKEN environment variable or use --token")
        sys.exit(1)
    
    # Determine date range
    if args.last_month:
        date_from, date_to = get_last_complete_month()
        print(f"Analyzing last complete month: {date_from} to {date_to}\n")
    elif args.month:
        try:
            year, month = map(int, args.month.split("-"))
            first_day = date(year, month, 1)
            # Last day of the month
            if month == 12:
                last_day = date(year + 1, 1, 1) - relativedelta(days=1)
            else:
                last_day = date(year, month + 1, 1) - relativedelta(days=1)
            date_from = first_day.strftime("%Y-%m-%d")
            date_to = last_day.strftime("%Y-%m-%d")
            print(f"Analyzing {args.month}: {date_from} to {date_to}\n")
        except ValueError:
            print("ERROR: Invalid month format. Use YYYY-MM (e.g., 2026-01)")
            sys.exit(1)
    elif args.date_from and args.date_to:
        date_from = args.date_from
        date_to = args.date_to
        print(f"Analyzing: {date_from} to {date_to}\n")
    else:
        print("ERROR: Please specify date range using --from/--to, --month, or --last-month")
        sys.exit(1)
    
    # Fetch data
    try:
        api = ChargingHistoryAPI(api_token)
        print("Fetching charging data...")
        data = api.get_charges(date_from, date_to)
        
        analyzer = ChargingAnalyzer(data)
        
        print(f"Total charging sessions found: {data.get('count', 0)}\n")
        
        # Home charging summary
        if not args.all_stats:
            print("=" * 60)
            print("HOME CHARGING SUMMARY")
            print("=" * 60)
            home_summary = analyzer.calculate_home_summary()
            print(json.dumps(home_summary, indent=2))
        
        # All charging summary
        if args.all_stats:
            print("=" * 60)
            print("ALL CHARGING SUMMARY")
            print("=" * 60)
            all_summary = analyzer.calculate_all_charging_summary()
            print(json.dumps(all_summary, indent=2))
            
            print("\n" + "=" * 60)
            print("HOME CHARGING DETAILS")
            print("=" * 60)
            home_summary = analyzer.calculate_home_summary()
            print(json.dumps(home_summary, indent=2))
        
        # Detailed list
        if args.details:
            print("\n" + "=" * 60)
            print("CHARGING SESSIONS DETAIL")
            print("=" * 60)
            details = analyzer.get_charging_details(home_only=args.home_only)
            for i, session in enumerate(details, 1):
                print(f"\nSession {i}:")
                print(json.dumps(session, indent=2))
        
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
