/**
 * Shared API configuration — single source of truth for backend URLs.
 *
 * Usage:
 *   import { API_BASE, API_HOST } from '../config';
 *   fetch(`${API_BASE}/build/stream`, ...)   // → http://localhost:3001/api/build/stream
 *   fetch(`${API_HOST}/exports/cad/x.stl`)   // → http://localhost:3001/exports/cad/x.stl
 */

export const API_HOST = process.env.REACT_APP_API_HOST || 'http://localhost:3001';
export const API_BASE = `${API_HOST}/api`;
