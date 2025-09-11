from flask import Flask, render_template, request, jsonify
import openai
import os
import requests
import json
from openai import OpenAIError

app = Flask(__name__)

# Load API keys from environment
openai.api_key = os.getenv("OPENAI_API_KEY")
brave_api_key = os.getenv("BRAVE_API_KEY")
if not openai.api_key:
    raise ValueError("Please set your OPENAI_API_KEY environment variable.")

def web_search(query, num_results=3):
    """Search the web using Brave Search API"""
    if not brave_api_key:
        return []
    
    try:
        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": brave_api_key
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
            return [{'title': r.get('title', ''), 'snippet': r.get('description', '')} 
                   for r in results[:num_results]]
    except Exception as e:
        print(f"Web search error: {e}")
    
    return []

A4_CSS_TEMPLATE = """.a4 {{
    width: 21cm;
    max-width: 100%;
    min-height: 29.7cm;
    padding: 0.6cm;
    background: white;
    box-sizing: border-box;
    margin: 10px auto;
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
    margin-bottom: 8px;
    margin-top: 0px;
}}
h2 {{
    font-size: 24px;
    margin-top: 0px;
    margin-bottom: 10px;
}}
p {{
    margin: 6px 0 12px 0;
    line-height: 1.6;
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
    "finance": "#28a745",
    "tech": "#007bff",
    "health": "#e83e8c",
    "auto": "#fd7e14",
    "default": "#6c757d"
}

@app.route("/")
def index():
    return render_template("index.html")

def extract_theme(text: str) -> str:
    text_lower = text.lower()
    if any(word in text_lower for word in ["bank", "finance", "tax", "loan"]):
        return "finance"
    if any(word in text_lower for word in ["oracle", "tech", "software", "erp"]):
        return "tech"
    if any(word in text_lower for word in ["health", "medical", "hospital"]):
        return "health"
    if any(word in text_lower for word in ["car", "vehicle", "auto"]):
        return "auto"
    return "default"

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
    selected_model = data.get("model", "GPT-5")
    
    if not input_text:
        return jsonify({"error": "No input text provided."})

    theme = extract_theme(input_text)
    theme_color = THEME_COLORS.get(theme, THEME_COLORS["default"])
    
    print(f"DEBUG: Detected theme: {theme}, color: {theme_color}")
    print(f"DEBUG: Selected model: {selected_model}")

    # Extract key topics for web search
    search_query = f"latest insights {' '.join(input_text.split()[:10])}"
    search_results = web_search(search_query, num_results=2)
    print(f"DEBUG: Found {len(search_results)} web search results")
    
    # Combine original text with search insights
    search_context = ""
    if search_results:
        search_context = f"\n\nAdditional Context from Web Search:\n"
        for i, result in enumerate(search_results, 1):
            search_context += f"{i}. {result['title']}: {result['snippet']}\n"

    prompt = f"""
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
Key finding or important fact from the analysis.
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

<h2>Summary</h2>
<ul>
  <li>Key point 1</li>
  <li>Key point 2</li>
  <li>Key point 3</li>
</ul>

<div class="note">
Final summary and key takeaways.
</div>

MANDATORY TABLE REQUIREMENTS:
- EVERY document MUST contain at least 1-2 tables
- Convert ANY structured information into tables:
  • Lists of items → table rows
  • Comparisons → comparison table
  • Categories/classifications → category table
  • Steps/processes → process table
  • Key-value pairs → data table
  • Timeline events → timeline table
- Even simple bullet points MUST become tables with headers like "Item", "Description", "Details"

CRITICAL RULES:
- NO nested cards or divs inside cards
- Use EXACT stat structure with .big and .sub classes
- Keep paragraphs concise and professional
- Extract all numbers into stat boxes
- CREATE TABLES FROM EVERYTHING POSSIBLE
- Return ONLY HTML (no explanations, no backticks)

Text to analyze:
{input_text}{search_context}
    """

    try:
        # Map model names to actual model IDs
        model_map = {
            "GPT-4o-mini": "gpt-4o-mini",
            "Gemini Pro 2.5": "gpt-4o-mini",  # fallback to GPT-4o-mini for now
            "GPT-5": "gpt-4o"  # Use GPT-4o as GPT-5 proxy
        }
        
        actual_model = model_map.get(selected_model, "gpt-4o")
        
        response = openai.chat.completions.create(
            model=actual_model,
            messages=[
                {"role": "system", "content": "You are an expert document analyst and professional HTML formatter. Create highly structured, intelligent documents with deep analysis."},
                {"role": "user", "content": prompt}
            ]
        )

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
