# ProductVision AI 🔮

An AI-powered product image understanding application that identifies visible product features and generates structured, SEO-ready product descriptions using **Google Gemini 2.0 Flash Vision**.

## ✨ Features

| Feature | Description |
|---|---|
| 🎨 **Visual Feature Detection** | Colors, materials, finishes, shape, design style |
| 📝 **Rich Descriptions** | Short & long-form marketing copy |
| 🏷️ **SEO Keywords** | Auto-extracted search keywords |
| 📊 **Specifications** | Components, labels, connectivity, packaging |
| 💡 **Use Cases** | Primary, secondary, tertiary use cases |
| 🏆 **Unique Selling Points** | AI-identified competitive advantages |
| 💰 **Price Estimation** | Estimated retail price range |
| 🎯 **Target Audience** | Who the product is designed for |
| 🔬 **Quality Assessment** | Visible quality indicators |
| 📋 **Confidence Score** | Analysis certainty percentage |

## 🏗️ Architecture

```
product-vision-app/
├── backend/
│   ├── app.py              # Flask API server
│   ├── .env                # Your API keys (create from .env.example)
│   ├── .env.example        # Template
│   ├── requirements.txt    # Python dependencies
│   └── test_backend.py     # Environment verification script
└── frontend/
    ├── public/
    │   └── index.html
    ├── src/
    │   ├── App.js           # Root component
    │   ├── components/
    │   │   ├── Header.js            # Top navigation
    │   │   ├── ImageUploader.js     # Drag-and-drop upload UI
    │   │   ├── AnalysisResults.js   # Structured results display
    │   │   └── LoadingOverlay.js    # Animated loading screen
    └── package.json
```

## 🚀 Setup & Running

### 1. Get a Gemini API Key

Go to [Google AI Studio](https://aistudio.google.com/app/apikey) and create a free API key.

### 2. Backend Setup

```bash
cd product-vision-app/backend

# Install dependencies
pip install flask flask-cors google-generativeai python-dotenv pillow

# Create .env file
copy .env.example .env
# Edit .env and set your GEMINI_API_KEY

# Verify setup
python test_backend.py

# Start the server
python app.py
```

Backend runs at: **http://localhost:5000**

### 3. Frontend Setup

```bash
cd product-vision-app/frontend

# Install dependencies
npm install

# Start the dev server
npm start
```

Frontend runs at: **http://localhost:3000**

## 🔌 API Reference

### `GET /health`
Health check endpoint.

**Response:**
```json
{ "status": "healthy", "model": "gemini-2.0-flash" }
```

### `POST /analyze`
Analyze a product image.

**Request (multipart form):**
```
Content-Type: multipart/form-data
image: <file>
```

**Request (JSON base64):**
```json
{
  "image_base64": "<base64-encoded-image>",
  "mime_type": "image/jpeg"
}
```

**Response:**
```json
{
  "success": true,
  "image_size_kb": 245.3,
  "analysis": {
    "product_name": "...",
    "category": "...",
    "tagline": "...",
    "short_description": "...",
    "long_description": "...",
    "visual_features": { ... },
    "key_features": [ ... ],
    "specifications": { ... },
    "use_cases": [ ... ],
    "unique_selling_points": [ ... ],
    "seo_keywords": [ ... ],
    "suggested_price_range": "...",
    "confidence_score": 0.92
  }
}
```

## 🖼️ Supported Image Formats

- JPEG / JPG
- PNG
- WebP
- GIF

**Maximum size:** 10 MB

## 🛠️ Configuration

Edit `backend/.env`:

```env
GEMINI_API_KEY=your_key_here
FLASK_ENV=development
PORT=5000
```

Edit `frontend/.env` (create if needed):

```env
REACT_APP_API_URL=http://localhost:5000
```

## 📦 Dependencies

**Backend:**
- `flask` — Web framework
- `flask-cors` — Cross-origin requests
- `google-generativeai` — Gemini Vision API
- `python-dotenv` — Environment management
- `Pillow` — Image validation

**Frontend:**
- `react` — UI framework
- `axios` — HTTP client
- `react-dropzone` — Drag-and-drop uploads
