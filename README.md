# AI Document Structurer

Transform any unstructured text into beautifully formatted A4 documents with AI-powered content analysis and theming.

## 🚀 Features

### Core Functionality
- **AI-Powered Document Structuring**: Uses OpenAI GPT models to intelligently structure content
- **Dynamic Theme Detection**: Enhanced detection for finance, tech, health, auto, and **food** themes with comprehensive keyword matching
- **A4-Formatted Output**: Professional document formatting optimized for printing with full width display
- **Real-Time Preview**: See your formatted document instantly in the browser with exact download formatting
- **Multiple Export Options**: Download as HTML or PDF
- **🆕 Interactive Citations**: Clickable web source references with professional academic styling

### Advanced Processing Methods
- **📄 Method 1 - Document Processing**: Upload/paste existing documents for intelligent restructuring
- **🔍 Method 2 - AI Research Mode**: Enter research topics (max 20 words) for AI to research and generate comprehensive documents
- **Radio Button Interface**: Clear method selection with auto-switching and field clearing

### Intelligence Features
- **3-Tier AI Model Selection**: GPT-4o-mini (fast), Gemini Pro 2.5 (balanced), GPT-5 (advanced reasoning)
- **3-Tier Verbosity Control**: Concise, Detailed, or Comprehensive output with different content depths
- **AI-Powered Theme Detection**: Intelligent content analysis using GPT-4o for accurate theme categorization
- **🆕 AI-Powered Search Queries**: Intelligent web search using AI to generate contextually relevant queries instead of random keywords
- **🆕 Smart Citations System**: Automatic generation of clickable source references with professional styling
- **Connection Resilience**: 3-attempt retry logic with 60-second timeout for comprehensive processing

### User Experience
- **Responsive Split-Screen**: 48/52 layout optimized for Surface 5 laptop at 150% scale
- **Auto-Hide Scrollbars**: Clean interface with scrollbars appearing only on hover
- **Animated Gradient Branding**: Beautiful rainbow gradient title with smooth color transitions
- **Real-Time Word Counter**: 20-word limit enforcement with color-coded feedback
- **Perfectly Aligned Sliders**: Precise slider knob alignment with text labels
- **Optimized A4 Scaling**: Responsive document width (18cm on smaller screens) eliminating horizontal scrollbars

## 🏗️ Architecture

### Backend (Flask)
```
server.py
├── Theme Detection Engine
├── OpenAI API Integration
├── Content Processing Pipeline
└── HTML Template Generation
```

### Frontend (Vanilla JS + CSS)
```
templates/index.html
├── Split-Screen Layout
├── A4 Document Preview
├── Real-Time Processing
└── Export Functionality
```

### AI Processing Flow
```
1. Text Input → 2. Theme Detection → 3. AI Structuring → 4. CSS Styling → 5. A4 Document
```

## 🎯 How It Works

### Example 1: Document Processing (Method 1)

**Input Text:**
```
The iPhone 17 lineup introduces diverse designs breaking away from uniformity. 
The iPhone 17 Air is 5.64mm thin. There are 452 million iPhone users with 
devices over 3 years old. The Pro models have larger camera islands.
```

**AI Processing Steps:**
1. **Theme Detection**: Analyzes keywords → Detects "Technology" theme → Applies blue color scheme
2. **Content Structuring**: AI identifies key statistics, features, and market data
3. **Document Generation**: Creates structured HTML with professional formatting

### Example 2: AI Research Mode (Method 2)

**Research Topic Input:**
```
"Role of AI in cancer research breakthroughs 2024"
```

**AI Research Steps:**
1. **Web Search**: Performs 5 targeted searches for latest cancer AI research
2. **Content Synthesis**: Combines search results with AI knowledge
3. **Comprehensive Document**: Generates research report with:
   - Current breakthrough analysis
   - Statistical data and trends
   - Timeline tables of developments
   - Future projections
   - Case studies and examples

**Output Features:**
- **Verbosity Control**: Concise (brief overview) → Comprehensive (research paper depth)
- **Dynamic Themes**: Health theme (pink) for cancer research, Tech theme (blue) for AI topics
- **Professional Formatting**: A4 layout with tables, fact boxes, and visual elements
- **Print-Ready**: Optimized for both screen viewing and document printing

## 🛠️ Setup & Installation

### Prerequisites
- Python 3.8+
- OpenAI API key

### Installation
```bash
# Clone the repository
git clone https://github.com/ssray23/ai-structurer.git
cd ai-structurer

# Install dependencies
pip install flask openai python-dotenv

# Create environment file
echo "OPENAI_API_KEY=your_api_key_here" > .env
echo "OPENAI_MODEL=gpt-4o-mini" >> .env

# Run the server
python server.py
```

### Access the Application
Open your browser and go to: `http://localhost:5000`

## 🎨 Theme System

The application automatically detects content themes and applies appropriate styling:

| Theme | Colors | AI-Powered Detection |
|-------|--------|----------|
| **Finance** | Green (#28a745) | AI analyzes content for financial topics, investments, economics |
| **Technology** | Blue (#007bff) | AI detects tech content, software, AI, digital systems |
| **Health** | Pink (#e83e8c) | AI identifies medical, healthcare, wellness content |
| **Automotive** | Orange (#fd7e14) | AI recognizes car brands, vehicle sales, transportation |
| **🆕 Food** | Orange (#ff6b35) | AI detects recipes, cooking, cuisine, nutrition content |
| **Default** | Gray (#6c757d) | Fallback for general content |

## 📊 Content Processing

### AI Prompt Engineering
The system uses carefully crafted prompts to:
- **Dual AI System**: GPT-4o for theme detection + user-selected model for content generation
- **Intelligent Structure Recognition**: Identifies document hierarchy and key elements
- **Consistent Stat Box Generation**: Enforced HTML structure for reliable visual formatting
- **Table-First Approach**: Converts structured information into professional tables
- **Bold Summary Styling**: Enhanced conclusion formatting for emphasis

### Styling Features
- **Responsive A4 Format**: 21cm standard, 18cm on smaller screens (eliminates scrollbars)
- **Professional Typography**: Helvetica font family with consistent 16px sizing
- **Enhanced Visual Elements**: Properly styled fact boxes, stat grids, tables with theme colors
- **Print Optimization**: Special CSS for print media with scaled content
- **Clean Interface**: Auto-hiding scrollbars, surgical gap adjustments, precise alignments
- **Surface 5 Optimized**: Perfect 150% scale viewing without horizontal scrollbars

### 🆕 AI-Powered Search & Citations System

#### Smart Query Generation
- **AI Content Analysis**: GPT-4o-mini analyzes your content to understand key concepts and context
- **Contextual Search Queries**: Instead of using random keywords, AI generates focused search terms
- **Examples**:
  - Banking document → `"commercial property lease legal guidelines India"`
  - Recipe content → `"peanut butter noodle cooking techniques"`
  - Tech article → `"software development best practices"`
- **Robust Fallback**: If AI fails, intelligent word extraction creates relevant backup queries
- **Universal Adaptability**: Works with ANY content type - no hardcoded categories needed

#### Professional Citations
- **Automatic Source Detection**: Captures web search results and converts them to citations
- **Professional Academic Styling**: Numbered badges, clickable titles, descriptive snippets
- **Theme-Adaptive Styling**: Citations match document theme colors for visual consistency
- **Interactive Links**: Click citations to open source websites in new tabs
- **Structured Format**: Clean academic-style layout with proper spacing and typography
- **Always Generated**: Every document includes a citations section with relevant sources

## 🔧 API Endpoints

### POST /api/process
Processes text input or research topics and returns structured HTML document.

**Request (Document Processing):**
```json
{
  "text": "Your document text here",
  "aiTopic": "",
  "model": "GPT-5",
  "verbosity": "Detailed"
}
```

**Request (AI Research):**
```json
{
  "text": "",
  "aiTopic": "role of AI in cancer research",
  "model": "GPT-5", 
  "verbosity": "Comprehensive"
}
```

**Response:**
```json
{
  "html": "<div class='a4'>...</div>",
  "theme": "health",
  "theme_color": "#e83e8c",
  "tokens": {"total": 2989, "prompt": 1243, "completion": 1746},
  "cost": 0.0324,
  "model": "GPT-5"
}
```

## 🎯 Use Cases

### Document Processing (Method 1)
- **Business Reports**: Transform raw data into professional presentations
- **Academic Papers**: Structure research content with proper formatting  
- **Technical Documentation**: Create well-organized technical guides
- **Executive Summaries**: Convert lengthy reports into structured overviews
- **Legal Documents**: Format contracts and agreements with proper structure

### AI Research Mode (Method 2)
- **Market Research**: Generate comprehensive industry analysis reports
- **Scientific Literature Reviews**: Create research summaries on specific topics
- **Trend Analysis**: Produce reports on emerging technologies or market trends
- **Educational Content**: Generate structured learning materials on any subject
- **Competitive Intelligence**: Research and analyze competitor landscapes
- **Policy Briefs**: Create government or organizational policy documents

## 🛡️ Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key for content processing | Yes |
| `OPENAI_MODEL` | AI model to use (default: gpt-4o-mini) | Yes |
| `BRAVE_API_KEY` | Future web search integration | No |

## 🚀 Deployment

The application is ready for deployment on platforms like:
- Heroku
- Railway
- Vercel
- AWS EC2
- Digital Ocean

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Built with ❤️ using Flask, OpenAI, and modern web technologies**