const isLocal = window.location.hostname === 'localhost'

export const API_BASE = isLocal
  ? 'http://localhost:8000'
  : `${window.location.protocol}//api.cookielab.cc`

export const LAB_URL = isLocal
  ? 'http://localhost:8888'
  : 'https://notebooks.cookielab.cc'
