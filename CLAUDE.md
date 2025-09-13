# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Flask-based web application that uses AI to structure and format documents into visually appealing HTML. The app takes unstructured text input and converts it into well-formatted documents with headings, tables, fact boxes, and themed styling.

## Architecture

- **Backend**: Flask server (`server.py`) with OpenAI API integration
- **Frontend**: Single HTML template (`templates/index.html`) with vanilla JavaScript
- **AI Processing**: Uses OpenAI GPT-4o-mini to interpret and structure content
- **Theming**: Dynamic color themes based on content analysis (finance=green, tech=blue, health=pink, auto=orange)

## Development Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
python server.py

# The server runs on http://localhost:5000 with debug=True

# Production deployment (using gunicorn)
gunicorn server:app

# Testing (if applicable)
python -m pytest  # No test framework currently configured
```

## Environment Setup

Required environment variables in `.env`:
- `OPENAI_API_KEY`: OpenAI API key for content processing
- `BRAVE_API_KEY`: For web search functionality (optional)
- `OPENAI_MODEL`: Set to "gpt-4o-mini" (default)
- `ENVIRONMENT`: "development", "production", or "testing" (auto-detected on Render)
- `API_TIMEOUT`: API timeout in seconds (default: 60 dev, 20 prod)
- `MAX_RETRIES`: Max retry attempts (default: 3 dev, 1 prod)
- `MAX_TOKENS_*`: Token limits per verbosity level (see config.py for defaults)

## Key Components

### Configuration System (`config.py`)
- Environment-based configuration (development/production/testing)
- Automatic Render deployment detection via `RENDER` env var
- Configurable API timeouts, retry limits, and token limits per environment
- Production settings optimized for free tier constraints

### Content Processing (`server.py:409-717`)
- `/api/process` endpoint handles both document processing and AI research modes
- Two processing modes:
  - **Document Processing**: Structures existing text with light web search enhancement
  - **AI Research**: Creates comprehensive documents from topic keywords with extensive web search
- AI-powered theme detection (`extract_theme` function at `server.py:343-391`)
- Dynamic verbosity levels (Concise/Detailed/Comprehensive) with different token limits
- Web search integration using Brave Search API (`web_search` function at `server.py:30-60`)

### Styling System (`server.py:62-329`)
- A4-formatted CSS template with dynamic theme injection
- Theme colors: finance=green, tech=blue, health=pink, auto=orange, default=gray
- Responsive design with breakpoints for different screen sizes
- Comprehensive styling for tables, stat boxes, fact cards, timelines
- Print-optimized styles for PDF generation

### Frontend Features (`templates/index.html`)
- Split-screen interface with input/output panels
- Model selection (GPT-4o-mini, Gemini Pro 2.5, GPT-5)
- Verbosity control (Concise/Detailed/Comprehensive)
- AI Research mode toggle for topic-based document generation
- Real-time HTML preview with live updates
- Download functionality (HTML/PDF)
- Token usage and cost tracking display

## Content Processing Flow

### Document Processing Mode
1. User inputs text via textarea and selects processing options
2. Frontend sends POST request to `/api/process` with text, model, verbosity
3. Backend performs light web search for additional context (2 results)
4. AI analyzes content for theme detection using GPT-4o
5. Main AI model processes content with verbosity-specific instructions
6. HTML generated following strict structural templates (tables, stat boxes, fact cards)
7. CSS styling applied with theme-specific colors
8. Complete styled document returned with token usage and cost data

### AI Research Mode
1. User enters research topic and enables AI Research mode
2. Frontend sends topic to `/api/process` with research flag
3. Backend performs extensive web search (5 results)
4. AI analyzes topic for theme detection
5. Research content generated from web results and AI knowledge
6. Same HTML structuring and styling process applied
7. Comprehensive research document returned

## Visual Design Principles

- A4 document format (21cm width, responsive scaling)
- CMYK-inspired color themes based on AI content analysis
- Professional document styling with borders and spacing
- Table-first approach for data presentation
- Clean typography using Helvetica font family
- Structured HTML elements: fact cards, stat grids, timelines, comparison tables
- Print-optimized styles for PDF generation

## File Structure

```
├── server.py           # Main Flask application with API endpoints
├── config.py          # Environment-based configuration system
├── requirements.txt   # Python dependencies
├── templates/
│   └── index.html     # Single-page frontend application
├── wsgi.py           # WSGI entry point for production deployment
└── test_gemini_api.py # API testing script
```

## API Endpoints

- `GET /` - Serves the main application interface
- `POST /api/process` - Main content processing endpoint
  - Accepts: `text`, `aiTopic`, `model`, `verbosity`
  - Returns: structured HTML, token usage, cost, theme data

## Important Implementation Details

- Theme detection uses AI analysis of content to determine appropriate color scheme
- Token limits vary by environment (development vs production) for cost control
- Web search results are integrated into AI prompts for enhanced context
- HTML output follows strict templating rules with mandatory table requirements
- Error handling includes retry logic for API failures
- Cost tracking provides transparency for API usage