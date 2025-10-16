import express from 'express';
import path from 'path';
import { fileURLToPath } from 'url';
import axios from 'axios';
import OpenAI from 'openai';
import { GoogleGenerativeAI } from '@google/generative-ai';
import * as cheerio from 'cheerio';
import { getConfig } from './config.js';
import cors from 'cors';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();

// Load configuration
const config = getConfig();

// Initialize OpenAI
const openai = new OpenAI({
  apiKey: config.OPENAI_API_KEY,
  timeout: config.API_TIMEOUT * 1000
});

if (!config.OPENAI_API_KEY) {
  throw new Error('Please set your OPENAI_API_KEY environment variable.');
}

// Configure Gemini API (optional)
let genAI = null;
if (config.GOOGLE_API_KEY) {
  genAI = new GoogleGenerativeAI(config.GOOGLE_API_KEY);
  console.log('INFO: Gemini API configured');
} else {
  console.log('INFO: GOOGLE_API_KEY/GEMINI_API_KEY not found - Gemini will fallback to OpenAI models');
}

// Global configuration variables
const API_TIMEOUT = config.API_TIMEOUT;
const MAX_RETRIES = config.MAX_RETRIES;
const MAX_TOKENS_CONFIG = config.MAX_TOKENS;
const BRAVE_API_KEY = config.BRAVE_API_KEY;

// Log configuration on startup
console.log(`INFO: RENDER env var = ${process.env.RENDER || 'NOT_SET'}`);
console.log(`INFO: ENVIRONMENT env var = ${process.env.ENVIRONMENT || 'NOT_SET'}`);
console.log(`INFO: Running in ${config.ENVIRONMENT} mode`);
console.log(`INFO: API timeout set to ${API_TIMEOUT}s, max retries: ${MAX_RETRIES}`);
console.log(`INFO: Token limits - Concise: ${MAX_TOKENS_CONFIG.Concise}, Detailed: ${MAX_TOKENS_CONFIG.Detailed}, Comprehensive: ${MAX_TOKENS_CONFIG.Comprehensive}`);

// Middleware
app.use(cors());
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));
app.use(express.static('templates'));

/**
 * Search the web using Brave Search API
 */
async function webSearch(query, numResults = 3) {
  if (!BRAVE_API_KEY) {
    return [];
  }

  try {
    const response = await axios.get('https://api.search.brave.com/res/v1/web/search', {
      headers: {
        'Accept': 'application/json',
        'Accept-Encoding': 'gzip',
        'X-Subscription-Token': BRAVE_API_KEY
      },
      params: {
        q: query,
        count: numResults,
        country: 'US',
        search_lang: 'en',
        ui_lang: 'en-US'
      },
      timeout: 5000
    });

    if (response.status === 200) {
      const results = response.data?.web?.results || [];
      return results.slice(0, numResults).map(r => ({
        title: r.title || '',
        snippet: r.description || '',
        url: r.url || ''
      }));
    }
  } catch (error) {
    console.log(`Web search error: ${error.message}`);
  }

  return [];
}

/**
 * Extract content while preserving important structure like tables, lists, headings
 */
function extractStructuredContent($element) {
  const contentParts = [];
  const processedIds = new Set();

  function processElement(elem) {
    const elemId = elem[0];
    if (processedIds.has(elemId)) {
      return [];
    }

    const parts = [];
    processedIds.add(elemId);

    const tagName = elem[0].name;

    if (tagName === 'table') {
      let tableText = '\n[TABLE]\n';
      elem.find('tr').each((i, row) => {
        const cells = cheerio.load(row)('th, td');
        const rowText = cells.map((j, cell) => {
          return cheerio.load(cell).text().trim();
        }).get().filter(text => text).join(' | ');

        if (rowText.trim()) {
          tableText += rowText + '\n';
        }
      });
      tableText += '[/TABLE]\n';
      parts.push(tableText);
    } else if (tagName === 'ol' || tagName === 'ul') {
      const listItems = elem.find('li');
      if (listItems.length > 0) {
        let listText = '\n[LIST]\n';
        listItems.each((i, item) => {
          const itemText = cheerio.load(item).text().trim();
          if (itemText) {
            const prefix = tagName === 'ol' ? `${i + 1}. ` : '• ';
            listText += `${prefix}${itemText}\n`;
          }
        });
        listText += '[/LIST]\n';
        parts.push(listText);
      }
    } else if (['h1', 'h2', 'h3', 'h4', 'h5', 'h6'].includes(tagName)) {
      const headingText = elem.text().trim();
      if (headingText) {
        parts.push(`\n[HEADING] ${headingText} [/HEADING]\n`);
      }
    } else if (tagName === 'p' || tagName === 'div') {
      const textContent = elem.text().trim();
      if (textContent && textContent.length > 15) {
        const hasNestedStructure = elem.find('table, ol, ul').length > 0;
        if (!hasNestedStructure) {
          parts.push(textContent + '\n');
        }
      }
    }

    return parts;
  }

  // Process all elements
  $element.find('table, ol, ul, h1, h2, h3, h4, h5, h6, p, div').each((i, elem) => {
    const $ = cheerio.load('');
    const $elem = $(elem);
    const parent = $elem.parent();
    if (parent && parent.length > 0 && ['table', 'ol', 'ul'].includes(parent[0]?.name)) {
      return; // Skip elements that are part of structured content
    }

    const parts = processElement($elem);
    contentParts.push(...parts);
  });

  return contentParts.join('\n');
}

/**
 * Extract article content from URL using multiple methods
 */
async function extractArticleContent(url) {
  try {
    // Fetch the page
    const response = await axios.get(url, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
      },
      timeout: 10000
    });

    const $ = cheerio.load(response.data);

    // Remove script and style elements
    $('script, style, nav, footer, header, aside').remove();

    // Try to find main content areas (enhanced for recipe sites)
    const contentSelectors = [
      'article', 'main', '.content', '.post-content', '.entry-content',
      '.article-content', '.post-body', '.story-body', '.article-body'
    ];

    // Check for WPRM recipe content first (priority for recipe sites)
    const wprmRecipe = $('div[class*="wp-recipe-maker"]');
    let contentText = '';

    if (wprmRecipe.length > 0) {
      console.log('DEBUG: Found WPRM recipe container');
      const wprmContent = extractStructuredContent(wprmRecipe);
      if (wprmContent.length > 500) {
        contentText = wprmContent;
      }
    }

    // Extract title
    const titleTag = $('title');
    const title = titleTag.text().trim() || 'Web Article';

    // Try to find content using selectors with enhanced structured extraction
    let articleContent = '';
    for (const selector of contentSelectors) {
      const elements = $(selector);
      if (elements.length > 0) {
        elements.each((i, element) => {
          const structuredText = extractStructuredContent($(element));
          if (structuredText.length > articleContent.length) {
            articleContent = structuredText;
          }
        });
        break;
      }
    }

    // Combine WPRM recipe content with article content if both exist
    if (contentText && articleContent) {
      contentText = contentText + '\n\n' + articleContent;
    } else if (articleContent && !contentText) {
      contentText = articleContent;
    }

    // If no specific content found, extract from body with structure preservation
    if (!contentText) {
      const body = $('body');
      if (body.length > 0) {
        contentText = extractStructuredContent(body);
      }
    }

    if (contentText && contentText.trim().length > 200) {
      return {
        title: title || 'Web Article',
        text: contentText.trim(),
        author: [],
        publish_date: null,
        method: 'cheerio'
      };
    }

    return null;
  } catch (error) {
    console.log(`Article extraction error for ${url}: ${error.message}`);
    return null;
  }
}

// Theme colors
const THEME_COLORS = {
  finance: '#28a745',      // Green - money/growth
  tech: '#007bff',         // Blue - digital/innovation
  health: '#e83e8c',       // Pink - healthcare/wellness
  travel: '#dc3545',       // Red - movement/adventure
  food: '#fd7e14',         // Orange - warmth/appetite
  default: '#6c757d'       // Gray - neutral
};

// A4 CSS Template
const A4_CSS_TEMPLATE = `.a4 {
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
}
@media (max-width: 1600px) {
    .a4 {
        width: 18cm;
        max-width: 90%;
    }
}
html, body {
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
}
h1 {
    font-size: 38px;
    font-family: Helvetica, Arial, sans-serif;
    font-weight: bold;
    margin-bottom: 20px;
    margin-top: 0px;
    line-height: 1.3;
}
h2 {
    font-size: 24px;
    margin-top: 0px;
    margin-bottom: 10px;
}
p {
    margin: 6px 0 12px 0;
    line-height: 1.6;
    font-size: 16px;
    font-family: Helvetica, Arial, sans-serif;
}
.card {
    background: THEME_COLOR1a;
    border-radius: 12px;
    padding: 18px;
    box-shadow: 0 6px 18px rgba(0, 0, 0, 0.06);
    border: 1px solid #dfe6ea;
}
table {
    border-collapse: separate;
    border-spacing: 0;
    width: 100%;
    margin: 10px 0 20px 0;
    border: 1.5px solid #000000;
    border-radius: 8px;
    overflow: hidden;
    line-height: 1.4;
}
thead tr {
    background: THEME_COLOR;
    color: #fff;
    line-height: 1.4;
}
thead th {
    padding: 10px 12px;
    text-align: left;
    font-weight: 700;
    border-right: 1.5px solid #000000;
}
thead th:last-child {
    border-right: none;
}
tbody td {
    padding: 10px 12px;
    border-top: 1.5px solid rgb(0, 0, 0);
    border-right: 1.5px solid #000;
}
tbody td:last-child {
    border-right: none;
}
tbody tr:nth-child(odd) {
    background: #ffffff;
}
tbody tr:nth-child(even) {
    background: #f6f6f6;
}
tfoot td {
    padding: 10px 12px;
    border-top: 1.5px solid rgb(0, 0, 0);
    font-weight: 600;
    background: THEME_COLOR13;
}
.diagram {
    display: flex;
    justify-content: center;
    margin: 12px auto;
    padding: 10px 12px;
    overflow: visible;
    height: 100px;
}
.small {
    max-width: 420px;
}
ul {
    margin: 6px 0 12px 18px;
}
code {
    background: #eef2f4;
    padding: 2px 6px;
    border-radius: 4px;
    font-family: monospace;
}
.note {
    font-size: 13px;
    color: #444;
    margin-top: 8px;
}
.fact {
    border-left: 6px solid THEME_COLOR;
    padding: 12px 16px;
    margin: 10px 0;
}
.fact strong,
.fact::first-line {
    font-weight: bold;
}
.stat-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 12px;
    margin: 12px 0 18px;
}
.stat {
    text-align: center;
    padding: 12px 10px;
    border: 1.5px solid #000;
    border-radius: 10px;
    background: THEME_COLOR27;
}
.stat .big {
    font-size: 28px;
    color: THEME_COLOR;
    font-weight: 800;
    line-height: 1.1;
}
.stat .sub {
    font-size: 14px;
    color: THEME_COLOR;
    line-height: 1.3;
    margin: 10px 0;
}
.figure {
    float: right;
    width: 180px;
    margin: 0 0 12px 16px;
}
.figure > svg {
    display: block;
    width: 100%;
    height: auto;
    overflow: visible;
}
.figure .caption {
    display: block;
    max-width: 100%;
    text-align: center;
    font-size: 13px;
    line-height: 1.35;
    color: THEME_COLOR;
}
.timeline {
    position: relative;
    margin: 20px 0 20px 60px;
    padding: 0;
    font-family: Helvetica, Arial, sans-serif;
}
.timeline::before {
    content: '';
    position: absolute;
    left: 50px;
    top: 0;
    bottom: 0;
    width: 2px;
    background: THEME_COLOR;
}
.timeline-item {
    position: relative;
    margin-bottom: 24px;
    padding-left: 70px;
    font-family: Helvetica, Arial, sans-serif;
}
.timeline-item::before {
    content: '';
    position: absolute;
    left: 44px;
    top: 50%;
    transform: translateY(-50%);
    width: 12px;
    height: 12px;
    border-radius: 50%;
    background: THEME_COLOR;
    border: 3px solid #fff;
    box-shadow: 0 0 0 2px THEME_COLOR;
}
.timeline-date {
    position: absolute;
    left: -10px;
    top: 50%;
    transform: translateY(-50%);
    font-size: 12px;
    font-weight: 600;
    color: THEME_COLOR;
    writing-mode: vertical-rl;
    text-orientation: mixed;
    line-height: 1.2;
    font-family: Helvetica, Arial, sans-serif;
    width: 40px;
}
.timeline-content {
    background: #fff;
    border: 1px solid THEME_COLOR40;
    border-radius: 8px;
    padding: 12px 16px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    font-family: Helvetica, Arial, sans-serif;
}
.timeline-title {
    font-size: 14px;
    font-weight: 600;
    color: THEME_COLOR;
    margin: 0 0 6px 0;
    font-family: Helvetica, Arial, sans-serif;
}
.timeline-description {
    font-size: 13px;
    color: #333;
    line-height: 1.4;
    margin: 0;
    font-family: Helvetica, Arial, sans-serif;
}
.citations {
    margin: 20px 0;
    padding: 16px;
    background: THEME_COLOR0d;
    border-left: 4px solid THEME_COLOR;
    border-radius: 0 8px 8px 0;
}
.citations h3 {
    font-size: 14px;
    font-weight: 600;
    color: THEME_COLOR;
    margin: 0 0 12px 0;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
.citation {
    display: flex;
    align-items: flex-start;
    margin: 8px 0;
    padding: 8px 0;
    border-bottom: 1px solid THEME_COLOR20;
}
.citation:last-child {
    border-bottom: none;
}
.citation-number {
    flex-shrink: 0;
    width: 24px;
    height: 24px;
    background: THEME_COLOR;
    color: white;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;
    font-weight: 600;
    margin-right: 12px;
    margin-top: 2px;
}
.citation-content {
    flex-grow: 1;
}
.citation-title {
    font-weight: 600;
    color: THEME_COLOR;
    font-size: 14px;
    line-height: 1.3;
    margin: 0 0 4px 0;
    text-decoration: none;
    display: inline-block;
    transition: all 0.2s ease;
}
.citation-title:hover {
    color: THEME_COLOR;
    text-decoration: underline;
    transform: translateX(2px);
}
.citation-snippet {
    color: #555;
    font-size: 13px;
    line-height: 1.4;
    margin: 0;
    font-style: italic;
}
@media print {
    body {
        background: none;
        margin: 0;
    }
    .a4 {
        width: auto;
        min-height: auto;
        padding: 0;
        box-shadow: none;
        page-break-after: always;
    }
    table {
        font-size: 13px;
    }
    h2 {
        font-size: 18px;
    }
}`;

/**
 * AI-powered theme detection using OpenAI to analyze content and suggest appropriate theme
 */
async function extractTheme(text) {
  try {
    const themePrompt = `You are an expert content analyst. Analyze the following text and determine the most appropriate visual theme category based on the primary subject matter and content focus.

Text to analyze:
"${text.substring(0, 800)}"

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

Respond with ONLY the theme category name: finance, health, tech, travel, food, or default`;

    const response = await openai.chat.completions.create({
      model: 'gpt-4o',
      messages: [
        { role: 'system', content: 'You are a precise content categorization expert. Always respond with exactly one word: the theme category name.' },
        { role: 'user', content: themePrompt }
      ],
      max_tokens: 20,
      temperature: 0
    });

    const detectedTheme = response.choices[0].message.content.trim().toLowerCase();

    // Validate the response is one of our supported themes
    const validThemes = ['finance', 'health', 'tech', 'travel', 'food', 'default'];
    if (validThemes.includes(detectedTheme)) {
      console.log(`DEBUG: AI detected theme: ${detectedTheme} for content: ${text.substring(0, 100)}...`);
      return detectedTheme;
    } else {
      console.log(`DEBUG: AI returned invalid theme '${detectedTheme}', using default for content: ${text.substring(0, 100)}...`);
      return 'default';
    }
  } catch (error) {
    console.log(`DEBUG: Theme detection failed: ${error.message}, using default for content: ${text.substring(0, 100)}...`);
    return 'default';
  }
}

/**
 * AI-powered search query generation with robust fallback
 */
async function generateSearchQuery(text, theme) {
  // Robust fallback function first
  function createFallbackQuery() {
    const words = text.toLowerCase().split(/\s+/);
    const stopWords = new Set(['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those']);
    const meaningfulWords = words.slice(0, 25)
      .filter(w => w.length > 3 && !stopWords.has(w) && /^[a-z]+$/.test(w));

    if (meaningfulWords.length > 0) {
      return `${meaningfulWords.slice(0, 4).join(' ')} ${theme} guidelines`;
    } else {
      return `${theme} information guidelines`;
    }
  }

  try {
    const queryPrompt = `Create a web search query for background information about this content.

Content (theme: ${theme}):
"${text.substring(0, 500)}"

Extract 2-4 key concepts and create a search query (max 7 words) that would find relevant context, guidelines, or background information. Focus on concepts, not exact phrases.

Query:`;

    const response = await openai.chat.completions.create({
      model: 'gpt-4o-mini',
      messages: [{ role: 'user', content: queryPrompt }],
      max_tokens: 25,
      temperature: 0.2
    });

    const aiQuery = response.choices[0].message.content.trim().replace(/"/g, '').replace(/Query:/g, '').trim();

    // Validate AI response
    if (aiQuery.split(/\s+/).length > 8 || aiQuery.length < 10) {
      console.log(`DEBUG: AI query invalid length, using fallback. AI returned: '${aiQuery}'`);
      return createFallbackQuery();
    }

    console.log(`DEBUG: AI generated search query: '${aiQuery}' for theme: ${theme}`);
    return aiQuery;
  } catch (error) {
    console.log(`DEBUG: AI query generation failed (${error.message}), using fallback`);
    return createFallbackQuery();
  }
}

/**
 * Get currency exchange rates from Frankfurter API (free, no API key required)
 */
async function getExchangeRates() {
  try {
    const response = await axios.get('https://api.frankfurter.app/latest?from=USD', {
      timeout: 3000
    });

    if (response.status === 200 && response.data.rates) {
      return response.data.rates;
    }
  } catch (error) {
    console.log(`Exchange rate fetch error: ${error.message}`);
  }

  // Fallback approximate rates if API fails (as of 2025)
  return {
    GBP: 0.79,   // British Pound
    INR: 83.50   // Indian Rupee
  };
}

/**
 * Calculate cost based on model pricing (as of 2025)
 */
function calculateCost(modelName, promptTokens, completionTokens) {
  const pricing = {
    'GPT-4o-mini': { input: 0.00015, output: 0.0006 },  // per 1k tokens
    'Gemini Pro 2.5': { input: 0.0025, output: 0.01 },  // Gemini 2.5 Pro pricing (estimated)
    'GPT-5': { input: 0.005, output: 0.015 },  // estimated premium pricing
    'gemini-2.5-pro': { input: 0.0025, output: 0.01 }  // Direct Gemini Pro pricing
  };

  const model = pricing[modelName] || pricing['GPT-5'];
  const inputCost = (promptTokens / 1000) * model.input;
  const outputCost = (completionTokens / 1000) * model.output;

  return inputCost + outputCost;
}

/**
 * Convert USD cost to GBP and INR
 */
async function convertCost(usdCost) {
  const rates = await getExchangeRates();

  return {
    USD: usdCost,
    GBP: usdCost * rates.GBP,
    INR: usdCost * rates.INR
  };
}

// Routes
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'templates', 'index.html'));
});

app.post('/api/process', async (req, res) => {
  try {
    const data = req.body;
    let inputText = (data.text || '').trim();
    const aiTopic = (data.aiTopic || '').trim();
    const articleUrl = (data.articleUrl || '').trim();
    const selectedModel = data.model || 'GPT-5';
    const verbosity = data.verbosity || 'Detailed';

    if (!inputText && !aiTopic && !articleUrl) {
      return res.json({ error: 'No input text, AI topic, or URL provided.' });
    }

    // Handle URL extraction first if provided
    if (articleUrl) {
      console.log(`DEBUG: Extracting article from URL: ${articleUrl}`);
      const articleData = await extractArticleContent(articleUrl);
      if (!articleData) {
        return res.json({ error: 'Failed to extract content from the provided URL. Please check the URL and try again.' });
      }

      inputText = `Article: ${articleData.title}\n\n${articleData.text}`;
      console.log(`DEBUG: Successfully extracted ${inputText.length} characters from URL`);
      console.log(`DEBUG: Article title: ${articleData.title}`);
      console.log(`DEBUG: Content preview: ${inputText.substring(0, 500)}...`);
    }

    // Determine processing mode (URL extraction is treated as document processing)
    const isAiResearch = Boolean(aiTopic && !inputText);
    const processingText = isAiResearch ? aiTopic : inputText;

    const theme = await extractTheme(processingText);
    const themeColor = THEME_COLORS[theme] || THEME_COLORS.default;

    console.log(`DEBUG: Processing mode: ${isAiResearch ? 'AI Research' : 'Document Processing'}`);
    console.log(`DEBUG: Detected theme: ${theme}, color: ${themeColor}`);
    console.log(`DEBUG: Selected model: ${selectedModel}, Verbosity: ${verbosity}`);
    console.log(`DEBUG: Input text length: ${processingText.length} characters`);

    // Handle AI Research vs Document Processing
    let processingContent;
    let searchContext;

    if (isAiResearch) {
      // For AI research mode, do extensive web search
      const searchQuery = aiTopic;
      const searchResults = await webSearch(searchQuery, 5);
      console.log(`DEBUG: AI Research - Found ${searchResults.length} web search results`);

      // Create research context
      searchContext = `\n\nWeb Research Results for '${aiTopic}' (USE THESE FOR CITATIONS):\n`;
      if (searchResults.length > 0) {
        searchResults.forEach((result, i) => {
          searchContext += `[${i + 1}] Title: ${result.title}\n    URL: ${result.url}\n    Snippet: ${result.snippet}\n\n`;
        });
      } else {
        searchContext += 'No specific web results found. Use general knowledge.\n';
      }

      processingContent = `Research Topic: ${aiTopic}${searchContext}`;
    } else {
      // Standard document processing with AI-powered search query generation
      const searchQuery = await generateSearchQuery(inputText, theme);
      const searchResults = await webSearch(searchQuery, 2);
      console.log(`DEBUG: Document Processing - Search query: '${searchQuery}' - Found ${searchResults.length} web search results`);

      searchContext = '';
      if (searchResults.length > 0) {
        searchContext = '\n\nAdditional Context from Web Search (USE THESE FOR CITATIONS):\n';
        searchResults.forEach((result, i) => {
          searchContext += `[${i + 1}] Title: ${result.title}\n    URL: ${result.url}\n    Snippet: ${result.snippet}\n\n`;
        });
      }

      processingContent = `${inputText}${searchContext}`;
    }

    // Create verbosity-specific instructions
    const verbosityInstructions = {
      Concise: 'Keep content brief and focused. Use 1-2 paragraphs per section, 2-3 stat boxes, and 1 small table. Prioritize key information only.',
      Detailed: 'Provide balanced detail. Use 2-3 paragraphs per section, 3 stat boxes, 1-2 comprehensive tables, and visual timelines when chronological data is present. Include supporting analysis.',
      Comprehensive: 'Provide EXTENSIVE analysis with maximum detail. REQUIREMENTS: 4-6 paragraphs per section, 6+ stat boxes, 3-4 detailed tables, visual timelines (when applicable), comparison tables, market analysis, trend data, future projections, case studies, and deep contextual insights. Make the document comprehensive like a research report.'
    };

    // Determine content type instructions
    const contentInstruction = isAiResearch ? `
RESEARCH MODE: You are researching and creating a comprehensive document about: "${aiTopic}"

Use the web search results provided and your knowledge to create an authoritative, well-researched document.
Focus on current trends, statistics, and factual information. Create original content based on research.

Verbosity Level: ${verbosity} - ${verbosityInstructions[verbosity]}
` : `
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

Verbosity Level: ${verbosity} - ${verbosityInstructions[verbosity]}
`;

    const prompt = `
${contentInstruction}

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

${theme === 'food' ? `<h2>Recipe Instructions (REQUIRED for recipe content)</h2>
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
` : ''}
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
${verbosity === 'Comprehensive' ? '- CREATE MULTIPLE SECTIONS (6+ sections minimum) with extensive analysis' : ''}
${['Detailed', 'Comprehensive'].includes(verbosity) ? '- ADD VISUAL TIMELINE with dates/milestones (use timeline HTML structure)' : ''}
${verbosity === 'Comprehensive' ? '- CREATE COMPARISON TABLES (before/after, competitor analysis, etc.)' : ''}
${verbosity === 'Comprehensive' ? '- INCLUDE MARKET ANALYSIS section with industry data' : ''}
${verbosity === 'Comprehensive' ? '- ADD FUTURE PROJECTIONS/TRENDS section' : ''}
${verbosity === 'Comprehensive' ? '- CREATE DETAILED STATISTICAL BREAKDOWN with 6+ stat boxes' : ''}
${verbosity === 'Comprehensive' ? '- INCLUDE CASE STUDIES or EXAMPLES section' : ''}
${verbosity === 'Comprehensive' ? '- ADD RISK ANALYSIS or IMPACT ASSESSMENT table' : ''}

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
${processingContent}
    `;

    // Check for Gemini API key dynamically
    const geminiApiKey = config.GOOGLE_API_KEY;
    console.log(`DEBUG: Gemini API key available: ${Boolean(geminiApiKey)}`);

    // Map model names to actual model IDs
    const modelMap = {
      'GPT-4o-mini': 'gpt-4o-mini',
      'Gemini Pro 2.5': geminiApiKey ? 'gemini-2.5-pro' : 'gpt-4o',
      'GPT-5': 'gpt-4o'
    };

    let actualModel = modelMap[selectedModel] || 'gpt-4o';

    // Retry logic for connection errors
    let response;
    for (let attempt = 0; attempt < MAX_RETRIES; attempt++) {
      try {
        // Set max tokens based on verbosity and environment
        const maxTokens = MAX_TOKENS_CONFIG[verbosity] || MAX_TOKENS_CONFIG.Detailed;

        console.log(`DEBUG: Using ${maxTokens} tokens for ${verbosity} mode with ${actualModel} (selected: ${selectedModel})`);
        console.log(`DEBUG: Prompt length: ${prompt.length} characters`);

        // Use Gemini API for Gemini models, OpenAI API for others
        if (actualModel.startsWith('gemini-')) {
          console.log('DEBUG: Using Gemini API...');
          try {
            const model = genAI.getGenerativeModel({ model: actualModel });
            const fullPrompt = 'You are an expert document analyst and professional HTML formatter. Create highly structured, intelligent documents with deep analysis.\n\n' + prompt;
            const geminiResponse = await model.generateContent({
              contents: [{ role: 'user', parts: [{ text: fullPrompt }] }],
              generationConfig: {
                maxOutputTokens: maxTokens
              }
            });

            // Convert Gemini response to OpenAI-like format
            const text = geminiResponse.response.text();
            response = {
              choices: [{ message: { content: text } }],
              usage: {
                total_tokens: text.split(/\s+/).length,
                prompt_tokens: prompt.split(/\s+/).length,
                completion_tokens: text.split(/\s+/).length
              }
            };
            console.log('DEBUG: Gemini API call successful!');
          } catch (error) {
            console.log(`DEBUG: Gemini API failed (${error.message}), falling back to OpenAI GPT-4o`);
            actualModel = 'gpt-4o';
            response = await openai.chat.completions.create({
              model: actualModel,
              messages: [
                { role: 'system', content: 'You are an expert document analyst and professional HTML formatter. Create highly structured, intelligent documents with deep analysis.' },
                { role: 'user', content: prompt }
              ],
              max_tokens: maxTokens,
              temperature: 0.7
            });
          }
        } else {
          response = await openai.chat.completions.create({
            model: actualModel,
            messages: [
              { role: 'system', content: 'You are an expert document analyst and professional HTML formatter. Create highly structured, intelligent documents with deep analysis.' },
              { role: 'user', content: prompt }
            ],
            max_tokens: maxTokens
          });
        }

        console.log(`DEBUG: Response tokens used: ${response.usage?.total_tokens || 'Unknown'}`);
        console.log(`DEBUG: Output length: ${response.choices[0].message.content.length} characters`);
        break; // Success, exit retry loop
      } catch (error) {
        console.log(`DEBUG: Attempt ${attempt + 1} failed: ${error.message}`);
        if (attempt === MAX_RETRIES - 1) {
          throw error;
        } else {
          await new Promise(resolve => setTimeout(resolve, 2000)); // Wait 2 seconds before retry
        }
      }
    }

    let aiHtml = response.choices[0].message.content;

    // Extract token usage information
    const tokenUsage = response.usage;
    const promptTokens = tokenUsage.prompt_tokens;
    const completionTokens = tokenUsage.completion_tokens;
    const totalTokens = tokenUsage.total_tokens;

    // Calculate cost and convert to multiple currencies
    const costUSD = calculateCost(selectedModel, promptTokens, completionTokens);
    const costInCurrencies = await convertCost(costUSD);

    console.log(`DEBUG: AI response length: ${aiHtml.length}`);
    console.log(`DEBUG: AI response starts with: ${aiHtml.substring(0, 100)}`);
    console.log(`DEBUG: Token usage - Prompt: ${promptTokens}, Completion: ${completionTokens}, Total: ${totalTokens}`);
    console.log(`DEBUG: Estimated cost: $${costUSD.toFixed(4)} USD`);

    // Clean up any markdown formatting that might have slipped through
    if (aiHtml.startsWith('```html')) {
      aiHtml = aiHtml.substring(7);
    }
    if (aiHtml.endsWith('```')) {
      aiHtml = aiHtml.substring(0, aiHtml.length - 3);
    }
    aiHtml = aiHtml.trim();

    // Clean up and validate the AI response
    function cleanHtml(htmlContent) {
      // Remove any remaining code block markers
      htmlContent = htmlContent.replace(/```html\s*/g, '');
      htmlContent = htmlContent.replace(/```\s*$/g, '');
      // Ensure proper formatting
      htmlContent = htmlContent.trim();
      return htmlContent;
    }

    aiHtml = cleanHtml(aiHtml);
    console.log(`DEBUG: Final HTML contains expected classes: ${aiHtml.includes('class=')}`);
    console.log(`DEBUG: Contains stat-grid: ${aiHtml.includes('stat-grid')}`);
    console.log(`DEBUG: Contains fact: ${aiHtml.includes('fact')}`);

    if (!aiHtml.trim()) {
      console.log('AI returned empty response:', response);
      return res.json({ error: 'AI returned empty HTML.' });
    }

    const cssContent = A4_CSS_TEMPLATE.replace(/THEME_COLOR/g, themeColor);
    console.log(`DEBUG: CSS content length: ${cssContent.length}`);
    console.log(`DEBUG: Theme color in CSS: ${themeColor}`);

    // Create styled document content only (no full HTML page)
    const documentContent = `
<style>
${cssContent}
</style>
<div class="a4">
${aiHtml}
</div>
    `;

    return res.json({
      html: documentContent,
      tokens: {
        prompt: promptTokens,
        completion: completionTokens,
        total: totalTokens
      },
      cost: costUSD,
      costInCurrencies: costInCurrencies,
      model: selectedModel,
      theme: theme,
      theme_color: themeColor
    });

  } catch (error) {
    console.error('Error processing request:', error);
    return res.json({ error: `Unexpected server error: ${error.message}` });
  }
});

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
});
