# 🚀 PostifyAI-AI LinkedIn Post Generator

An intelligent AI-powered tool that generates engaging LinkedIn posts using LangChain and LangGraph. Transform your ideas into professional, audience-targeted content with just a few clicks.

## ✨ Features

- **AI-Powered Content Generation**: Uses advanced AI to create engaging LinkedIn posts
- **Multiple Tone Options**: Professional, casual, inspirational, educational, humorous, and thought-provoking
- **Audience Targeting**: Tailored content for different professional audiences
- **Customizable Length**: Short, medium, or long-form posts
- **Smart Hashtags**: Automatically generated relevant hashtags
- **Call-to-Action**: Includes engaging CTAs to boost engagement
- **Dark/Light Theme**: Toggle between dark and light modes
- **Real-time Metrics**: Track generation time, tokens used, and cost estimates
- **Copy to Clipboard**: Easy one-click copying of generated posts

## 🏗️ Architecture

### Backend (Python + FastAPI)
- FastAPI web framework
- LangChain for AI orchestration
- LangGraph for complex AI workflows
- Integration with LLM APIs
- RESTful API endpoints

### Frontend (React + Vite)
- Modern React with hooks
- Tailwind CSS for styling
- Responsive design
- Real-time theme switching
- Lucide React icons

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- npm or yarn

### Backend Setup

1. Navigate to the backend directory:
```bash
cd linkedin-backend
```

2. Create and activate virtual environment:
```bash
uv init
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
uv run pip install -r requirements.txt
```

4. Set up environment variables:
```bash
# Create .env file with your API keys
GOOGLE_API_KEY=your_google_api_key_here
# Add other required environment variables
```

5. Run the backend:
```bash
uvicorn main:app --host 0.0.0.0 --port 8500
```

The backend will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd linkedin-frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm run dev
```

The frontend will be available at `http://localhost:5173`

## 📁 Project Structure

```
project-root/
├── linkedin-backend/
│   ├── venv/                 # Python virtual environment
│   ├── main.py              # FastAPI application
│   ├── requirements.txt     # Python dependencies
│   ├── Dockerfile          # Docker configuration
│   └── vercel.json         # Vercel deployment config
└── linkedin-frontend/
    ├── node_modules/        # Node.js dependencies
    ├── src/
    │   ├── App.jsx         # Main React component
    │   └── index.css       # Global styles
    ├── package.json        # Node.js configuration
    ├── vite.config.js      # Vite configuration
    └── tailwind.config.js  # Tailwind CSS configuration
```

## 🔧 API Endpoints

- `POST /generate-posts` - Generate LinkedIn posts
- `GET /tones` - Get available tone options
- `GET /audiences` - Get available audience options

## 🎨 Customization

### Adding New Tones
Edit the tones array in the backend to add new tone options.

### Adding New Audiences
Modify the audiences array to include new target audience types.

### Styling
The frontend uses Tailwind CSS. Modify the classes in `App.jsx` to customize the appearance.

## 🚢 Deployment

### Backend Deployment (Vercel)
The backend includes a `vercel.json` configuration for easy deployment to Vercel.

### Frontend Deployment
The frontend can be deployed to any static hosting service like Vercel, Netlify, or GitHub Pages.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🛠️ Built With

- **Backend**: Python, FastAPI, LangChain, LangGraph
- **Frontend**: React, Vite, Tailwind CSS
- **Icons**: Lucide React
- **AI**: OpenAI GPT models (or your preferred LLM)

## 📞 Support

If you encounter any issues or have questions, please open an issue on GitHub.

---

⭐ Don't forget to star this repository if you found it helpful!
