# Quick Start Guide

## Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

## Common Commands

### Check Battery Status
```bash
python3 electrafi_query.py battery
```

### Check Charging Status
```bash
python3 electrafi_query.py charging
```

### Get Complete Summary
```bash
python3 electrafi_query.py summary
```

### Check Vehicle Location
```bash
python3 electrafi_query.py location
```

## Control Commands (with --execute flag)

### Start/Stop Charging
```bash
# Start
python3 electrafi_query.py charge-start --execute

# Stop
python3 electrafi_query.py charge-stop --execute
```

### Control HVAC
```bash
# Start HVAC
python3 electrafi_query.py hvac-start --execute

# Set temperature to 21°C
python3 electrafi_query.py set-temp 21 --execute

# Stop HVAC
python3 electrafi_query.py hvac-stop --execute
```

### Set Charge Limit
```bash
# Set to 80%
python3 electrafi_query.py set-charge-limit 80 --execute
```

## Testing Commands Safely

All commands default to dry-run mode. Test without --execute:

```bash
# This will NOT actually start HVAC
python3 electrafi_query.py hvac-start

# Output shows what WOULD happen
[DRY RUN] Would send command: auto_conditioning_start
```

## Your Current Status

Based on the test query, your Rivian R1S:
- **Battery:** 82.4% (charging to 85% limit)
- **Range:** 231 miles (372 km)
- **Location:** Home
- **Status:** Currently charging at 7.3 kW
- **Estimated time to full:** ~28 minutes
- **Odometer:** 14,247 miles (22,928 km)
- **Software:** 2025.46.0

## Important Notes

- All control commands require `--execute` to actually run
- Commands may wake your vehicle if it's asleep (uses extra API credits)
- Responses are automatically cached in `api_cache/` directory
- Your API token is stored in `.env` (not tracked by git)

## Get Help

```bash
python3 electrafi_query.py --help
```
