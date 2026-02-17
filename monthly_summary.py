#!/usr/bin/env python3
"""
Simple monthly charging summary with year-over-year comparisons
"""

import os
import sys
from datetime import date
from dateutil.relativedelta import relativedelta
import requests
import json

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def get_charges(api_token, date_from, date_to):
    """Get charging data for date range."""
    headers = {"Authorization": f"Bearer {api_token}"}
    params = {
        "command": "charges",
        "dateFrom": date_from,
        "dateTo": date_to
    }
    
    response = requests.get(
        "https://www.electrafi.com/history.php",
        headers=headers,
        params=params,
        timeout=30
    )
    response.raise_for_status()
    return response.json()


def analyze_month(data):
    """Extract the three key values for a month."""
    results = data.get("results", [])
    home_charges = [r for r in results if r.get("homeChargeFlag") == 1]
    
    if not home_charges:
        return None
    
    total_kwh = sum(float(c.get("totalEnergyAdded", 0) or 0) for c in home_charges)
    total_cost = sum(float(c.get("homeCost", 0) or 0) for c in home_charges)
    
    # Get final odometer from last charge
    sorted_charges = sorted(home_charges, key=lambda x: x.get("date", ""))
    final_odo = float(sorted_charges[-1].get("odometer", 0)) if sorted_charges else 0
    
    return {
        "kwh": round(total_kwh, 1),
        "cost": round(total_cost, 2),
        "odo": round(final_odo, 0),
        "cost_per_kwh": round(total_cost / total_kwh, 2) if total_kwh > 0 else 0
    }


def main():
    api_token = os.getenv("ELECTRAFI_API_TOKEN")
    if not api_token:
        print("ERROR: ELECTRAFI_API_TOKEN not set")
        sys.exit(1)
    
    output_file = "charging_history.txt"
    
    # Calculate last 24 months
    today = date.today()
    months = []
    
    for i in range(24, 0, -1):
        month_date = today - relativedelta(months=i)
        first_day = date(month_date.year, month_date.month, 1)
        
        # Last day of month
        if month_date.month == 12:
            last_day = date(month_date.year + 1, 1, 1) - relativedelta(days=1)
        else:
            last_day = date(month_date.year, month_date.month + 1, 1) - relativedelta(days=1)
        
        months.append({
            "year": month_date.year,
            "month": month_date.month,
            "first_day": first_day.strftime("%Y-%m-%d"),
            "last_day": last_day.strftime("%Y-%m-%d"),
            "label": first_day.strftime("%y-%m")
        })
    
    # Fetch data for all months
    print("Fetching 24 months of charging data...")
    monthly_data = {}
    
    for m in months:
        try:
            data = get_charges(api_token, m["first_day"], m["last_day"])
            result = analyze_month(data)
            if result:
                monthly_data[m["label"]] = result
        except Exception as e:
            print(f"Error fetching {m['label']}: {e}")
    
    # Open file in append mode
    with open(output_file, 'a') as f:
        # Write header with timestamp
        from datetime import datetime
        f.write(f"\n{'='*60}\n")
        f.write(f"Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"{'='*60}\n")
        f.write(f"{'date':<8} {'kWh':<8} {'cost':<10} {'ODO':<8} {'$/kWh':<8} {'Y/Y':<8}\n")
        f.write(f"{'-'*60}\n")
        
        # Also print to screen
        print(f"\n{'date':<8} {'kWh':<8} {'cost':<10} {'ODO':<8} {'$/kWh':<8} {'Y/Y':<8}")
        print("=" * 60)
        
        for m in months:
            label = m["label"]
            if label not in monthly_data:
                continue
            
            data = monthly_data[label]
            
            # Calculate Y/Y (compare to same month last year)
            prior_year_label = f"{m['year']-1-2000:02d}-{m['month']:02d}"
            yoy = ""
            if prior_year_label in monthly_data:
                prior_kwh = monthly_data[prior_year_label]["kwh"]
                if prior_kwh > 0:
                    pct_change = ((data["kwh"] - prior_kwh) / prior_kwh) * 100
                    yoy = f"{pct_change:+.0f}%"
            
            line = f"{label:<8} {data['kwh']:<8.1f} ${data['cost']:<9.2f} {data['odo']:<8.0f} ${data['cost_per_kwh']:<7.2f} {yoy:<8}"
            print(line)
            f.write(line + "\n")
        
        f.write("\n")
    
    print(f"\nData appended to: {output_file}")


if __name__ == "__main__":
    main()
