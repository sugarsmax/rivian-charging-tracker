# Rivian R1S Charging Tracker

Automated GitHub Pages site that displays 24 months of home charging history, updated automatically on the 3rd of each month.

## Quick Start

1. **Set up GitHub repository** - See [GITHUB_PAGES_SETUP.md](GITHUB_PAGES_SETUP.md) for complete instructions

2. **Test locally**:
   ```bash
   pip install -r requirements.txt
   python3 monthly_summary_web.py
   ```

3. **View generated page**:
   ```bash
   open docs/index.html
   ```

## What This Does

- **GitHub Pages Site**: Automatically updates on the 3rd of each month with 24 months of charging history
- **Real-Time Queries**: Query current vehicle status (battery, charging, location, temperature)
- **Historical Analysis**: Deep dive into charging patterns for any date range
- **Vehicle Control**: Send commands to your vehicle (HVAC, charging, etc.)

## Tools Included

### 🌐 GitHub Pages (Auto-updating)
- `monthly_summary_web.py` - Generates HTML and JSON from ElectraFi API
- `.github/workflows/update_charging_data.yml` - GitHub Actions workflow
- `docs/index.html` - Your public charging history page with chart
- `docs/charging_data.json` - Raw data in JSON format

### ⚡ Real-Time Vehicle Queries
- `electrafi_query.py` - Query current vehicle data and send commands
  - Battery status, charging info, location, temperature
  - Control HVAC, charging, seat heaters
  - Dry-run mode by default for safety

### 📊 Historical Analysis
- `analyze_charging.py` - Analyze charging history for any date range
  - Monthly summaries with costs and efficiency
  - Session-level details
  - Home vs. away charging comparison
  
- `monthly_summary.py` - Generate 24-month summary with Y/Y comparisons
  - Appends to `charging_history.txt` for tracking over time

## Quick Examples

### Real-Time Queries
```bash
# Check battery status
python3 electrafi_query.py battery

# Get complete vehicle summary
python3 electrafi_query.py summary

# Start HVAC (dry-run)
python3 electrafi_query.py hvac-start
```

### Historical Analysis
```bash
# Analyze January 2026
python3 analyze_charging.py --month 2026-01

# Last complete month
python3 analyze_charging.py --last-month

# 24-month summary with Y/Y
python3 monthly_summary.py
```

See [QUICK_START.md](QUICK_START.md) for more examples.

## Setup Checklist

- [ ] Create GitHub repository (public)
- [ ] Add `ELECTRAFI_API_TOKEN` as repository secret
- [ ] Enable GitHub Pages (branch: main, folder: /docs)
- [ ] Test workflow manually
- [ ] Visit your live site!

## Your Site URL

After setup: `https://YOUR_USERNAME.github.io/rivian-charging-tracker/`

## Security

- API token stored as encrypted GitHub Secret
- `.env` file is gitignored
- Only aggregated monthly data is public
- No personal information exposed
