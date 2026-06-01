<template>
  <svg viewBox="0 0 940 980" xmlns="http://www.w3.org/2000/svg" font-family="Inter, system-ui, sans-serif" class="w-full h-auto">
    <rect width="940" height="980" fill="white" rx="8"/>

    <defs>
      <marker id="ah" viewBox="0 0 10 8" refX="9" refY="4" markerWidth="8" markerHeight="6" orient="auto">
        <path d="M0,0 L10,4 L0,8 Z" fill="#6b7280"/>
      </marker>
      <marker id="ah-db" viewBox="0 0 10 8" refX="9" refY="4" markerWidth="8" markerHeight="6" orient="auto">
        <path d="M0,0 L10,4 L0,8 Z" fill="#2563eb"/>
      </marker>
      <marker id="ah-llm" viewBox="0 0 10 8" refX="9" refY="4" markerWidth="8" markerHeight="6" orient="auto">
        <path d="M0,0 L10,4 L0,8 Z" fill="#9333ea"/>
      </marker>
      <marker id="ah-llm-rev" viewBox="0 0 10 8" refX="1" refY="4" markerWidth="8" markerHeight="6" orient="auto">
        <path d="M10,0 L0,4 L10,8 Z" fill="#9333ea"/>
      </marker>
    </defs>

    <!-- ==================== NODES ==================== -->

    <!-- Frontend (teal) -->
    <rect x="145" y="18" width="510" height="70" rx="12" fill="#f0fdfa" stroke="#2dd4bf" stroke-width="1.8"/>
    <text x="400" y="44" text-anchor="middle" font-size="14" font-weight="600" fill="#134e4a">Frontend</text>
    <text x="400" y="64" text-anchor="middle" font-size="10.5" fill="#4b5563">Vue 3 + Vite — Login · Chatbot · ETL · Exportador</text>

    <!-- Planka (teal, connected to frontend) -->
    <rect x="720" y="25" width="160" height="56" rx="10" fill="#f0fdfa" stroke="#2dd4bf" stroke-width="1.4"/>
    <text x="800" y="48" text-anchor="middle" font-size="12" font-weight="600" fill="#134e4a">Planka</text>
    <text x="800" y="64" text-anchor="middle" font-size="9.5" fill="#6b7280">Gestion de tareas</text>

    <!-- Nginx + JWT (sky blue) -->
    <rect x="275" y="128" width="250" height="55" rx="10" fill="#f0f9ff" stroke="#38bdf8" stroke-width="1.8"/>
    <text x="400" y="151" text-anchor="middle" font-size="13" font-weight="600" fill="#0c4a6e">Nginx + JWT</text>
    <text x="400" y="168" text-anchor="middle" font-size="10.5" fill="#0369a1">Reverse proxy · Autenticacion</text>

    <!-- API REST (green) -->
    <rect x="275" y="225" width="250" height="55" rx="10" fill="#f0fdf4" stroke="#4ade80" stroke-width="1.8"/>
    <text x="400" y="248" text-anchor="middle" font-size="13" font-weight="600" fill="#166534">API REST</text>
    <text x="400" y="265" text-anchor="middle" font-size="10.5" fill="#15803d">FastAPI · Python 3.12</text>

    <!-- Duplicados (green) -->
    <rect x="35" y="340" width="210" height="62" rx="10" fill="#f0fdf4" stroke="#4ade80" stroke-width="1.5"/>
    <text x="140" y="365" text-anchor="middle" font-size="13" font-weight="600" fill="#166534">Duplicados</text>
    <text x="140" y="383" text-anchor="middle" font-size="10" fill="#15803d">pg_trgm · PostgreSQL</text>

    <!-- Categorizacion (green) -->
    <rect x="290" y="340" width="210" height="62" rx="10" fill="#f0fdf4" stroke="#4ade80" stroke-width="1.5"/>
    <text x="395" y="365" text-anchor="middle" font-size="13" font-weight="600" fill="#166534">Categorizacion</text>
    <text x="395" y="383" text-anchor="middle" font-size="10" fill="#15803d">Modelo ML</text>

    <!-- Normalizacion (green) -->
    <rect x="545" y="340" width="210" height="62" rx="10" fill="#f0fdf4" stroke="#4ade80" stroke-width="1.5"/>
    <text x="650" y="365" text-anchor="middle" font-size="13" font-weight="600" fill="#166534">Normalizacion</text>
    <text x="650" y="383" text-anchor="middle" font-size="10" fill="#15803d">Descripcion SAP</text>

    <!-- Gemini (purple) -->
    <rect x="793" y="340" width="130" height="62" rx="10" fill="#faf5ff" stroke="#a855f7" stroke-width="1.5"/>
    <text x="858" y="362" text-anchor="middle" font-size="12" font-weight="600" fill="#6b21a8">Gemini</text>
    <text x="858" y="378" text-anchor="middle" font-size="9.5" fill="#7c3aed">gemini-2.5-flash</text>
    <text x="858" y="392" text-anchor="middle" font-size="9.5" fill="#7c3aed">LLM via API</text>

    <!-- Confirmacion humana (amber/orange) -->
    <rect x="280" y="455" width="192" height="62" rx="10" fill="#fffbeb" stroke="#f59e0b" stroke-width="1.8"/>
    <text x="376" y="480" text-anchor="middle" font-size="13" font-weight="600" fill="#92400e">Confirmacion</text>
    <text x="376" y="498" text-anchor="middle" font-size="10.5" fill="#b45309">Validacion humana</text>

    <!-- DB Group (dashed, blue) -->
    <rect x="22" y="575" width="725" height="115" rx="14" fill="none" stroke="#3b82f6" stroke-width="1.5" stroke-dasharray="8,4"/>
    <text x="732" y="592" text-anchor="end" font-size="10" fill="#2563eb" font-style="italic">PostgreSQL 16 — medallon</text>

    <!-- Bronze (blue) -->
    <rect x="45" y="600" width="192" height="62" rx="10" fill="#eff6ff" stroke="#3b82f6" stroke-width="1.5"/>
    <text x="141" y="625" text-anchor="middle" font-size="13" font-weight="600" fill="#1e40af">Bronze</text>
    <text x="141" y="643" text-anchor="middle" font-size="10" fill="#1d4ed8">Datos crudos + logs</text>

    <!-- Silver (blue) -->
    <rect x="280" y="600" width="192" height="62" rx="10" fill="#eff6ff" stroke="#3b82f6" stroke-width="1.5"/>
    <text x="376" y="625" text-anchor="middle" font-size="13" font-weight="600" fill="#1e40af">Silver</text>
    <text x="376" y="643" text-anchor="middle" font-size="10" fill="#1d4ed8">Normalizado</text>

    <!-- Gold (blue) -->
    <rect x="515" y="600" width="192" height="62" rx="10" fill="#eff6ff" stroke="#3b82f6" stroke-width="1.5"/>
    <text x="611" y="625" text-anchor="middle" font-size="13" font-weight="600" fill="#1e40af">Gold</text>
    <text x="611" y="643" text-anchor="middle" font-size="10" fill="#1d4ed8">Agregados</text>

    <!-- Jupyter Lab (gray) -->
    <rect x="45" y="745" width="192" height="58" rx="10" fill="#f9fafb" stroke="#9ca3af" stroke-width="1.5"/>
    <text x="141" y="769" text-anchor="middle" font-size="12" font-weight="600" fill="#374151">Jupyter Lab</text>
    <text x="141" y="786" text-anchor="middle" font-size="10" fill="#6b7280">EDA + entrenamiento</text>

    <!-- Exportador (gray) -->
    <rect x="280" y="745" width="192" height="58" rx="10" fill="#f9fafb" stroke="#9ca3af" stroke-width="1.5"/>
    <text x="376" y="769" text-anchor="middle" font-size="12" font-weight="600" fill="#374151">Exportador</text>
    <text x="376" y="786" text-anchor="middle" font-size="10" fill="#6b7280">XLSX via Frontend</text>

    <!-- Power BI (rose/red) -->
    <rect x="515" y="745" width="192" height="58" rx="10" fill="#fff1f2" stroke="#fb7185" stroke-width="1.8"/>
    <text x="611" y="769" text-anchor="middle" font-size="12" font-weight="600" fill="#9f1239">Power BI</text>
    <text x="611" y="786" text-anchor="middle" font-size="10" fill="#be123c">Rendimiento + control</text>

    <!-- SAP (gray) -->
    <rect x="280" y="855" width="192" height="58" rx="10" fill="#f9fafb" stroke="#9ca3af" stroke-width="1.5"/>
    <text x="376" y="879" text-anchor="middle" font-size="12" font-weight="600" fill="#374151">SAP</text>
    <text x="376" y="896" text-anchor="middle" font-size="10" fill="#6b7280">Carga masiva</text>

    <!-- ==================== ARROWS ==================== -->

    <!-- Frontend → Planka (horizontal connector) -->
    <line x1="655" y1="53" x2="720" y2="53" stroke="#6b7280" stroke-width="1.3" stroke-dasharray="5,3"/>

    <!-- Frontend → Nginx -->
    <line x1="400" y1="88" x2="400" y2="128" stroke="#6b7280" stroke-width="1.5" marker-end="url(#ah)"/>

    <!-- Nginx → API -->
    <line x1="400" y1="183" x2="400" y2="225" stroke="#6b7280" stroke-width="1.5" marker-end="url(#ah)"/>

    <!-- API → Services (branching tree) -->
    <path d="M400,280 V310" stroke="#6b7280" stroke-width="1.5" fill="none"/>
    <path d="M400,310 H140 V340" stroke="#6b7280" stroke-width="1.5" fill="none" marker-end="url(#ah)"/>
    <line x1="400" y1="310" x2="400" y2="340" stroke="#6b7280" stroke-width="1.5" marker-end="url(#ah)"/>
    <path d="M400,310 H650 V340" stroke="#6b7280" stroke-width="1.5" fill="none" marker-end="url(#ah)"/>

    <!-- Norm ↔ Gemini (purple, bidirectional) -->
    <line x1="755" y1="371" x2="793" y2="371" stroke="#a855f7" stroke-width="1.5" marker-end="url(#ah-llm)" marker-start="url(#ah-llm-rev)"/>

    <!-- Services → Confirm (converging tree) -->
    <path d="M140,402 V428 H376" stroke="#6b7280" stroke-width="1.5" fill="none"/>
    <line x1="395" y1="402" x2="395" y2="428" stroke="#6b7280" stroke-width="1.5"/>
    <path d="M650,402 V428 H376" stroke="#6b7280" stroke-width="1.5" fill="none"/>
    <line x1="376" y1="428" x2="376" y2="455" stroke="#6b7280" stroke-width="1.5" marker-end="url(#ah)"/>

    <!-- Confirm → Silver (straight vertical) -->
    <line x1="376" y1="517" x2="376" y2="600" stroke="#6b7280" stroke-width="1.5" marker-end="url(#ah)"/>

    <!-- ETL side path: API left → Bronze (L-shaped, dashed) -->
    <path d="M275,252 H14 V631 H45" stroke="#6b7280" stroke-width="1.3" fill="none" stroke-dasharray="6,3" marker-end="url(#ah)"/>
    <text x="10" y="445" fill="#6b7280" font-size="10" text-anchor="middle" transform="rotate(-90,10,445)" font-style="italic">datos + logs</text>

    <!-- Bronze → Silver → Gold (blue arrows) -->
    <line x1="237" y1="631" x2="280" y2="631" stroke="#3b82f6" stroke-width="1.5" marker-end="url(#ah-db)"/>
    <line x1="472" y1="631" x2="515" y2="631" stroke="#3b82f6" stroke-width="1.5" marker-end="url(#ah-db)"/>

    <!-- Silver → Exportador (through group) -->
    <line x1="376" y1="662" x2="376" y2="745" stroke="#6b7280" stroke-width="1.5" marker-end="url(#ah)"/>

    <!-- Gold → Power BI (through group) -->
    <line x1="611" y1="662" x2="611" y2="745" stroke="#6b7280" stroke-width="1.5" marker-end="url(#ah)"/>

    <!-- DB group → Jupyter (dashed, EDA) -->
    <line x1="141" y1="690" x2="141" y2="745" stroke="#94a3b8" stroke-width="1.3" stroke-dasharray="6,3" marker-end="url(#ah)"/>

    <!-- Exportador → SAP -->
    <line x1="376" y1="803" x2="376" y2="855" stroke="#6b7280" stroke-width="1.5" marker-end="url(#ah)"/>

    <!-- ==================== LEGEND ==================== -->
    <g transform="translate(55, 940)">
      <rect x="0" y="0" width="16" height="12" rx="3" fill="#f0fdfa" stroke="#2dd4bf" stroke-width="1.2"/>
      <text x="22" y="10" font-size="10.5" fill="#4b5563">Frontend</text>

      <rect x="110" y="0" width="16" height="12" rx="3" fill="#f0f9ff" stroke="#38bdf8" stroke-width="1.2"/>
      <text x="132" y="10" font-size="10.5" fill="#4b5563">Infraestructura</text>

      <rect x="260" y="0" width="16" height="12" rx="3" fill="#f0fdf4" stroke="#4ade80" stroke-width="1.2"/>
      <text x="282" y="10" font-size="10.5" fill="#4b5563">Backend</text>

      <rect x="360" y="0" width="16" height="12" rx="3" fill="#fffbeb" stroke="#f59e0b" stroke-width="1.2"/>
      <text x="382" y="10" font-size="10.5" fill="#4b5563">Validacion humana</text>

      <rect x="530" y="0" width="16" height="12" rx="3" fill="#eff6ff" stroke="#3b82f6" stroke-width="1.2"/>
      <text x="552" y="10" font-size="10.5" fill="#4b5563">Capas medallon</text>

      <rect x="680" y="0" width="16" height="12" rx="3" fill="#faf5ff" stroke="#a855f7" stroke-width="1.2"/>
      <text x="702" y="10" font-size="10.5" fill="#4b5563">LLM externo</text>

      <rect x="800" y="0" width="16" height="12" rx="3" fill="#fff1f2" stroke="#fb7185" stroke-width="1.2"/>
      <text x="822" y="10" font-size="10.5" fill="#4b5563">Analitica</text>
    </g>
  </svg>
</template>
