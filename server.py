from flask import Flask, render_template, request, jsonify
import openai
import os
import requests
import json
from openai import OpenAIError
from config import get_config
from newspaper import Article
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

app = Flask(__name__)

# Load configuration (fresh import to avoid caching issues)
config = get_config()
openai.api_key = config.OPENAI_API_KEY
if not openai.api_key:
    raise ValueError("Please set your OPENAI_API_KEY environment variable.")

# Global configuration variables
API_TIMEOUT = config.API_TIMEOUT
MAX_RETRIES = config.MAX_RETRIES
MAX_TOKENS_CONFIG = config.MAX_TOKENS
BRAVE_API_KEY = config.BRAVE_API_KEY

# Log configuration on startup
print(f"INFO: RENDER env var = {os.getenv('RENDER', 'NOT_SET')}")
print(f"INFO: ENVIRONMENT env var = {os.getenv('ENVIRONMENT', 'NOT_SET')}")
print(f"INFO: Running in {config.ENVIRONMENT} mode")
print(f"INFO: API timeout set to {API_TIMEOUT}s, max retries: {MAX_RETRIES}")
print(f"INFO: Token limits - Concise: {MAX_TOKENS_CONFIG['Concise']}, Detailed: {MAX_TOKENS_CONFIG['Detailed']}, Comprehensive: {MAX_TOKENS_CONFIG['Comprehensive']}")

def web_search(query, num_results=3):
    """Search the web using Brave Search API"""
    if not BRAVE_API_KEY:
        return []
    
    try:
        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": BRAVE_API_KEY
        }
        
        params = {
            "q": query,
            "count": num_results,
            "country": "US",
            "search_lang": "en",
            "ui_lang": "en-US"
        }
        
        response = requests.get("https://api.search.brave.com/res/v1/web/search", 
                              headers=headers, params=params, timeout=5)
        
        if response.status_code == 200:
            results = response.json().get('web', {}).get('results', [])
            return [{'title': r.get('title', ''), 'snippet': r.get('description', ''), 'url': r.get('url', '')}
                   for r in results[:num_results]]
    except Exception as e:
        print(f"Web search error: {e}")
    
    return []

def extract_structured_content(element):
    """Extract content while preserving important structure like tables, lists, headings"""
    content_parts = []

    # Process direct children and their descendants more carefully
    def process_element(elem, processed_ids):
        if id(elem) in processed_ids:
            return []

        parts = []
        processed_ids.add(id(elem))

        if elem.name == 'table':
            table_text = "\n[TABLE]\n"
            rows = elem.find_all('tr')
            for row in rows:
                cells = row.find_all(['th', 'td'])
                row_text = ' | '.join([cell.get_text(strip=True) for cell in cells if cell.get_text(strip=True)])
                if row_text.strip():
                    table_text += row_text + "\n"
            table_text += "[/TABLE]\n"
            parts.append(table_text)

        elif elem.name in ['ol', 'ul']:
            list_items = elem.find_all('li')
            if list_items:
                list_text = "\n[LIST]\n"
                for i, item in enumerate(list_items):
                    item_text = item.get_text(strip=True)
                    if item_text:
                        prefix = f"{i+1}. " if elem.name == 'ol' else "• "
                        list_text += f"{prefix}{item_text}\n"
                list_text += "[/LIST]\n"
                parts.append(list_text)

        elif elem.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            heading_text = elem.get_text(strip=True)
            if heading_text:
                parts.append(f"\n[HEADING] {heading_text} [/HEADING]\n")

        elif elem.name in ['p', 'div']:
            text_content = elem.get_text(strip=True)
            if text_content and len(text_content) > 15:
                # Only add if it doesn't contain nested structured elements we've already processed
                has_nested_structure = elem.find_all(['table', 'ol', 'ul'])
                if not has_nested_structure:
                    parts.append(text_content + "\n")

        return parts

    # Process all elements
    seen_ids = set()
    all_elements = element.find_all(['table', 'ol', 'ul', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'div'])

    for elem in all_elements:
        if elem.parent and elem.parent.name in ['table', 'ol', 'ul']:
            continue  # Skip elements that are part of structured content

        parts = process_element(elem, seen_ids)
        content_parts.extend(parts)

    return '\n'.join(content_parts)

def extract_article_content(url):
    """Extract article content from URL using multiple methods"""
    try:
        # Method 1: Try newspaper3k first (best for news articles)
        try:
            article = Article(url)
            article.download()
            article.parse()

            if article.text and len(article.text.strip()) > 200:
                return {
                    'title': article.title or 'Article',
                    'text': article.text.strip(),
                    'author': getattr(article, 'authors', []),
                    'publish_date': str(article.publish_date) if article.publish_date else None,
                    'method': 'newspaper3k'
                }
        except Exception as e:
            print(f"Newspaper3k extraction failed: {e}")

        # Method 2: Fallback to BeautifulSoup for general web content
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header", "aside"]):
            script.decompose()

        # Try to find main content areas (enhanced for recipe sites)
        content_selectors = [
            'article', 'main', '.content', '.post-content', '.entry-content',
            '.article-content', '.post-body', '.story-body', '.article-body'
        ]

        content_text = ""
        title = ""

        # Check for WPRM (WP Recipe Maker) recipe containers first
        wprm_recipe = soup.find('div', class_=lambda x: x and 'wprm-recipe-container' in str(x))
        if wprm_recipe:
            wprm_content = extract_structured_content(wprm_recipe)
            if len(wprm_content) > 500:  # Substantial recipe content
                content_text = wprm_content

        # Extract title
        title_tag = soup.find('title')
        if title_tag:
            title = title_tag.get_text().strip()

        # Try to find content using selectors with enhanced structured extraction
        article_content = ""
        for selector in content_selectors:
            elements = soup.select(selector)
            if elements:
                for element in elements:
                    structured_text = extract_structured_content(element)
                    if len(structured_text) > len(article_content):
                        article_content = structured_text
                break

        # Combine WPRM recipe content with article content if both exist
        if content_text and article_content:
            # WPRM content first (recipe), then article content (context/tips)
            content_text = content_text + "\n\n" + article_content
        elif article_content and not content_text:
            content_text = article_content

        # If no specific content found, extract from body with structure preservation
        if not content_text:
            body = soup.find('body')
            if body:
                content_text = extract_structured_content(body)

        if content_text and len(content_text.strip()) > 200:
            return {
                'title': title or 'Web Article',
                'text': content_text.strip(),
                'author': [],
                'publish_date': None,
                'method': 'beautifulsoup'
            }

        return None

    except Exception as e:
        print(f"Article extraction error for {url}: {e}")
        return None

A4_CSS_TEMPLATE = """.a4 {{
    width: 21cm;
    max-width: 95%;
    min-height: 29.7cm;
    padding: 0.6cm;
    background: white;
    box-sizing: border-box;
    margin: 10px auto;
    font-family: Helvetica, Arial, sans-serif;
    font-size: 16px;
    line-height: 1.6;
    transform-origin: top center;
}}
@media (max-width: 1600px) {{
    .a4 {{
        width: 18cm;
        max-width: 90%;
    }}
}}
html, body {{
    height: 100%;
    margin: 0;
    padding: 0;
    font-family: Helvetica, Arial, sans-serif;
    background: #f6f7f8;
    color: #000000;
    display: box;
    align-items: center;
    justify-content: center;
    line-height: 1.6;
}}
h1 {{
    font-size: 38px;
    font-family: Helvetica, Arial, sans-serif;
    font-weight: bold;
    margin-bottom: 20px;
    margin-top: 0px;
    line-height: 1.3;
}}
h2 {{
    font-size: 24px;
    margin-top: 0px;
    margin-bottom: 10px;
}}
p {{
    margin: 6px 0 12px 0;
    line-height: 1.6;
    font-size: 16px;
    font-family: Helvetica, Arial, sans-serif;
}}
.card {{
    background: {theme_color}1a;
    border-radius: 12px;
    padding: 18px;
    box-shadow: 0 6px 18px rgba(0, 0, 0, 0.06);
    border: 1px solid #dfe6ea;
}}
table {{
    border-collapse: separate;
    border-spacing: 0;
    width: 100%;
    margin: 10px 0 20px 0;
    border: 1.5px solid #000000;
    border-radius: 8px;
    overflow: hidden;
    line-height: 1.4;
}}
thead tr {{
    background: {theme_color};
    color: #fff;
    line-height: 1.4;
}}
thead th {{
    padding: 10px 12px;
    text-align: left;
    font-weight: 700;
    border-right: 1.5px solid #000000;
}}
thead th:last-child {{
    border-right: none;
}}
tbody td {{
    padding: 10px 12px;
    border-top: 1.5px solid rgb(0, 0, 0);
    border-right: 1.5px solid #000;
}}
tbody td:last-child {{
    border-right: none;
}}
tbody tr:nth-child(odd) {{
    background: #ffffff;
}}
tbody tr:nth-child(even) {{
    background: #f6f6f6;
}}
tfoot td {{
    padding: 10px 12px;
    border-top: 1.5px solid rgb(0, 0, 0);
    font-weight: 600;
    background: {theme_color}13;
}}
.diagram {{
    display: flex;
    justify-content: center;
    margin: 12px auto;
    padding: 10px 12px;
    overflow: visible;
    height: 100px;
}}
.small {{
    max-width: 420px;
}}
ul {{
    margin: 6px 0 12px 18px;
}}
code {{
    background: #eef2f4;
    padding: 2px 6px;
    border-radius: 4px;
    font-family: monospace;
}}
.note {{
    font-size: 13px;
    color: #444;
    margin-top: 8px;
}}
.fact {{
    border-left: 6px solid {theme_color};
    padding: 12px 16px;
    margin: 10px 0;
}}
.fact strong,
.fact::first-line {{
    font-weight: bold;
}}
.stat-grid {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 12px;
    margin: 12px 0 18px;
}}
.stat {{
    text-align: center;
    padding: 12px 10px;
    border: 1.5px solid #000;
    border-radius: 10px;
    background: {theme_color}27;
}}
.stat .big {{
    font-size: 28px;
    color: {theme_color};
    font-weight: 800;
    line-height: 1.1;
}}
.stat .sub {{
    font-size: 14px;
    color: {theme_color};
    line-height: 1.3;
    margin: 10px 0;
}}
.figure {{
    float: right;
    width: 180px;
    margin: 0 0 12px 16px;
}}
.figure > svg {{
    display: block;
    width: 100%;
    height: auto;
    overflow: visible;
}}
.figure .caption {{
    display: block;
    max-width: 100%;
    text-align: center;
    font-size: 13px;
    line-height: 1.35;
    color: {theme_color};
}}
.timeline {{
    position: relative;
    margin: 20px 0 20px 60px;
    padding: 0;
    font-family: Helvetica, Arial, sans-serif;
}}
.timeline::before {{
    content: '';
    position: absolute;
    left: 50px;
    top: 0;
    bottom: 0;
    width: 2px;
    background: {theme_color};
}}
.timeline-item {{
    position: relative;
    margin-bottom: 24px;
    padding-left: 70px;
    font-family: Helvetica, Arial, sans-serif;
}}
.timeline-item::before {{
    content: '';
    position: absolute;
    left: 44px;
    top: 50%;
    transform: translateY(-50%);
    width: 12px;
    height: 12px;
    border-radius: 50%;
    background: {theme_color};
    border: 3px solid #fff;
    box-shadow: 0 0 0 2px {theme_color};
}}
.timeline-date {{
    position: absolute;
    left: -10px;
    top: 50%;
    transform: translateY(-50%);
    font-size: 12px;
    font-weight: 600;
    color: {theme_color};
    writing-mode: vertical-rl;
    text-orientation: mixed;
    line-height: 1.2;
    font-family: Helvetica, Arial, sans-serif;
    width: 40px;
}}
.timeline-content {{
    background: #fff;
    border: 1px solid {theme_color}40;
    border-radius: 8px;
    padding: 12px 16px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    font-family: Helvetica, Arial, sans-serif;
}}
.timeline-title {{
    font-size: 14px;
    font-weight: 600;
    color: {theme_color};
    margin: 0 0 6px 0;
    font-family: Helvetica, Arial, sans-serif;
}}
.timeline-description {{
    font-size: 13px;
    color: #333;
    line-height: 1.4;
    margin: 0;
    font-family: Helvetica, Arial, sans-serif;
}}
.citations {{
    margin: 20px 0;
    padding: 16px;
    background: {theme_color}0d;
    border-left: 4px solid {theme_color};
    border-radius: 0 8px 8px 0;
}}
.citations h3 {{
    font-size: 14px;
    font-weight: 600;
    color: {theme_color};
    margin: 0 0 12px 0;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}
.citation {{
    display: flex;
    align-items: flex-start;
    margin: 8px 0;
    padding: 8px 0;
    border-bottom: 1px solid {theme_color}20;
}}
.citation:last-child {{
    border-bottom: none;
}}
.citation-number {{
    flex-shrink: 0;
    width: 24px;
    height: 24px;
    background: {theme_color};
    color: white;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;
    font-weight: 600;
    margin-right: 12px;
    margin-top: 2px;
}}
.citation-content {{
    flex-grow: 1;
}}
.citation-title {{
    font-weight: 600;
    color: {theme_color};
    font-size: 14px;
    line-height: 1.3;
    margin: 0 0 4px 0;
    text-decoration: none;
    display: inline-block;
    transition: all 0.2s ease;
}}
.citation-title:hover {{
    color: {theme_color};
    text-decoration: underline;
    transform: translateX(2px);
}}
.citation-snippet {{
    color: #555;
    font-size: 13px;
    line-height: 1.4;
    margin: 0;
    font-style: italic;
}}
@media print {{
    body {{
        background: none;
        margin: 0;
    }}
    .a4 {{
        width: auto;
        min-height: auto;
        padding: 0;
        box-shadow: none;
        page-break-after: always;
    }}
    table {{
        font-size: 13px;
    }}
    h2 {{
        font-size: 18px;
    }}
}}"""

THEME_COLORS = {
    "finance": "#28a745",      # Green - money/growth
    "tech": "#007bff",         # Blue - digital/innovation
    "health": "#e83e8c",       # Pink - healthcare/wellness
    "travel": "#dc3545",       # Red - movement/adventure
    "food": "#fd7e14",         # Orange - warmth/appetite
    "default": "#6c757d"       # Gray - neutral
}

@app.route("/")
def index():
    return render_template("index.html")

def extract_theme(text: str) -> str:
    """AI-powered theme detection using OpenAI to analyze content and suggest appropriate theme"""
    try:
        # Use comprehensive analysis for better accuracy
        theme_prompt = f"""You are an expert content analyst. Analyze the following text and determine the most appropriate visual theme category based on the primary subject matter and content focus.

Text to analyze:
"{text[:800]}"

Available theme categories:
- finance: Banking, money, investments, economics, business finance, financial markets, accounting, budgets, costs, revenue, profits, loans, taxes
- health: Medical topics, healthcare, wellness, pharmaceuticals, clinical research, diseases, treatments, hospitals, doctors, patients, therapy
- tech: Technology, software, AI, digital systems, computing, programming, apps, platforms, internet, web development, data science
- travel: Transportation, travel, tourism, cars, flights, trains, buses, public transit, airlines, hotels, destinations, trip planning, vehicle rental, road trips, airports, travel guides, vacation planning
- food: Cooking, recipes, restaurants, cuisine, nutrition, ingredients, food preparation, culinary arts, dining, beverages, meal planning, kitchen tools
- default: General topics, lifestyle, education, or content that doesn't clearly fit the specialized categories above

Instructions:
1. Focus on the PRIMARY subject matter, not just individual keywords
2. Consider the overall context and purpose of the content
3. If the content spans multiple categories, choose the most dominant one
4. Be specific - ALL transportation content (cars, flights, trains, tourism, vehicles) should be "travel", not "default"
5. IMPORTANT: Car content, automotive reviews, vehicle comparisons = "travel" theme

Respond with ONLY the theme category name: finance, health, tech, travel, food, or default"""

        response = openai.chat.completions.create(
            model="gpt-4o",  # Use more powerful model for better accuracy
            messages=[
                {"role": "system", "content": "You are a precise content categorization expert. Always respond with exactly one word: the theme category name."},
                {"role": "user", "content": theme_prompt}
            ],
            max_tokens=20,  # Allow some flexibility for response
            temperature=0,  # Maximum consistency
            timeout=30  # Shorter timeout for theme detection
        )
        
        detected_theme = response.choices[0].message.content.strip().lower()

        # Validate the response is one of our supported themes
        valid_themes = ["finance", "health", "tech", "travel", "food", "default"]
        if detected_theme in valid_themes:
            print(f"DEBUG: AI detected theme: {detected_theme} for content: {text[:100]}...")
            return detected_theme
        else:
            print(f"DEBUG: AI returned invalid theme '{detected_theme}', using default for content: {text[:100]}...")
            return "default"
            
    except Exception as e:
        print(f"DEBUG: Theme detection failed: {e}, using default for content: {text[:100]}...")
        return "default"

def generate_search_query(text: str, theme: str) -> str:
    """AI-powered search query generation with robust fallback"""
    # Robust fallback function first
    def create_fallback_query():
        words = text.lower().split()
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those'}
        meaningful_words = [w for w in words[:25] if len(w) > 3 and w not in stop_words and w.isalpha()]

        if meaningful_words:
            return f"{' '.join(meaningful_words[:4])} {theme} guidelines"
        else:
            return f"{theme} information guidelines"

    try:
        # Try AI-powered query generation
        query_prompt = f"""Create a web search query for background information about this content.

Content (theme: {theme}):
"{text[:500]}"

Extract 2-4 key concepts and create a search query (max 7 words) that would find relevant context, guidelines, or background information. Focus on concepts, not exact phrases.

Query:"""

        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": query_prompt}],
            max_tokens=25,
            temperature=0.2,
            timeout=15
        )

        ai_query = response.choices[0].message.content.strip().replace('"', '').replace("Query:", "").strip()

        # Validate AI response
        if len(ai_query.split()) > 8 or len(ai_query) < 10:
            print(f"DEBUG: AI query invalid length, using fallback. AI returned: '{ai_query}'")
            return create_fallback_query()

        print(f"DEBUG: AI generated search query: '{ai_query}' for theme: {theme}")
        return ai_query

    except Exception as e:
        print(f"DEBUG: AI query generation failed ({e}), using fallback")
        return create_fallback_query()

def calculate_cost(model_name, prompt_tokens, completion_tokens):
    """Calculate cost based on model pricing (as of 2024)"""
    pricing = {
        "GPT-4o-mini": {"input": 0.00015, "output": 0.0006},  # per 1k tokens
        "Gemini Pro 2.5": {"input": 0.000125, "output": 0.000375},  # estimated
        "GPT-5": {"input": 0.005, "output": 0.015}  # estimated premium pricing
    }
    
    if model_name not in pricing:
        model_name = "GPT-5"  # default
    
    input_cost = (prompt_tokens / 1000) * pricing[model_name]["input"]
    output_cost = (completion_tokens / 1000) * pricing[model_name]["output"]
    
    return input_cost + output_cost

@app.route("/api/process", methods=["POST"])
def process():
    data = request.json
    input_text = data.get("text", "").strip()
    ai_topic = data.get("aiTopic", "").strip()
    article_url = data.get("articleUrl", "").strip()
    selected_model = data.get("model", "GPT-5")
    verbosity = data.get("verbosity", "Detailed")

    if not input_text and not ai_topic and not article_url:
        return jsonify({"error": "No input text, AI topic, or URL provided."})

    # Handle URL extraction first if provided
    if article_url:
        print(f"DEBUG: Extracting article from URL: {article_url}")
        article_data = extract_article_content(article_url)
        if not article_data:
            return jsonify({"error": "Failed to extract content from the provided URL. Please check the URL and try again."})

        input_text = f"Article: {article_data['title']}\n\n{article_data['text']}"
        print(f"DEBUG: Successfully extracted {len(input_text)} characters from URL")
        print(f"DEBUG: Article title: {article_data['title']}")
        print(f"DEBUG: Content preview: {input_text[:500]}...")

    # Determine processing mode (URL extraction is treated as document processing)
    is_ai_research = bool(ai_topic and not input_text)
    processing_text = ai_topic if is_ai_research else input_text
    
    theme = extract_theme(processing_text)
    theme_color = THEME_COLORS.get(theme, THEME_COLORS["default"])
    
    print(f"DEBUG: Processing mode: {'AI Research' if is_ai_research else 'Document Processing'}")
    print(f"DEBUG: Detected theme: {theme}, color: {theme_color}")
    print(f"DEBUG: Selected model: {selected_model}, Verbosity: {verbosity}")
    print(f"DEBUG: Input text length: {len(processing_text)} characters")

    # Handle AI Research vs Document Processing
    if is_ai_research:
        # For AI research mode, do extensive web search
        search_query = ai_topic
        search_results = web_search(search_query, num_results=5)
        print(f"DEBUG: AI Research - Found {len(search_results)} web search results")
        
        # Create research context
        search_context = f"\n\nWeb Research Results for '{ai_topic}' (USE THESE FOR CITATIONS):\n"
        if search_results:
            for i, result in enumerate(search_results, 1):
                search_context += f"[{i}] Title: {result['title']}\n    URL: {result['url']}\n    Snippet: {result['snippet']}\n\n"
        else:
            search_context += "No specific web results found. Use general knowledge.\n"
            
        # Use the topic as the base text for processing
        processing_content = f"Research Topic: {ai_topic}{search_context}"
    else:
        # Standard document processing with AI-powered search query generation
        search_query = generate_search_query(input_text, theme)
        search_results = web_search(search_query, num_results=2)
        print(f"DEBUG: Document Processing - Search query: '{search_query}' - Found {len(search_results)} web search results")
        
        search_context = ""
        if search_results:
            search_context = f"\n\nAdditional Context from Web Search (USE THESE FOR CITATIONS):\n"
            for i, result in enumerate(search_results, 1):
                search_context += f"[{i}] Title: {result['title']}\n    URL: {result['url']}\n    Snippet: {result['snippet']}\n\n"
        
        processing_content = f"{input_text}{search_context}"

    # Create verbosity-specific instructions
    verbosity_instructions = {
        "Concise": "Keep content brief and focused. Use 1-2 paragraphs per section, 2-3 stat boxes, and 1 small table. Prioritize key information only.",
        "Detailed": "Provide balanced detail. Use 2-3 paragraphs per section, 3 stat boxes, 1-2 comprehensive tables, and visual timelines when chronological data is present. Include supporting analysis.",
        "Comprehensive": "Provide EXTENSIVE analysis with maximum detail. REQUIREMENTS: 4-6 paragraphs per section, 6+ stat boxes, 3-4 detailed tables, visual timelines (when applicable), comparison tables, market analysis, trend data, future projections, case studies, and deep contextual insights. Make the document comprehensive like a research report."
    }
    
    # Determine content type instructions
    if is_ai_research:
        content_instruction = f"""
RESEARCH MODE: You are researching and creating a comprehensive document about: "{ai_topic}"

Use the web search results provided and your knowledge to create an authoritative, well-researched document. 
Focus on current trends, statistics, and factual information. Create original content based on research.

Verbosity Level: {verbosity} - {verbosity_instructions[verbosity]}
"""
    else:
        content_instruction = f"""
DOCUMENT PROCESSING MODE: Structure and enhance the provided text content.

CRITICAL INSTRUCTIONS - FOLLOW EXACTLY:
- PRESERVE EVERY DETAIL from the source content - do not summarize or omit ANY information
- STRUCTURE EVERY numbered/bulleted list into comprehensive HTML tables
- INCLUDE ALL items from source lists - if source has 16 items, your table MUST have 16 rows
- NEVER select highlights or examples - include COMPLETE lists with ALL entries
- EXPAND on details rather than condensing them
- ADD relevant context from web search results where applicable

SPECIAL HANDLING for RECIPE CONTENT:
- When you see [LIST] markers, these represent recipe steps, ingredients, or instructions
- Convert ALL [LIST] content into detailed HTML tables with proper step numbers
- For recipe instructions: create tables with columns like "Step", "Action", "Details"
- For ingredients: create tables with "Ingredient", "Amount", "Notes" columns
- NEVER summarize recipe steps - include every single instruction exactly as provided
- RECIPE STEPS MUST BE IN TABLES - this is mandatory for recipe content
- If you detect recipe/cooking content, you MUST create step-by-step instruction tables

This is DOCUMENT PROCESSING, not summarization - maintain ALL original content

Verbosity Level: {verbosity} - {verbosity_instructions[verbosity]}
"""

    prompt = f"""
{content_instruction}

Create a professional document following this EXACT structure (like a medical/scientific paper):

<h1>Descriptive Title</h1>

<div class="fact card">
<strong>Key insight:</strong> Main takeaway from the content
</div>

<h2>Section Name</h2>
<p>Paragraph content explaining the topic.</p>
<p>Additional analysis and insights.</p>

<div class="stat-grid">
  <div class="stat">
    <div class="big">NUMBER</div>
    <div class="sub">Description of what this number means</div>
  </div>
  <div class="stat">
    <div class="big">NUMBER</div>
    <div class="sub">Description of what this number means</div>
  </div>
  <div class="stat">
    <div class="big">NUMBER</div>
    <div class="sub">Description of what this number means</div>
  </div>
</div>

<h2>Another Section</h2>
<p>More content and analysis.</p>

<div class="fact card">
<strong>Key finding:</strong> Important fact or insight from the analysis.
</div>

<h2>Data Table</h2>
<table>
  <thead>
    <tr>
      <th>Column 1</th>
      <th>Column 2</th>
      <th>Column 3</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Data</td>
      <td>Data</td>
      <td>Data</td>
    </tr>
  </tbody>
</table>

<h2>Recipe Instructions (REQUIRED for recipe content)</h2>
<table>
  <thead>
    <tr>
      <th>Step</th>
      <th>Instruction</th>
      <th>Details</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>1</td>
      <td>Combine ingredients</td>
      <td>Mix sesame paste, soy sauce, and other seasonings</td>
    </tr>
    <tr>
      <td>2</td>
      <td>Cook noodles</td>
      <td>Boil according to package directions</td>
    </tr>
  </tbody>
</table>

<h2>Summary</h2>
<ul>
  <li>Key point 1</li>
  <li>Key point 2</li>
  <li>Key point 3</li>
</ul>

<p style="font-weight: bold;">
Final summary and key takeaways with bold formatting for emphasis.
</p>

<div class="citations">
  <h3>Sources & References</h3>
  <div class="citation">
    <div class="citation-number">1</div>
    <div class="citation-content">
      <a href="https://example.com" class="citation-title" target="_blank">Source Title</a>
      <div class="citation-snippet">Brief description of what was referenced from this source.</div>
    </div>
  </div>
  <div class="citation">
    <div class="citation-number">2</div>
    <div class="citation-content">
      <a href="https://example.com" class="citation-title" target="_blank">Another Source</a>
      <div class="citation-snippet">Description of information used from this source.</div>
    </div>
  </div>
</div>

MANDATORY TABLE REQUIREMENTS:
- EVERY document MUST contain at least 1-2 tables
- Convert ANY structured information into tables:
  • Lists of items → table rows
  • Comparisons → comparison table
  • Categories/classifications → category table
  • Steps/processes → process table
  • Key-value pairs → data table
  • Timeline events → visual timeline (NOT table)
- Even simple bullet points MUST become tables with headers like "Item", "Description", "Details"
- INCLUDE ALL numbered/bulleted items from the source - do NOT select only a few examples
- If there are N items in a list, create tables with ALL N items, not just highlights or summaries

TIMELINE STRUCTURE (when events/dates are present):
Use this HTML structure for chronological events WITHIN content sections, NOT after summary:
<div class="timeline">
  <div class="timeline-item">
    <div class="timeline-date">2024</div>
    <div class="timeline-content">
      <div class="timeline-title">Event Title</div>
      <div class="timeline-description">Event description...</div>
    </div>
  </div>
</div>

DOCUMENT STRUCTURE ORDER:
1. Main content sections with analysis
2. Timeline (if applicable) within relevant content sections
3. Tables and data analysis
4. Summary section
5. Citations section (ALWAYS LAST - include ALL web search sources used)

COMPREHENSIVE VERBOSITY EXTRA REQUIREMENTS:
{f"- CREATE MULTIPLE SECTIONS (6+ sections minimum) with extensive analysis" if verbosity == "Comprehensive" else ""}
{f"- ADD VISUAL TIMELINE with dates/milestones (use timeline HTML structure)" if verbosity in ["Detailed", "Comprehensive"] else ""}
{f"- CREATE COMPARISON TABLES (before/after, competitor analysis, etc.)" if verbosity == "Comprehensive" else ""}
{f"- INCLUDE MARKET ANALYSIS section with industry data" if verbosity == "Comprehensive" else ""}
{f"- ADD FUTURE PROJECTIONS/TRENDS section" if verbosity == "Comprehensive" else ""}
{f"- CREATE DETAILED STATISTICAL BREAKDOWN with 6+ stat boxes" if verbosity == "Comprehensive" else ""}
{f"- INCLUDE CASE STUDIES or EXAMPLES section" if verbosity == "Comprehensive" else ""}
{f"- ADD RISK ANALYSIS or IMPACT ASSESSMENT table" if verbosity == "Comprehensive" else ""}

CRITICAL RULES:
- NO nested cards or divs inside cards
- Use EXACT stat structure with .big and .sub classes
- ALL stat boxes MUST be inside <div class="stat-grid"> container
- NEVER put stat boxes outside the stat-grid div
- Each stat box MUST follow this exact format: <div class="stat"><div class="big">NUMBER</div><div class="sub">description</div></div>
- Keep paragraphs concise and professional
- Extract all numbers into stat boxes
- CREATE TABLES FROM EVERYTHING POSSIBLE
- Return ONLY HTML (no explanations, no backticks)

CITATIONS REQUIREMENTS:
- ALWAYS include a citations section at the end with ALL web search sources
- Use the provided web search results to create accurate citations with REAL CLICKABLE LINKS
- Each citation must have: numbered badge, <a href="ACTUAL_URL" class="citation-title" target="_blank">TITLE</a>, and snippet description
- Use the exact URLs provided in the web search results
- Number citations sequentially (1, 2, 3...)
- If no web search results provided, create citations section anyway with note "No external sources used"

Content to process:
{processing_content}
    """

    try:
        # Map model names to actual model IDs
        model_map = {
            "GPT-4o-mini": "gpt-4o-mini",
            "Gemini Pro 2.5": "gpt-4o-mini",  # fallback to GPT-4o-mini for now
            "GPT-5": "gpt-4o"  # Use the most capable model available (GPT-4o is the latest standard model)
        }
        
        actual_model = model_map.get(selected_model, "gpt-4o")
        
        # Retry logic for connection errors
        max_retries = MAX_RETRIES
        for attempt in range(max_retries):
            try:
                # Set max tokens based on verbosity and environment
                max_tokens = MAX_TOKENS_CONFIG.get(verbosity, MAX_TOKENS_CONFIG["Detailed"])
                
                print(f"DEBUG: Using {max_tokens} tokens for {verbosity} mode with {actual_model} (selected: {selected_model})")
                print(f"DEBUG: Prompt length: {len(prompt)} characters")

                response = openai.chat.completions.create(
                    model=actual_model,
                    messages=[
                        {"role": "system", "content": "You are an expert document analyst and professional HTML formatter. Create highly structured, intelligent documents with deep analysis."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=max_tokens,
                    timeout=API_TIMEOUT
                )

                print(f"DEBUG: Response tokens used: {response.usage.total_tokens if response.usage else 'Unknown'}")
                print(f"DEBUG: Output length: {len(response.choices[0].message.content)} characters")
                break  # Success, exit retry loop
            except Exception as e:
                print(f"DEBUG: Attempt {attempt + 1} failed: {str(e)}")
                if attempt == max_retries - 1:  # Last attempt
                    raise e
                else:
                    import time
                    time.sleep(2)  # Wait 2 seconds before retry

        ai_html = response.choices[0].message.content
        
        # Extract token usage information
        token_usage = response.usage
        prompt_tokens = token_usage.prompt_tokens
        completion_tokens = token_usage.completion_tokens
        total_tokens = token_usage.total_tokens
        
        # Calculate cost
        cost = calculate_cost(selected_model, prompt_tokens, completion_tokens)
        
        print(f"DEBUG: AI response length: {len(ai_html)}")
        print(f"DEBUG: AI response starts with: {ai_html[:100]}")
        print(f"DEBUG: Token usage - Prompt: {prompt_tokens}, Completion: {completion_tokens}, Total: {total_tokens}")
        print(f"DEBUG: Estimated cost: ${cost:.4f}")

        # Clean up any markdown formatting that might have slipped through
        if ai_html.startswith("```html"):
            ai_html = ai_html[7:]
        if ai_html.endswith("```"):
            ai_html = ai_html[:-3]
        ai_html = ai_html.strip()

        # Clean up and validate the AI response
        def clean_html(html_content):
            import re
            # Remove any remaining code block markers
            html_content = re.sub(r'```html\s*', '', html_content)
            html_content = re.sub(r'```\s*$', '', html_content)
            # Ensure proper formatting
            html_content = html_content.strip()
            return html_content
        
        ai_html = clean_html(ai_html)
        print(f"DEBUG: Final HTML contains expected classes: {'class=' in ai_html}")
        print(f"DEBUG: Contains stat-grid: {'stat-grid' in ai_html}")
        print(f"DEBUG: Contains fact: {'fact' in ai_html}")

        if not ai_html.strip():
            print("AI returned empty response:", response)
            return jsonify({"error": "AI returned empty HTML."})

        css_content = A4_CSS_TEMPLATE.format(theme_color=theme_color)
        print(f"DEBUG: CSS content length: {len(css_content)}")
        print(f"DEBUG: Theme color in CSS: {theme_color}")
        
        # Create styled document content only (no full HTML page)
        document_content = f"""
<style>
{css_content}
</style>
<div class="a4">
{ai_html}
</div>
        """
        
        return jsonify({
            "html": document_content,
            "tokens": {
                "prompt": prompt_tokens,
                "completion": completion_tokens,
                "total": total_tokens
            },
            "cost": cost,
            "model": selected_model,
            "theme": theme,
            "theme_color": theme_color
        })

    except OpenAIError as e:
        return jsonify({"error": f"OpenAI API error: {str(e)}"})
    except Exception as e:
        return jsonify({"error": f"Unexpected server error: {str(e)}"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
