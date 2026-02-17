# GitHub Pages Setup Instructions

This will set up automatic monthly updates of your Rivian charging data on GitHub Pages.

## 📋 Prerequisites

1. GitHub account
2. Git installed locally

## 🚀 Setup Steps

### 1. Create GitHub Repository

```bash
cd "/Users/maxfiep/Library/CloudStorage/GoogleDrive-pmaxfield@gmail.com/My Drive/Property/Car/Rivian_R1S_2023/Rivian_Home_Charging"

# Initialize git repository (if not already done)
git init

# Create .gitignore to protect sensitive files
cat > .gitignore << 'EOF'
.env
api_cache/
__pycache__/
*.pyc
.DS_Store
EOF

# Add all files
git add .
git commit -m "Initial commit: Rivian charging tracker"

# Create repository on GitHub (via web or CLI)
# Option A: Via GitHub website
#   1. Go to https://github.com/new
#   2. Name it: rivian-charging-tracker
#   3. Keep it PUBLIC (required for free GitHub Pages)
#   4. Don't initialize with README
#   5. Create repository

# Option B: Via GitHub CLI (if installed)
gh repo create rivian-charging-tracker --public --source=. --remote=origin

# Push to GitHub
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/rivian-charging-tracker.git
git push -u origin main
```

### 2. Add API Token as Secret

1. Go to your repository on GitHub
2. Click **Settings** tab
3. In left sidebar, click **Secrets and variables** → **Actions**
4. Click **New repository secret**
5. Name: `ELECTRAFI_API_TOKEN`
6. Value: `bdd0db288be24dc8dc1b95d73c3387a82579427417fe33fe196037c45f846d58`
7. Click **Add secret**

### 3. Enable GitHub Pages

1. In your repository, go to **Settings** tab
2. In left sidebar, click **Pages**
3. Under **Source**, select:
   - Branch: `main`
   - Folder: `/docs`
4. Click **Save**
5. Wait ~1 minute, then refresh - you'll see your site URL

Your site will be at: `https://YOUR_USERNAME.github.io/rivian-charging-tracker/`

### 4. Test the Workflow

The workflow runs automatically on the 3rd of each month, but you can test it now:

1. Go to **Actions** tab in your repository
2. Click on **Update Charging Data** workflow
3. Click **Run workflow** button
4. Select `main` branch
5. Click **Run workflow**

Watch it run! It should complete in ~30 seconds.

## 📅 Automatic Updates

The GitHub Action runs automatically:
- **When:** 2 AM UTC on the 3rd of each month
- **What it does:**
  1. Fetches last 24 months of charging data from ElectraFi API
  2. Generates updated HTML page and JSON data
  3. Commits and pushes changes to your repository
  4. GitHub Pages automatically updates within minutes

## 📁 What Was Created

```
.github/workflows/
  └── update_charging_data.yml    # GitHub Actions workflow

docs/
  ├── index.html                   # Your GitHub Pages site
  └── charging_data.json          # Raw data (for potential API use)

monthly_summary_web.py            # Script to generate web content
GITHUB_PAGES_SETUP.md            # This file
```

## 🎨 Customizing the Page

To customize the look of your page, edit `monthly_summary_web.py` in the HTML generation section (around line 100). You can:
- Change colors
- Modify layout
- Add charts/graphs
- Add your vehicle name/photo

After making changes:
```bash
git add monthly_summary_web.py
git commit -m "Customize page design"
git push
```

Then manually trigger the workflow or wait for next month's automatic update.

## 🔒 Security Notes

- **Never commit your `.env` file** - it's in `.gitignore`
- The API token is stored as a GitHub Secret (encrypted)
- The repository should be PUBLIC for free GitHub Pages
- Only the charging data is public (no personal info)

## 🐛 Troubleshooting

### Workflow fails
- Check that `ELECTRAFI_API_TOKEN` secret is set correctly
- View workflow logs in Actions tab for specific error

### Page not updating
- Verify workflow completed successfully in Actions tab
- Check that GitHub Pages is enabled and pointing to `/docs` folder
- Clear browser cache and refresh

### Want to run manually
```bash
python3 monthly_summary_web.py
# Then commit and push the updated docs/ files
```

## 📊 What Visitors See

The public page shows:
- Last 24 months of home charging data
- kWh consumed
- Cost per month
- Odometer readings
- Year-over-year comparisons
- Last updated timestamp

No personal information (VIN, exact location, real-time data) is exposed.
