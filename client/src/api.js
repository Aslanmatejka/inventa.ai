/**
 * API Client - Handles communication with inventa.AI backend
 */
import { API_BASE, API_HOST } from './config';
import { supabase } from './supabaseClient';

// Use shared config for all API calls
const API_BASE_URL = API_BASE;

/**
 * Get auth headers with current Supabase session token
 */
async function getAuthHeaders() {
  const headers = { 'Content-Type': 'application/json' };
  try {
    const { data: { session } } = await supabase.auth.getSession();
    if (session?.access_token) {
      headers['Authorization'] = `Bearer ${session.access_token}`;
    }
  } catch {
    // Continue without auth header
  }
  return headers;
}

/**
 * Authenticated fetch wrapper - automatically injects auth token
 * @public - exported for use in components that make direct fetch calls
 */
export async function authFetch(url, options = {}) {
  const authHeaders = await getAuthHeaders();
  try {
    return await fetch(url, {
      ...options,
      headers: {
        ...authHeaders,
        ...options.headers,
      },
    });
  } catch (error) {
    if (error.name === 'AbortError') throw error;
    if (error.name === 'TypeError' || error.message?.includes('Failed to fetch') || error.message?.includes('NetworkError')) {
      throw new Error('Cannot reach the server. It may be waking up from sleep — please wait a moment and try again.');
    }
    throw error;
  }
}

/**
 * Stream build with SSE progress events.
 * onStep(stepData) is called for each progress event.
 * Returns the final build result when complete.
 */
export async function buildProductStream(prompt, previousDesign = null, onStep = () => {}, projectId = null, model = null, signal = null, image = null) {
  const body = { prompt, previousDesign, projectId, model };
  if (image) body.image = { base64: image.base64, mediaType: image.mediaType };
  const response = await authFetch(`${API_BASE_URL}/build/stream`, {
    method: 'POST',
    body: JSON.stringify(body),
    signal,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({
      error: 'Server error',
      message: `Server returned ${response.status}.`
    }));
    throw new Error(error.detail || error.message || error.error || `Server returned ${response.status}`);
  }

  if (!response.body) throw new Error('Server returned empty response body');
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  let finalResult = null;
  let wasCancelled = false;

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });

    // Process complete SSE lines
    const lines = buffer.split('\n');
    buffer = lines.pop(); // keep incomplete line in buffer

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        try {
          const data = JSON.parse(line.slice(6));
          onStep(data);

          if (data.status === 'complete' && data.result) {
            finalResult = data.result;
          }
          if (data.status === 'cancelled') {
            wasCancelled = true;
          }
          if (data.status === 'fatal') {
            throw new Error(data.message || 'Build failed');
          }
        } catch (e) {
          if (!(e instanceof SyntaxError)) throw e;
          // Ignore JSON parse errors on partial SSE data
        }
      }
    }
  }

  // Process any remaining buffer
  if (buffer.trim().startsWith('data: ')) {
    try {
      const data = JSON.parse(buffer.trim().slice(6));
      onStep(data);
      if (data.status === 'complete' && data.result) finalResult = data.result;
      if (data.status === 'cancelled') wasCancelled = true;
      if (data.status === 'fatal') throw new Error(data.message || 'Build failed');
    } catch (e) {
      if (!(e instanceof SyntaxError)) throw e;
    }
  }

  if (!finalResult) {
    if (wasCancelled) {
      // Graceful cancel / timeout — hook already dispatched BUILD_CANCELLED.
      return null;
    }
    throw new Error('Build stream ended without a result. Check server logs.');
  }

  return finalResult;
}

/**
 * Cancel an in-progress build by its stream build ID.
 */
export async function cancelBuild(streamBuildId) {
  const response = await authFetch(`${API_BASE_URL}/build/cancel`, {
    method: 'POST',
    body: JSON.stringify({ streamBuildId }),
  });
  return response.json();
}

/**
 * Fetch the authenticated user's aggregated token usage (today + month).
 */
export async function getMyUsage() {
  const response = await authFetch(`${API_BASE_URL}/me/usage`);
  if (!response.ok) throw new Error(`Usage fetch failed: ${response.status}`);
  return response.json();
}

/**
 * Ask mode — text-only Q&A about CAD/design (no build).
 * Returns the AI's text answer via SSE.
 */
export async function askStream(prompt, currentDesign = null, model = null) {
  const response = await authFetch(`${API_BASE_URL}/ask`, {
    method: 'POST',
    body: JSON.stringify({ prompt, currentDesign, model }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: `Server returned ${response.status}` }));
    throw new Error(error.detail || error.message || `Server error ${response.status}`);
  }

  if (!response.body) throw new Error('Server returned empty response body');
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  let answer = null;

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop();
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        try {
          const data = JSON.parse(line.slice(6));
          if (data.status === 'complete') answer = data;
          if (data.status === 'error') throw new Error(data.message);
        } catch (e) { if (!(e instanceof SyntaxError)) throw e; }
      }
    }
  }
  if (buffer.trim().startsWith('data: ')) {
    try {
      const data = JSON.parse(buffer.trim().slice(6));
      if (data.status === 'complete') answer = data;
    } catch (e) { /* ignore */ }
  }
  if (!answer) throw new Error('Ask stream ended without a response.');
  return answer;
}

/**
 * Plan mode — structured multi-step build plan (no build).
 * Returns a plan object with steps the user can execute.
 */
export async function planStream(prompt, currentDesign = null, model = null) {
  const response = await authFetch(`${API_BASE_URL}/plan`, {
    method: 'POST',
    body: JSON.stringify({ prompt, currentDesign, model }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: `Server returned ${response.status}` }));
    throw new Error(error.detail || error.message || `Server error ${response.status}`);
  }

  if (!response.body) throw new Error('Server returned empty response body');
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  let result = null;

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop();
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        try {
          const data = JSON.parse(line.slice(6));
          if (data.status === 'complete') result = data;
          if (data.status === 'error') throw new Error(data.message);
        } catch (e) { if (!(e instanceof SyntaxError)) throw e; }
      }
    }
  }
  if (buffer.trim().startsWith('data: ')) {
    try {
      const data = JSON.parse(buffer.trim().slice(6));
      if (data.status === 'complete') result = data;
    } catch (e) { /* ignore */ }
  }
  if (!result) throw new Error('Plan stream ended without a response.');
  return result;
}

/**
 * Phase 4: Rebuild model with updated parameters (no AI call)
 */
export async function rebuildWithParameters(buildId, parameters) {
  try {
    const response = await authFetch(`${API_BASE_URL}/rebuild`, {
      method: 'POST',
      body: JSON.stringify({ 
        buildId,
        parameters
      }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ 
        error: 'Rebuild failed', 
        message: `Server returned ${response.status}` 
      }));
      throw new Error(error.message || error.error || `Server returned ${response.status}`);
    }

    return response.json();
  } catch (error) {
    if (error.message.includes('fetch') || 
        error.message.includes('Failed to fetch') ||
        error.message.includes('NetworkError') ||
        (error.name === 'TypeError' && error.message.includes('fetch'))) {
      throw new Error('Cannot connect to server. The backend may be starting up — please try again in a few seconds.');
    }
    throw error;
  }
}

/**
 * Phase 4: Upload model to S3 for caching and sharing
 */
export async function uploadToS3(buildId) {
  try {
    const response = await authFetch(`${API_BASE_URL}/s3/upload`, {
      method: 'POST',
      body: JSON.stringify({ buildId }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ 
        error: 'S3 upload failed' 
      }));
      throw new Error(error.message || error.error || `Upload failed: ${response.status}`);
    }

    return response.json(); // { shareUrl, s3Key }
  } catch (error) {
    if (error.message.includes('fetch')) {
      throw new Error('Cannot connect to server.');
    }
    throw error;
  }
}

/**
 * Get all projects for the current user
 */
export async function getProjects() {
  const response = await authFetch(`${API_BASE_URL}/projects`);
  if (!response.ok) throw new Error(`Failed to load projects: ${response.status}`);
  return response.json();
}

/**
 * Get a single project with builds and messages
 */
export async function getProject(projectId) {
  const response = await authFetch(`${API_BASE_URL}/projects/${projectId}`);
  if (!response.ok) throw new Error(`Failed to load project: ${response.status}`);
  return response.json();
}

/**
 * Update a project (rename)
 */
export async function updateProject(projectId, name = null, description = null) {
  const response = await authFetch(`${API_BASE_URL}/projects/${projectId}`, {
    method: 'PUT',
    body: JSON.stringify({ name, description }),
  });
  if (!response.ok) throw new Error(`Failed to update project: ${response.status}`);
  return response.json();
}

/**
 * Delete a project and all its data
 */
export async function deleteProject(projectId) {
  const response = await authFetch(`${API_BASE_URL}/projects/${projectId}`, {
    method: 'DELETE',
  });
  if (!response.ok) throw new Error(`Failed to delete project: ${response.status}`);
  return response.json();
}

/**
 * Save a chat message to a project
 */
export async function saveMessage(projectId, role, content, buildResult = null, status = null) {
  const response = await authFetch(`${API_BASE_URL}/messages`, {
    method: 'POST',
    body: JSON.stringify({ projectId, role, content, buildResult, status }),
  });
  if (!response.ok) throw new Error(`Failed to save message: ${response.status}`);
  return response.json();
}

// â”€â”€ File Upload API â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

/**
 * Upload a CAD file for visualization and NLP editing
 * @param {File} file - The file to upload
 * @param {function} onProgress - Optional progress callback (0-100)
 * @returns Upload result with buildId, stlUrl, geometry info, etc.
 */
export async function uploadCADFile(file, onProgress = null) {
  const formData = new FormData();
  formData.append('file', file);

  // Get auth token for the XHR request
  const authHeaders = await getAuthHeaders();

  // Use XMLHttpRequest for progress tracking
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open('POST', `${API_BASE_URL}/upload`);

    // Set auth header (don't set Content-Type - FormData sets it with boundary)
    if (authHeaders['Authorization']) {
      xhr.setRequestHeader('Authorization', authHeaders['Authorization']);
    }

    if (onProgress) {
      xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable) {
          onProgress(Math.round((e.loaded / e.total) * 100));
        }
      });
    }

    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          resolve(JSON.parse(xhr.responseText));
        } catch {
          reject(new Error('Invalid response from server'));
        }
      } else {
        try {
          const err = JSON.parse(xhr.responseText);
          reject(new Error(err.detail || `Upload failed: ${xhr.status}`));
        } catch {
          reject(new Error(`Upload failed: ${xhr.status}`));
        }
      }
    };

    xhr.onerror = () => reject(new Error('Network error during upload'));
    xhr.send(formData);
  });
}

// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
// Assembly Export API (F34)
// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

/**
 * Export multiple scene products as a single merged STEP assembly file
 */
export async function exportAssembly(buildIds, name = 'Assembly') {
  const response = await authFetch(`${API_BASE_URL}/scene/export-assembly`, {
    method: 'POST',
    body: JSON.stringify({ buildIds, name }),
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: 'Assembly export failed' }));
    throw new Error(err.detail || `Assembly export failed: ${response.status}`);
  }
  return response.json();
}


// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
// Material Metadata API (F37)
// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

/**
 * List all available materials
 */
export async function listMaterials() {
  const response = await authFetch(`${API_BASE_URL}/materials`);
  if (!response.ok) throw new Error('Failed to fetch materials');
  return response.json();
}

/**
 * Get material metadata for a specific build
 */
export async function getMaterial(buildId) {
  const response = await authFetch(`${API_BASE_URL}/materials/${buildId}`);
  if (!response.ok) throw new Error('Failed to fetch material');
  return response.json();
}

/**
 * Set material for a build
 */
export async function setMaterial(buildId, materialData) {
  const response = await authFetch(`${API_BASE_URL}/materials/${buildId}`, {
    method: 'PUT',
    body: JSON.stringify(materialData),
  });
  if (!response.ok) throw new Error('Failed to set material');
  return response.json();
}


// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
// BOM Generation API (F39)
// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

/**
 * Generate a Bill of Materials from scene items
 */
export async function generateBOM(items) {
  const response = await authFetch(`${API_BASE_URL}/bom/generate`, {
    method: 'POST',
    body: JSON.stringify({ items }),
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: 'BOM generation failed' }));
    throw new Error(err.detail || 'BOM generation failed');
  }
  return response.json();
}


// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
// 2D Drawing Export API (F40)
// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

/**
 * Generate 2D engineering drawing (SVG) from a STEP model
 */
export async function export2DDrawing(buildId, views = ['front', 'top', 'right']) {
  const response = await authFetch(`${API_BASE_URL}/export/2d`, {
    method: 'POST',
    body: JSON.stringify({ buildId, views }),
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: 'Drawing export failed' }));
    throw new Error(err.detail || 'Drawing export failed');
  }
  return response.json();
}


// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
// Version History API (F36)
// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

/**
 * Save a version snapshot
 */
export async function saveVersion(buildId, label = '', design = null, parameters = null) {
  const response = await authFetch(`${API_BASE_URL}/versions/save`, {
    method: 'POST',
    body: JSON.stringify({ buildId, label, design, parameters }),
  });
  if (!response.ok) throw new Error('Failed to save version');
  return response.json();
}

/**
 * List versions for a build
 */
export async function listVersions(buildId) {
  const response = await authFetch(`${API_BASE_URL}/versions/${buildId}`);
  if (!response.ok) throw new Error('Failed to list versions');
  return response.json();
}

/**
 * Restore a specific version
 */
export async function restoreVersion(buildId, versionId) {
  const response = await authFetch(`${API_BASE_URL}/versions/restore`, {
    method: 'POST',
    body: JSON.stringify({ buildId, versionId }),
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: 'Restore failed' }));
    throw new Error(err.detail || 'Restore failed');
  }
  return response.json();
}


// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
// 3D Printer Slicer API (F38)
// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

/**
 * Get slicer presets and filament types
 */
export async function getSlicerPresets() {
  const response = await authFetch(`${API_BASE_URL}/slicer/presets`);
  if (!response.ok) throw new Error('Failed to load slicer presets');
  return response.json();
}

/**
 * Estimate print time, material, and cost
 */
export async function estimatePrint(buildId, options = {}) {
  const response = await authFetch(`${API_BASE_URL}/slicer/estimate`, {
    method: 'POST',
    body: JSON.stringify({ buildId, ...options }),
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: 'Slicer estimation failed' }));
    throw new Error(err.detail || 'Slicer estimation failed');
  }
  return response.json();
}


// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
// Real-time Collaboration API (F35)
// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

/**
 * Create a collaboration room
 */
export async function createCollabRoom(hostName, sceneId = '') {
  const response = await authFetch(`${API_BASE_URL}/collab/create`, {
    method: 'POST',
    body: JSON.stringify({ hostName, sceneId }),
  });
  if (!response.ok) throw new Error('Failed to create collaboration room');
  return response.json();
}

/**
 * Get collaboration room info
 */
export async function getCollabRoom(roomId) {
  const response = await authFetch(`${API_BASE_URL}/collab/${roomId}`);
  if (!response.ok) throw new Error('Room not found');
  return response.json();
}

/**
 * Open a WebSocket connection to a collab room
 */
export function connectToCollabRoom(roomId, onMessage) {
  const wsProtocol = API_HOST.startsWith('https') ? 'wss' : 'ws';
  const wsHost = API_HOST.replace(/^https?:\/\//, '');
  const wsUrl = `${wsProtocol}://${wsHost}/ws/collab/${roomId}`;
  const ws = new WebSocket(wsUrl);
  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      onMessage(data);
    } catch (e) {
      console.error('Failed to parse collab message:', e);
    }
  };
  ws.onerror = (err) => console.error('Collab WebSocket error:', err);
  return ws;
}



// ═══════════════════════════════════════════════════════════════════
// Billing API (Stripe)
// ═══════════════════════════════════════════════════════════════════

/**
 * Create a Stripe Checkout session and redirect to payment
 */
export async function createCheckoutSession(planId, interval = 'monthly') {
  const response = await authFetch(`${API_BASE_URL}/billing/checkout`, {
    method: 'POST',
    body: JSON.stringify({ planId, interval }),
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: 'Checkout failed' }));
    throw new Error(err.detail || `Checkout failed: ${response.status}`);
  }
  return response.json();
}

