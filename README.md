# AI Document Structurer

Transform any unstructured text into beautifully formatted A4 documents with AI-powered content analysis and theming.

## 🚀 Features

- **AI-Powered Document Structuring**: Uses OpenAI GPT models to intelligently structure content
- **Dynamic Theme Detection**: Automatically detects content themes (finance, tech, health, auto) and applies appropriate color schemes
- **A4-Formatted Output**: Professional document formatting optimized for printing with full width display
- **Real-Time Preview**: See your formatted document instantly in the browser with exact download formatting
- **Multiple Export Options**: Download as HTML or PDF
- **Split-Screen Interface**: Input on left, formatted output on right
- **Animated Gradient Branding**: Beautiful animated gradient title with professional styling
- **Theme-Consistent Documents**: Generated documents follow theme colors without interference

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

### Example: Transform Raw Text into Structured Document

**Input Text:**
```
The iPhone 17 lineup introduces diverse designs breaking away from uniformity. 
The iPhone 17 Air is 5.64mm thin. There are 452 million iPhone users with 
devices over 3 years old. The Pro models have larger camera islands.
```

**AI Processing Steps:**

1. **Theme Detection**: Analyzes keywords → Detects "Technology" theme → Applies blue color scheme
2. **Content Structuring**: AI identifies:
   - Main topic: iPhone 17 Lineup
   - Key statistics: 5.64mm thickness, 452 million users
   - Important features: Design changes, camera improvements
3. **Document Generation**: Creates structured HTML with:
   - Professional heading
   - Fact boxes for key insights
   - Statistics grid for numbers
   - Comparison tables
   - Summary bullets

**Output Document:**
- A4-formatted professional document
- Blue tech theme with branded styling
- Tables, fact boxes, and visual elements
- Print-ready formatting

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
Processes text input and returns structured HTML document.

**Request:**
```json
{
  "text": "Your unstructured text here",
  "model": "GPT-4o-mini"
}
```

**Response:**
```json
{
  "html": "<div class='a4'>...</div>",
  "theme": "technology",
  "theme_color": "#007bff",
  "tokens": {"total": 1250, "prompt": 800, "completion": 450},
  "cost": 0.0125,
  "model": "gpt-4o-mini"
}
```

## 🎯 Use Cases

- **Business Reports**: Transform data into professional presentations
- **Academic Papers**: Structure research content with proper formatting
- **Technical Documentation**: Create well-organized technical guides
- **Content Marketing**: Generate visually appealing content pieces
- **Executive Summaries**: Convert lengthy reports into structured overviews

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