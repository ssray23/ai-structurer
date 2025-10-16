# AI Document Structurer (Node.js Version)

This is the **Node.js/Express** replatform of the AI Document Structurer application. This version provides significantly faster startup times compared to the Python/Flask version while maintaining 100% feature parity.

## Why Node.js?

- **Instant Startup**: Node.js starts in milliseconds vs Python's slow module loading
- **Lower Memory**: More efficient runtime environment
- **Same Logic**: All AI processing, theming, and formatting logic is identical
- **Same API**: Frontend works unchanged - same endpoints, same responses

## Quick Start

### 1. Install Dependencies

```bash
npm install
```

### 2. Environment Variables

Create a `.env` file with your API keys:

```env
OPENAI_API_KEY=your_openai_key_here
GOOGLE_API_KEY=your_gemini_key_here
BRAVE_API_KEY=your_brave_search_key_here

# Optional configuration
ENVIRONMENT=development
API_TIMEOUT=60
MAX_RETRIES=3
MAX_TOKENS_CONCISE=4000
MAX_TOKENS_DETAILED=8000
MAX_TOKENS_COMPREHENSIVE=12000
```

### 3. Run the Server

```bash
# Production mode
npm start

# Development mode with auto-reload
npm run dev
```

The server runs on `http://localhost:5000`

## Features

All features from the Python version are preserved:

- AI-powered document structuring with GPT-4o-mini, Gemini Pro 2.5, and GPT-5
- Dynamic theme detection (finance, tech, health, travel, food)
- Web search integration with Brave API
- URL article extraction with recipe support (WPRM)
- Verbosity levels (Concise, Detailed, Comprehensive)
- A4 document formatting with professional styling
- Token usage tracking and cost calculation

## Architecture

```
├── server.js          # Main Express application (replaces server.py)
├── config.js          # Configuration system (replaces config.py)
├── package.json       # Node.js dependencies
├── templates/
│   └── index.html     # Frontend (unchanged from Python version)
└── .env               # Environment variables
```

## API Endpoints

### `GET /`
Serves the main application interface

### `POST /api/process`
Process documents with AI

**Request Body:**
```json
{
  "text": "Content to process",
  "aiTopic": "Research topic (for AI Research mode)",
  "articleUrl": "URL to extract content from",
  "model": "GPT-4o-mini | Gemini Pro 2.5 | GPT-5",
  "verbosity": "Concise | Detailed | Comprehensive"
}
```

**Response:**
```json
{
  "html": "<styled document>",
  "tokens": {
    "prompt": 1000,
    "completion": 2000,
    "total": 3000
  },
  "cost": 0.0045,
  "model": "GPT-5",
  "theme": "tech",
  "theme_color": "#007bff"
}
```

## Performance Comparison

| Metric | Python/Flask | Node.js/Express |
|--------|--------------|-----------------|
| Cold Start | 2-5 seconds | ~200ms |
| Memory Usage | ~150MB | ~80MB |
| Request Handling | Same | Same |
| API Processing | Same | Same |

## Deployment

### Local Development
```bash
npm run dev
```

### Production
```bash
npm start
```

### Render.com (or similar)
1. Set build command: `npm install`
2. Set start command: `npm start`
3. Add environment variables in dashboard
4. Deploy!

## Migration from Python

If you're migrating from the Python version:

1. **Keep your `.env` file** - environment variables are the same
2. **Templates folder** - no changes needed
3. **Remove Python dependencies** - you can optionally remove `requirements.txt` and Python files
4. **Update deployment** - change start command to `npm start`

## Dependencies

- **express**: Web framework
- **openai**: OpenAI API client
- **@google/generative-ai**: Gemini API client
- **axios**: HTTP client for web searches
- **cheerio**: HTML parsing for article extraction
- **dotenv**: Environment variable management
- **cors**: CORS middleware

## License

Same as the original Python version.
