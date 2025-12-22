# LLM Poker Benchmark - GitHub Pages Site

This directory contains the static GitHub Pages website for the LLM Poker Benchmark.

## 🌐 Live Site

The benchmark results are automatically published to GitHub Pages at:
**https://edenlumbroso.github.io/poker/**

## 📁 Structure

```
docs/
├── index.html          # Main leaderboard page
├── pairwise.html       # Pairwise results matrix
├── about.html          # About the benchmark
├── assets/
│   ├── css/
│   │   └── style.css   # Main stylesheet
│   └── js/
│       ├── data.js     # Generated benchmark data
│       ├── main.js     # Leaderboard page logic
│       └── pairwise.js # Pairwise results logic
└── README.md           # This file
```

## 🔄 Auto-Updates

The site is automatically updated when:

1. **New benchmark results** are added to `benchmark/results.db`
2. **Site generator** (`benchmark/site_generator.py`) is modified
3. **Manual trigger** via GitHub Actions

## 🛠️ Manual Generation

To generate the site locally:

```bash
# From the project root
python benchmark/site_generator.py --db benchmark/results.db --output docs

# Or using the CLI
python benchmark/cli.py generate-site
```

## 📊 Data Source

The site displays data from the SQLite database at `benchmark/results.db`, including:

- **Leaderboard**: Overall LLM rankings by average chips per hand
- **Pairwise Results**: Head-to-head matchup matrix
- **Recent Matches**: Latest session results
- **Statistics**: Overall benchmark stats

## 🎨 Features

### Leaderboard Page (`index.html`)
- Overall LLM rankings
- Performance metrics (avg chips/hand, win rate, fallback rate)
- Recent match summaries
- Interactive statistics

### Pairwise Results (`pairwise.html`)
- Interactive matchup matrix
- Multiple display metrics (winnings, win rate, sessions)
- Detailed match results
- Filtering by LLM

### About Page (`about.html`)
- Benchmark methodology
- Technical implementation details
- Game format explanation
- Contributing guidelines

## 🔧 Customization

To customize the site:

1. **Styling**: Edit `assets/css/style.css`
2. **Layout**: Modify the HTML templates
3. **Data Processing**: Update `benchmark/site_generator.py`
4. **Interactions**: Edit JavaScript files in `assets/js/`

## 📱 Responsive Design

The site is fully responsive and works on:
- Desktop browsers
- Tablets
- Mobile devices

## 🚀 Deployment

Deployment is handled automatically by GitHub Actions:

1. Push changes to the `main` branch
2. GitHub Actions runs the site generator
3. Updated site is deployed to GitHub Pages
4. Changes are live within minutes

## 🐛 Troubleshooting

### Site Not Updating
- Check GitHub Actions logs for errors
- Verify database file exists and has data
- Ensure Python dependencies are available

### Display Issues
- Clear browser cache
- Check browser console for JavaScript errors
- Verify data.js is being generated correctly

### Performance Issues
- Large datasets may slow page loading
- Consider pagination for very large result sets
- Optimize images and assets if added

## 📈 Analytics

To add analytics (optional):
1. Add Google Analytics or similar tracking code
2. Update HTML templates with tracking scripts
3. Respect user privacy and add appropriate notices
