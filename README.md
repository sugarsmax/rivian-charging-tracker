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

- Fetches last 24 months of charging data from ElectraFi API
- Displays: kWh consumed, cost, odometer, and year-over-year comparisons
- Automatically updates on the 3rd of each month via GitHub Actions
- Publishes to GitHub Pages

## Files

- `monthly_summary_web.py` - Generates HTML and JSON from ElectraFi API
- `.github/workflows/update_charging_data.yml` - GitHub Actions workflow
- `docs/index.html` - Generated GitHub Pages site
- `docs/charging_data.json` - Raw data in JSON format
- `GITHUB_PAGES_SETUP.md` - Detailed setup instructions

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
