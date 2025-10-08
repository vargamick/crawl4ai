const path = require('path');
const fs = require('fs');

// Read package.json for version
const packageJson = JSON.parse(fs.readFileSync(path.join(__dirname, 'package.json'), 'utf8'));

module.exports = {
  mode: process.env.NODE_ENV === 'production' ? 'production' : 'development',
  entry: './src/js/embed.js',
  output: {
    path: path.resolve(__dirname, 'dist'),
    filename: process.env.NODE_ENV === 'production' ? 'crawl4ai-scraper.min.js' : 'crawl4ai-scraper.js',
    library: {
      name: 'Crawl4AIScraper',
      type: 'umd',
      export: 'default'
    },
    globalObject: 'this'
  },
  module: {
    rules: [
      {
        test: /\.js$/,
        exclude: /node_modules/,
        use: {
          loader: 'babel-loader',
          options: {
            presets: ['@babel/preset-env']
          }
        }
      },
      {
        test: /\.css$/,
        use: [
          {
            loader: 'css-loader',
            options: {
              exportType: 'string'
            }
          }
        ]
      },
      {
        test: /\.html$/,
        use: [
          {
            loader: 'html-loader',
            options: {
              minimize: true,
              esModule: false
            }
          }
        ]
      }
    ]
  },
  resolve: {
    extensions: ['.js', '.css', '.html']
  },
  devtool: process.env.NODE_ENV === 'production' ? 'source-map' : 'eval-source-map',
  plugins: [
    // Add banner with version and build info
    new (require('webpack')).BannerPlugin({
      banner: `
/*!
 * Crawl4AI Scraper Frontend v${packageJson.version}
 * Embeddable web scraper interface for Crawl4AI
 * 
 * Build: ${new Date().toISOString()}
 * License: ${packageJson.license}
 * Repository: ${packageJson.repository?.url || 'N/A'}
 */
      `.trim(),
      raw: false
    })
  ],
  optimization: {
    minimize: process.env.NODE_ENV === 'production'
  }
};
