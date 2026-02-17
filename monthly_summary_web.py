#!/usr/bin/env python3
"""
Generate web-ready charging data for GitHub Pages
"""

import os
import sys
import json
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
import requests


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
    
    # Prepare data with Y/Y comparisons
    output_data = []
    for m in months:
        label = m["label"]
        if label not in monthly_data:
            continue
        
        data = monthly_data[label]
        
        # Calculate Y/Y
        prior_year_label = f"{m['year']-1-2000:02d}-{m['month']:02d}"
        yoy = None
        if prior_year_label in monthly_data:
            prior_kwh = monthly_data[prior_year_label]["kwh"]
            if prior_kwh > 0:
                pct_change = ((data["kwh"] - prior_kwh) / prior_kwh) * 100
                yoy = round(pct_change, 0)
        
        output_data.append({
            "date": label,
            "kwh": data["kwh"],
            "cost": data["cost"],
            "odo": data["odo"],
            "cost_per_kwh": data["cost_per_kwh"],
            "yoy": yoy
        })
    
    # Create docs directory if it doesn't exist
    os.makedirs("docs", exist_ok=True)
    
    # Save JSON data
    with open("docs/charging_data.json", "w") as f:
        json.dump({
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
            "data": output_data
        }, f, indent=2)
    
    # Generate HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Rivian R1S Charging History</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            max-width: 1000px;
            margin: 40px auto;
            padding: 0 20px;
            background: #f5f5f5;
            color: #333;
        }}
        .container {{
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #1a1a1a;
            margin-bottom: 10px;
        }}
        .subtitle {{
            color: #666;
            margin-bottom: 30px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th {{
            background: #f8f9fa;
            padding: 12px;
            text-align: left;
            border-bottom: 2px solid #dee2e6;
            font-weight: 600;
        }}
        td {{
            padding: 10px 12px;
            border-bottom: 1px solid #e9ecef;
        }}
        tr:hover {{
            background: #f8f9fa;
        }}
        .positive {{
            color: #28a745;
        }}
        .negative {{
            color: #dc3545;
        }}
        .footer {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #e9ecef;
            color: #666;
            font-size: 14px;
        }}
        @media (max-width: 768px) {{
            table {{
                font-size: 14px;
            }}
            th, td {{
                padding: 8px 6px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔋 Rivian R1S Home Charging History</h1>
        <p class="subtitle">Last 24 months of home charging data</p>
        
        <table>
            <thead>
                <tr>
                    <th>Date</th>
                    <th>kWh</th>
                    <th>Cost</th>
                    <th>Odometer</th>
                    <th>$/kWh</th>
                    <th>Y/Y</th>
                </tr>
            </thead>
            <tbody>
"""
    
    for row in output_data:
        yoy_class = ""
        yoy_text = ""
        if row["yoy"] is not None:
            yoy_class = "positive" if row["yoy"] >= 0 else "negative"
            yoy_text = f"{row['yoy']:+.0f}%"
        
        html += f"""                <tr>
                    <td>{row['date']}</td>
                    <td>{row['kwh']:.1f}</td>
                    <td>${row['cost']:.2f}</td>
                    <td>{row['odo']:,.0f}</td>
                    <td>${row['cost_per_kwh']:.2f}</td>
                    <td class="{yoy_class}">{yoy_text}</td>
                </tr>
"""
    
    html += f"""            </tbody>
        </table>
        
        <div class="footer">
            <p><strong>Last Updated:</strong> {datetime.now().strftime("%B %d, %Y at %H:%M UTC")}</p>
            <p><strong>Data Source:</strong> ElectraFi API</p>
            <p><strong>Y/Y:</strong> Year-over-year comparison of kWh usage vs same month in prior year</p>
        </div>
    </div>
</body>
</html>"""
    
    with open("docs/index.html", "w") as f:
        f.write(html)
    
    print("✓ Generated docs/index.html")
    print("✓ Generated docs/charging_data.json")
    print(f"✓ Updated with data through {output_data[-1]['date']}")


if __name__ == "__main__":
    main()
