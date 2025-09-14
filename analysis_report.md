# Food Theme Detection & Citation Issues Analysis

## Issues Identified

### 1. Food Theme Detection Failure

**Current Implementation**: `server.py:409-458`
- Uses GPT-4o with comprehensive food category definition
- Includes explicit "food" theme with detailed keywords: "Cooking, recipes, restaurants, cuisine, nutrition, ingredients, food preparation, culinary arts, dining, beverages, meal planning, kitchen tools"
- Text is truncated to first 800 chars (your recipe is 567 chars - within limit)

**Potential Root Causes**:
1. **OpenAI API Call Failure**: The `extract_theme()` function has exception handling that defaults to "default" theme on any API error
2. **Model Response Format**: If GPT-4o responds with anything other than exact theme names, it defaults to "default"
3. **API Key Issues**: No OPENAI_API_KEY configured would cause API call failure

**The recipe should clearly trigger "food" theme** - contains multiple food keywords (noodles, peanut butter, cooking, sauce, etc.)

### 2. Missing Citations Issue

**Current Implementation**: `server.py:516-527`
- Document processing mode performs web search with query: `"latest insights {first 10 words of input}"`
- For your recipe: Query would be `"latest insights spicy peanut butter noodles: -Shin ramyun noodles -Peanut"`
- Gets 2 web search results (vs 5 in research mode)
- Citations are automatically generated from web search results

**Potential Root Causes**:
1. **No BRAVE_API_KEY**: `web_search()` function returns empty array `[]` if `BRAVE_API_KEY` is not configured
2. **Poor Search Query**: The generated query may not return relevant results for recipe content
3. **Search Results Processing**: Even if search works, results might not be properly formatted into citations

## Environment Check Required

**Critical Check**: Are these environment variables set?
- `OPENAI_API_KEY` - Required for theme detection
- `BRAVE_API_KEY` - Required for web search citations

## Expected Behavior vs Actual

**Expected**:
- Theme: "food" (clear recipe content)
- Citations: 2 web search results about peanut butter noodles/recipes

**Actual**:
- Theme: "default" (failure)
- Citations: None (likely no web search results)

## Quick Fix Recommendations

1. **Check Environment Variables**:
   ```bash
   # Check if API keys are configured
   echo $OPENAI_API_KEY
   echo $BRAVE_API_KEY
   ```

2. **Debug Theme Detection**: Add logging to see exact GPT-4o response
3. **Debug Web Search**: Add logging to see if search is called and results returned
4. **Test Search Query**: The auto-generated search query might need improvement for recipe content

## Code Locations
- Theme detection: `server.py:409-458`
- Web search: `server.py:30-60`
- Citation generation: `server.py:516-527`
- Processing flow: `server.py:480-530`