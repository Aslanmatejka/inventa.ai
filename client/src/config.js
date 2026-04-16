/**
 * Shared API configuration — single source of truth for backend URLs.
 *
 * Usage:
 *   import { API_BASE, API_HOST } from '../config';
 *   fetch(`${API_BASE}/build/stream`, ...)   // → http://localhost:3001/api/build/stream
 *   fetch(`${API_HOST}/exports/cad/x.stl`)   // → http://localhost:3001/exports/cad/x.stl
 */

function getApiHost() {
  if (process.env.REACT_APP_API_HOST) return process.env.REACT_APP_API_HOST;
  // Auto-detect: if running on Render, use the Render backend URL
  const { hostname } = window.location;
  if (hostname.endsWith('.onrender.com')) {
    // Replace any frontend slug pattern with the backend slug
    return 'https://inventa-backend-3s91.onrender.com';
  }
  return 'http://localhost:3001';
}

export const API_HOST = getApiHost();
export const API_BASE = `${API_HOST}/api`;
