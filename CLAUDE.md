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
pip install flask openai python-dotenv

# Run development server
python server.py

# The server runs on http://localhost:5000 with debug=True
```

## Environment Setup

Required environment variables in `.env`:
- `OPENAI_API_KEY`: OpenAI API key for content processing
- `BRAVE_API_KEY`: Currently unused but present in config
- `OPENAI_MODEL`: Set to "gpt-4o-mini"

## Key Components

### Content Processing (`server.py:86-149`)
- `/api/process` endpoint handles document structuring
- Theme detection based on content keywords (`extract_theme` function)
- AI prompt engineering for HTML generation with semantic structure

### Styling System
- A4-formatted CSS template with dynamic theme colors
- Responsive tables with rounded borders and alternating row colors
- Fact boxes, stat boxes, and footnotes styling
- Print-optimized styles

### Frontend Features (`templates/index.html`)
- Real-time HTML preview
- Download as HTML or PDF functionality
- Clean, document-focused UI design

## Content Processing Flow

1. User inputs text via textarea
2. Frontend sends text to `/api/process`
3. Backend analyzes content for theme detection
4. OpenAI processes content into structured HTML
5. CSS styling applied with theme-specific colors
6. Formatted HTML returned and displayed

## Visual Design Principles

- A4 document format (21cm width)
- CMYK-inspired color themes based on content
- Professional document styling with borders and spacing
- Table-first approach for data presentation
- Clean typography using Helvetica font family