const isLocal = window.location.hostname === 'localhost'

export const API_BASE = isLocal
  ? 'http://localhost:8000'
  : ''

export const LAB_URL = isLocal
  ? 'http://localhost:8888'
  : 'https://notebooks.cookielab.cc'
