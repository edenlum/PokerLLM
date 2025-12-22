# GitHub Pages Setup for LLM Poker Benchmark

This guide explains how to set up GitHub Pages for the LLM Poker Benchmark to automatically publish results online.

## 🚀 Quick Setup

### 1. Enable GitHub Pages

1. Go to your repository settings on GitHub
2. Navigate to **Pages** in the left sidebar
3. Under **Source**, select **GitHub Actions**
4. The workflow will automatically deploy when you push changes

### 2. Run Some Benchmarks

Generate some data to display:

```bash
# Register a few LLMs
python3 benchmark/cli.py register "gpt-4-turbo" openai gpt-4-turbo
python3 benchmark/cli.py register "gemini-pro" google gemini-pro

# Run a tournament
python3 benchmark/cli.py run-tournament --hands 100

# Generate the site
python3 benchmark/cli.py generate-site
```

### 3. Push to GitHub

```bash
git add .
git commit -m "Add benchmark results and GitHub Pages site"
git push origin main
```

Your site will be available at: `https://yourusername.github.io/poker/`

## 📁 Site Structure

The GitHub Pages site is located in the `docs/` directory:

```
docs/
├── index.html          # Main leaderboard page
├── pairwise.html       # Head-to-head results matrix  
├── about.html          # Methodology and info
├── assets/
│   ├── css/style.css   # Styling
│   └── js/
│       ├── data.js     # Auto-generated benchmark data
│       ├── main.js     # Leaderboard functionality
│       └── pairwise.js # Pairwise results functionality
└── README.md           # Site documentation
```

## 🔄 Automatic Updates

The site automatically updates when:

1. **New benchmark results** are added to `benchmark/results.db`
2. **Site generator** is modified
3. **Manual workflow trigger** via GitHub Actions

The workflow (`.github/workflows/deploy-site.yml`) will:
1. Check out the code
2. Set up Python environment
3. Run the site generator to update `data.js`
4. Deploy the updated site to GitHub Pages

## 🛠️ Manual Site Generation

You can generate the site locally:

```bash
# Using the site generator directly
python3 benchmark/site_generator.py --db benchmark/results.db --output docs

# Using the CLI
python3 benchmark/cli.py generate-site --output docs
```

## 📊 Site Features

### Leaderboard Page
- **Overall Rankings**: LLMs ranked by average chips per hand
- **Performance Metrics**: Win rate, fallback rate, total hands
- **Recent Matches**: Latest session results
- **Interactive Stats**: Total LLMs, sessions, hands played

### Pairwise Results Page
- **Interactive Matrix**: Head-to-head performance grid
- **Multiple Metrics**: Switch between winnings, win rate, sessions
- **Detailed Results**: Filterable match history
- **Visual Indicators**: Color-coded performance levels

### About Page
- **Methodology**: How the benchmark works
- **Technical Details**: Implementation information
- **Game Rules**: Poker format and scoring
- **Contributing**: How to add LLMs or improve the benchmark

## 🎨 Customization

### Styling
Edit `docs/assets/css/style.css` to customize:
- Colors and themes
- Layout and spacing
- Responsive breakpoints
- Visual effects

### Data Processing
Modify `benchmark/site_generator.py` to:
- Add new metrics or calculations
- Change data aggregation logic
- Include additional information
- Optimize for large datasets

### Layout
Update HTML templates to:
- Add new pages or sections
- Modify navigation structure
- Include additional content
- Change page organization

## 🔧 Troubleshooting

### Site Not Updating
1. Check GitHub Actions tab for workflow errors
2. Verify database file exists and has data
3. Ensure Python dependencies are available in workflow
4. Check if GitHub Pages is enabled in repository settings

### Display Issues
1. Clear browser cache and hard refresh
2. Check browser console for JavaScript errors
3. Verify `data.js` is being generated correctly
4. Test site locally before pushing

### Performance Issues
1. Large datasets may slow loading - consider pagination
2. Optimize images and assets
3. Use CDN for external libraries
4. Minimize JavaScript and CSS files

## 📈 Analytics (Optional)

To add website analytics:

1. **Google Analytics**: Add tracking code to HTML templates
2. **GitHub Insights**: Use repository traffic data
3. **Custom Analytics**: Track specific benchmark metrics
4. **Privacy**: Add appropriate privacy notices

## 🔒 Security Considerations

- **No Sensitive Data**: Don't include API keys in the site
- **Static Content**: Site is purely static HTML/CSS/JS
- **Public Repository**: All code and results are public
- **HTTPS**: GitHub Pages provides HTTPS by default

## 🚀 Advanced Features

### Custom Domain
1. Add `CNAME` file to `docs/` directory
2. Configure DNS settings for your domain
3. Enable custom domain in GitHub Pages settings

### Multiple Environments
- **Production**: Main branch → GitHub Pages
- **Staging**: Feature branches → separate deployments
- **Development**: Local testing with `python -m http.server`

### API Integration
- Add real-time data updates via GitHub API
- Integrate with external benchmark services
- Provide JSON API endpoints for data access

## 📝 Content Management

### Adding New Pages
1. Create HTML file in `docs/`
2. Add navigation links in existing pages
3. Update CSS for consistent styling
4. Test responsive design

### Data Updates
- Site automatically regenerates when database changes
- Manual updates via CLI or site generator
- Batch processing for large datasets

### Version Control
- All site changes tracked in Git
- Easy rollback to previous versions
- Collaborative editing via pull requests

## 🎯 Best Practices

1. **Regular Updates**: Run benchmarks frequently for fresh data
2. **Data Validation**: Verify results before publishing
3. **Performance Testing**: Test site with large datasets
4. **Mobile Optimization**: Ensure good mobile experience
5. **Accessibility**: Follow web accessibility guidelines
6. **SEO**: Add meta tags and structured data
7. **Monitoring**: Set up alerts for site issues

Your LLM Poker Benchmark site is now ready to showcase your results to the world! 🎉
