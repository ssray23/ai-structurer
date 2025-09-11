# AI Document Structurer

Transform any unstructured text into beautifully formatted A4 documents with AI-powered content analysis and theming.

## 🚀 Features

### Core Functionality
- **AI-Powered Document Structuring**: Uses OpenAI GPT models to intelligently structure content
- **Dynamic Theme Detection**: Enhanced detection for finance, tech, health, auto themes with comprehensive keyword matching
- **A4-Formatted Output**: Professional document formatting optimized for printing with full width display
- **Real-Time Preview**: See your formatted document instantly in the browser with exact download formatting
- **Multiple Export Options**: Download as HTML or PDF

### Advanced Processing Methods
- **📄 Method 1 - Document Processing**: Upload/paste existing documents for intelligent restructuring
- **🔍 Method 2 - AI Research Mode**: Enter research topics (max 20 words) for AI to research and generate comprehensive documents
- **Radio Button Interface**: Clear method selection with auto-switching and field clearing

### Intelligence Features  
- **3-Tier Verbosity Control**: Concise, Detailed, or Comprehensive output with different content depths
- **Enhanced Web Search**: 5 search results for research mode, 2 for document processing
- **Smart Theme Detection**: Expanded keyword recognition including "cancer" → health, "AI" → tech
- **Connection Resilience**: 3-attempt retry logic for API reliability

### User Experience
- **Split-Screen Interface**: Input on left, formatted output on right with perfect A4 scaling
- **Animated Gradient Branding**: Beautiful rainbow gradient title with smooth color transitions
- **Real-Time Word Counter**: 20-word limit enforcement with color-coded feedback
- **Improved Font Consistency**: 16px readable text matching downloaded documents
- **Theme-Consistent Documents**: Generated documents follow theme colors without UI interference

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

| Theme | Colors | Triggers |
|-------|--------|----------|
| **Finance** | Green | finance, money, investment, revenue |
| **Technology** | Blue | tech, software, AI, digital, iPhone |
| **Health** | Pink | health, medical, wellness, fitness |
| **Automotive** | Orange | car, vehicle, automotive, transport |
| **Default** | Blue | Fallback theme |

## 📊 Content Processing

### AI Prompt Engineering
The system uses carefully crafted prompts to:
- Identify document structure and hierarchy
- Extract key statistics and facts
- Create appropriate tables and visual elements
- Generate professional formatting

### Styling Features
- **A4 Format**: 21cm × 29.7cm document size with full-width preview
- **Professional Typography**: Helvetica font family
- **Visual Elements**: Fact boxes, stat grids, tables
- **Print Optimization**: Special CSS for print media
- **Responsive Design**: Adapts to different screen sizes
- **Animated Branding**: Gradient-filled app title with smooth color transitions
- **Scoped Styling**: Document themes remain pure without UI interference

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