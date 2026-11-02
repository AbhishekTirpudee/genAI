const BASE_URL = import.meta.env.VITE_API_BASE_URL || "";

/**
 * Perform a GET request to the health endpoint
 */
export async function checkHealth() {
  const url = `${BASE_URL}/api/health`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Health check failed with status: ${response.status}`);
  }
  return response.json();
}

/**
 * Fetch available style presets
 */
export async function fetchStyles() {
  const url = `${BASE_URL}/api/styles`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to load styles: ${response.status}`);
  }
  return response.json();
}

/**
 * Generate image using POST /api/generate
 * @param {Object} payload
 * @param {string} payload.prompt
 * @param {string} payload.style
 * @param {number} payload.width
 * @param {number} payload.height
 * @param {number} payload.num_inference_steps
 * @param {number|null} payload.seed
 */
export async function generateImage(payload) {
  const url = `${BASE_URL}/api/generate`;
  
  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Accept": "application/json"
    },
    body: JSON.stringify(payload)
  });

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    let errorMessage = "An error occurred while generating the image.";
    
    if (data && data.error) {
      errorMessage = data.error;
    } else if (data && data.detail) {
      if (Array.isArray(data.detail)) {
        errorMessage = data.detail.map(d => d.msg || JSON.stringify(d)).join(", ");
      } else {
        errorMessage = data.detail;
      }
    } else if (response.status === 401) {
      errorMessage = "Hugging Face token is missing or invalid. Check backend/.env.";
    } else if (response.status === 429) {
      errorMessage = "Hugging Face rate limit exceeded. Please wait a few moments and try again.";
    } else if (response.status === 503) {
      errorMessage = "The FLUX.1-schnell model is warming up on Hugging Face providers. Please retry in 20-30 seconds.";
    }

    const error = new Error(errorMessage);
    error.status = response.status;
    error.data = data;
    throw error;
  }

  return data;
}

/**
 * Helper to download base64 PNG directly to user's disk
 * @param {string} base64Data
 * @param {string} filename
 */
export function downloadPngFromBase64(base64Data, filename = "dreamcanvas-artwork.png") {
  const link = document.createElement("a");
  link.href = `data:image/png;base64,${base64Data}`;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

