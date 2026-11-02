# DreamCanvas — AI Text-to-Image Generator

![DreamCanvas AI Banner](https://img.shields.io/badge/FLUX.1-schnell-orange?style=for-the-badge&logo=cloudflare)
![Cloudflare Workers AI](https://img.shields.io/badge/Cloudflare-Workers_AI-F38020?style=for-the-badge&logo=cloudflare&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-19-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-3.4-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)
![Pillow](https://img.shields.io/badge/Pillow-PNG_Engine-3776AB?style=for-the-badge&logo=python&logoColor=white)

**DreamCanvas** is a full-stack, production-ready AI image generation studio powered by **Cloudflare Workers AI** using the state-of-the-art **`@cf/black-forest-labs/flux-1-schnell`** diffusion model.

---

## ⚡ Highlights & Migration

- **Engine Migration**: Switched from Hugging Face to **Cloudflare Workers AI** for low latency and high reliability without 402 payment bottlenecks.
- **Model**: `@cf/black-forest-labs/flux-1-schnell` (distilled 4-step Latent Diffusion Transformer).
- **HTTP Client**: Built with **`httpx`** for fast async/sync API calls.
- **Pillow Conversion**: Decodes `result.image` from base64, processes through Pillow (`PIL.Image`), and converts into an optimized lossless PNG.
- **Dual Response Support**:
  - `POST /api/generate` returns JSON with `image_base64` and metadata for the React frontend.
  - Returns raw `image/png` bytes when `Accept: image/png` or `?format=raw` is requested.
  - Dedicated `POST /api/generate/raw` returns raw `image/png` stream directly.
- **Download PNG**: Full browser-side and API-side PNG download capability.

---

## 🏗️ Architecture & Project Structure

```
genai prac/
├── backend/
│   ├── .venv/                      # Python virtual environment
│   ├── .env.example                # Backend environment variables template
│   ├── .env                        # Local credentials (git-ignored)
│   ├── requirements.txt            # Python dependencies (httpx, fastapi, pillow, etc.)
│   ├── main.py                     # FastAPI routes, health & generation endpoints
│   ├── config.py                   # Pydantic Settings (reads CLOUDFLARE credentials)
│   ├── schemas.py                  # Pydantic request & response models
│   ├── services/
│   │   ├── __init__.py
│   │   ├── cf_generator.py         # Cloudflare Workers AI client & Pillow PNG converter
│   │   └── style_presets.py        # 12 artistic style presets & prompt modifiers
│   └── tests/
│       ├── __init__.py
│       └── test_api.py             # Pytest test suite (100% passing)
├── frontend/
│   ├── package.json                # React 19, Lucide icons, Tailwind CSS
│   ├── vite.config.js              # Vite server configuration with backend API proxy
│   ├── tailwind.config.js          # Custom colors, animations & glassmorphism
│   ├── postcss.config.js           # PostCSS configuration
│   ├── index.html                  # HTML document & Google Fonts
│   └── src/
│       ├── App.jsx                 # Main application workspace
│       ├── main.jsx                # React root
│       ├── index.css               # Tailwind directives & custom scrollbars
│       ├── constants/
│       │   └── styles.js           # Style presets, aspect ratios & sample prompts
│       ├── services/
│       │   └── api.js              # API service for health, generation & download
│       └── components/             # Reusable UI components
├── .env.example                    # Root environment template
├── .gitignore                      # Git ignore rules protecting API keys and venvs
├── package.json                    # Root project scripts
├── requirements.txt                # Root requirements file
└── README.md                       # Complete project documentation
```

---

## 🔑 Cloudflare Credentials Setup

To run image generation with Cloudflare Workers AI:

1. **Obtain your API Token**:
   - Go to [dash.cloudflare.com/profile/api-tokens](https://dash.cloudflare.com/profile/api-tokens).
   - Create a token using the **Workers AI** template (with `Account - Workers AI - Edit/Read` permissions).

2. **Locate your Account ID**:
   - In the [Cloudflare Dashboard](https://dash.cloudflare.com/), navigate to **Workers & Pages**.
   - Your **Account ID** is displayed in the right sidebar under **Account details** (a 32-character hex string).
   - Alternatively, it is present in your dashboard URL: `https://dash.cloudflare.com/<ACCOUNT_ID>/workers-and-pages`.

3. **Configure `backend/.env`**:
   ```env
   CLOUDFLARE_API_TOKEN=cfut_your_token_here
   CLOUDFLARE_ACCOUNT_ID=your_cloudflare_account_id_here
   CLOUDFLARE_MODEL=@cf/black-forest-labs/flux-1-schnell
   HOST=0.0.0.0
   PORT=8000
   DEBUG=False
   ```

---

## 🚀 Running the Project

### 1. Run the Backend (FastAPI)

```powershell
$env:PYTHONPATH="."; .\backend\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --port 8000
```
- API Health Check: `http://127.0.0.1:8000/api/health`
- Interactive Swagger Docs: `http://127.0.0.1:8000/docs`

### 2. Run the Frontend (React + Vite)

```powershell
cd frontend
npm run dev
```
- Open `http://localhost:5173` in your browser.

---

## 🧪 Testing

Run the automated test suite verifying Cloudflare Workers AI integration, Pillow PNG conversion, and input validation:

```powershell
$env:PYTHONPATH="."; .\backend\.venv\Scripts\pytest.exe .\backend\tests -v
```

All 8 tests verify:
- Endpoint health and status
- Input validation (rejecting empty whitespace)
- Missing credential handling (401 with clear feedback)
- Mocked Cloudflare Workers AI response decoding (`result.image` base64)
- Lossless Pillow PNG conversion
- Dual format support (JSON base64 and binary `image/png` stream)

---

## 📡 API Reference

### 1. `POST /api/generate`
Generates an image via Cloudflare Workers AI `@cf/black-forest-labs/flux-1-schnell`.

**Request Body (JSON):**
```json
{
  "prompt": "A majestic snow leopard resting on Himalayan peaks at sunrise",
  "style": "photorealistic",
  "num_inference_steps": 4,
  "seed": 42
}
```

**JSON Response (Default / Frontend):**
```json
{
  "success": true,
  "image_base64": "iVBORw0KGgo...",
  "mime_type": "image/png",
  "prompt": "A majestic snow leopard resting on Himalayan peaks at sunrise",
  "enhanced_prompt": "Award-winning professional photograph of A majestic snow leopard resting on Himalayan peaks at sunrise, 35mm lens, f/1.8 aperture...",
  "style": "photorealistic",
  "width": 1024,
  "height": 1024,
  "seed": 42,
  "generation_time_seconds": 2.15,
  "model": "@cf/black-forest-labs/flux-1-schnell"
}
```

**Binary PNG Response:**
Send `Accept: image/png` or query parameter `?format=raw`:
```bash
curl -X POST "http://127.0.0.1:8000/api/generate?format=raw" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "A red sports car", "style": "cyberpunk"}' \
  --output result.png
```

---

## 🔒 Security
- API tokens are stored strictly in `backend/.env` on the server and are never exposed to the client.
- `.gitignore` prevents secret files from being committed.
