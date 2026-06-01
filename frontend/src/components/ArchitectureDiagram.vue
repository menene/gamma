<template>
  <svg viewBox="0 0 940 980" xmlns="http://www.w3.org/2000/svg" font-family="Inter, system-ui, sans-serif" class="w-full h-auto">
    <rect width="940" height="980" fill="white" rx="8"/>

    <defs>
      <marker id="ah" viewBox="0 0 10 8" refX="9" refY="4" markerWidth="8" markerHeight="6" orient="auto">
        <path d="M0,0 L10,4 L0,8 Z" fill="#6b7280"/>
      </marker>
      <marker id="ah-purple" viewBox="0 0 10 8" refX="9" refY="4" markerWidth="8" markerHeight="6" orient="auto">
        <path d="M0,0 L10,4 L0,8 Z" fill="#a78bfa"/>
      </marker>
      <marker id="ah-violet" viewBox="0 0 10 8" refX="9" refY="4" markerWidth="8" markerHeight="6" orient="auto">
        <path d="M0,0 L10,4 L0,8 Z" fill="#c084fc"/>
      </marker>
      <marker id="ah-violet-rev" viewBox="0 0 10 8" refX="1" refY="4" markerWidth="8" markerHeight="6" orient="auto">
        <path d="M10,0 L0,4 L10,8 Z" fill="#c084fc"/>
      </marker>
    </defs>

    <!-- ==================== NODES ==================== -->

    <!-- Frontend -->
    <rect x="145" y="18" width="510" height="70" rx="12" fill="#f0fdf4" stroke="#86efac" stroke-width="1.8"/>
    <text x="400" y="44" text-anchor="middle" font-size="14" font-weight="600" fill="#166534">Frontend</text>
    <text x="400" y="64" text-anchor="middle" font-size="10.5" fill="#4b5563">Vue 3 + Vite — Login · Chatbot · ETL · Exportador</text>

    <!-- Planka -->
    <rect x="720" y="25" width="160" height="56" rx="10" fill="#f1f5f9" stroke="#94a3b8" stroke-width="1.4"/>
    <text x="800" y="48" text-anchor="middle" font-size="12" font-weight="600" fill="#334155">Planka</text>
    <text x="800" y="64" text-anchor="middle" font-size="9.5" fill="#6b7280">Gestion de tareas</text>

    <!-- Nginx + JWT -->
    <rect x="275" y="128" width="250" height="55" rx="10" fill="#fef3c7" stroke="#fbbf24" stroke-width="1.8"/>
    <text x="400" y="151" text-anchor="middle" font-size="13" font-weight="600" fill="#92400e">Nginx + JWT</text>
    <text x="400" y="168" text-anchor="middle" font-size="10.5" fill="#b45309">Reverse proxy · Autenticacion</text>

    <!-- API REST -->
    <rect x="275" y="225" width="250" height="55" rx="10" fill="#e0f7f0" stroke="#34d399" stroke-width="1.8"/>
    <text x="400" y="248" text-anchor="middle" font-size="13" font-weight="600" fill="#065f46">API REST</text>
    <text x="400" y="265" text-anchor="middle" font-size="10.5" fill="#047857">FastAPI · Python 3.12</text>

    <!-- Duplicados -->
    <rect x="35" y="340" width="210" height="62" rx="10" fill="#e0f7f0" stroke="#34d399" stroke-width="1.5"/>
    <text x="140" y="365" text-anchor="middle" font-size="13" font-weight="600" fill="#065f46">Duplicados</text>
    <text x="140" y="383" text-anchor="middle" font-size="10" fill="#047857">pg_trgm · PostgreSQL</text>

    <!-- Categorizacion -->
    <rect x="290" y="340" width="210" height="62" rx="10" fill="#e0f7f0" stroke="#34d399" stroke-width="1.5"/>
    <text x="395" y="365" text-anchor="middle" font-size="13" font-weight="600" fill="#065f46">Categorizacion</text>
    <text x="395" y="383" text-anchor="middle" font-size="10" fill="#047857">Modelo ML</text>

    <!-- Normalizacion -->
    <rect x="545" y="340" width="210" height="62" rx="10" fill="#e0f7f0" stroke="#34d399" stroke-width="1.5"/>
    <text x="650" y="365" text-anchor="middle" font-size="13" font-weight="600" fill="#065f46">Normalizacion</text>
    <text x="650" y="383" text-anchor="middle" font-size="10" fill="#047857">Descripcion SAP</text>

    <!-- Gemini -->
    <rect x="793" y="347" width="130" height="48" rx="10" fill="#faf5ff" stroke="#c084fc" stroke-width="1.5"/>
    <text x="858" y="367" text-anchor="middle" font-size="12" font-weight="600" fill="#6b21a8">Gemini</text>
    <text x="858" y="382" text-anchor="middle" font-size="9.5" fill="#7c3aed">LLM via API</text>

    <!-- Confirmacion humana -->
    <rect x="290" y="455" width="210" height="62" rx="10" fill="#fffbeb" stroke="#f59e0b" stroke-width="1.8"/>
    <text x="395" y="480" text-anchor="middle" font-size="13" font-weight="600" fill="#92400e">Confirmacion</text>
    <text x="395" y="498" text-anchor="middle" font-size="10.5" fill="#b45309">Validacion humana</text>

    <!-- DB Group (dashed) -->
    <rect x="22" y="575" width="725" height="115" rx="14" fill="none" stroke="#a78bfa" stroke-width="1.5" stroke-dasharray="8,4"/>
    <text x="732" y="592" text-anchor="end" font-size="10" fill="#7c3aed" font-style="italic">PostgreSQL 16 — medallon</text>

    <!-- Bronze -->
    <rect x="45" y="600" width="192" height="62" rx="10" fill="#ede9fe" stroke="#a78bfa" stroke-width="1.5"/>
    <text x="141" y="625" text-anchor="middle" font-size="13" font-weight="600" fill="#5b21b6">Bronze</text>
    <text x="141" y="643" text-anchor="middle" font-size="10" fill="#6d28d9">Datos crudos + logs</text>

    <!-- Silver -->
    <rect x="280" y="600" width="192" height="62" rx="10" fill="#ede9fe" stroke="#a78bfa" stroke-width="1.5"/>
    <text x="376" y="625" text-anchor="middle" font-size="13" font-weight="600" fill="#5b21b6">Silver</text>
    <text x="376" y="643" text-anchor="middle" font-size="10" fill="#6d28d9">Normalizado</text>

    <!-- Gold -->
    <rect x="515" y="600" width="192" height="62" rx="10" fill="#ede9fe" stroke="#a78bfa" stroke-width="1.5"/>
    <text x="611" y="625" text-anchor="middle" font-size="13" font-weight="600" fill="#5b21b6">Gold</text>
    <text x="611" y="643" text-anchor="middle" font-size="10" fill="#6d28d9">Agregados</text>

    <!-- Jupyter Lab -->
    <rect x="45" y="745" width="192" height="58" rx="10" fill="#f1f5f9" stroke="#94a3b8" stroke-width="1.5"/>
    <text x="141" y="769" text-anchor="middle" font-size="12" font-weight="600" fill="#334155">Jupyter Lab</text>
    <text x="141" y="786" text-anchor="middle" font-size="10" fill="#6b7280">EDA + entrenamiento</text>

    <!-- Exportador -->
    <rect x="280" y="745" width="192" height="58" rx="10" fill="#f9fafb" stroke="#9ca3af" stroke-width="1.5"/>
    <text x="376" y="769" text-anchor="middle" font-size="12" font-weight="600" fill="#334155">Exportador</text>
    <text x="376" y="786" text-anchor="middle" font-size="10" fill="#6b7280">XLSX via Frontend</text>

    <!-- Power BI -->
    <rect x="515" y="745" width="192" height="58" rx="10" fill="#fef2f2" stroke="#f87171" stroke-width="1.8"/>
    <text x="611" y="769" text-anchor="middle" font-size="12" font-weight="600" fill="#991b1b">Power BI</text>
    <text x="611" y="786" text-anchor="middle" font-size="10" fill="#b91c1c">Monetizacion</text>

    <!-- SAP -->
    <rect x="280" y="855" width="192" height="58" rx="10" fill="#e0f7f0" stroke="#34d399" stroke-width="1.5"/>
    <text x="376" y="879" text-anchor="middle" font-size="12" font-weight="600" fill="#065f46">SAP</text>
    <text x="376" y="896" text-anchor="middle" font-size="10" fill="#047857">Carga masiva</text>

    <!-- ==================== ARROWS ==================== -->

    <!-- Frontend → Nginx -->
    <line x1="400" y1="88" x2="400" y2="128" stroke="#6b7280" stroke-width="1.5" marker-end="url(#ah)"/>

    <!-- Nginx → API -->
    <line x1="400" y1="183" x2="400" y2="225" stroke="#6b7280" stroke-width="1.5" marker-end="url(#ah)"/>

    <!-- API → Services (branching tree) -->
    <path d="M400,280 V310" stroke="#6b7280" stroke-width="1.5" fill="none"/>
    <path d="M400,310 H140 V340" stroke="#6b7280" stroke-width="1.5" fill="none" marker-end="url(#ah)"/>
    <line x1="400" y1="310" x2="400" y2="340" stroke="#6b7280" stroke-width="1.5" marker-end="url(#ah)"/>
    <path d="M400,310 H650 V340" stroke="#6b7280" stroke-width="1.5" fill="none" marker-end="url(#ah)"/>

    <!-- Norm ↔ Gemini -->
    <line x1="755" y1="371" x2="793" y2="371" stroke="#c084fc" stroke-width="1.5" marker-end="url(#ah-violet)" marker-start="url(#ah-violet-rev)"/>

    <!-- Services → Confirm (converging tree) -->
    <path d="M140,402 V428 H395" stroke="#6b7280" stroke-width="1.5" fill="none"/>
    <line x1="395" y1="402" x2="395" y2="428" stroke="#6b7280" stroke-width="1.5"/>
    <path d="M650,402 V428 H395" stroke="#6b7280" stroke-width="1.5" fill="none"/>
    <line x1="395" y1="428" x2="395" y2="455" stroke="#6b7280" stroke-width="1.5" marker-end="url(#ah)"/>

    <!-- Confirm → Silver -->
    <line x1="395" y1="517" x2="376" y2="600" stroke="#6b7280" stroke-width="1.5" marker-end="url(#ah)"/>

    <!-- ETL side path: API left → Bronze (L-shaped, dashed) -->
    <path d="M275,252 H14 V631 H45" stroke="#6b7280" stroke-width="1.3" fill="none" stroke-dasharray="6,3" marker-end="url(#ah)"/>
    <text x="10" y="445" fill="#6b7280" font-size="10" text-anchor="middle" transform="rotate(-90,10,445)" font-style="italic">datos + logs</text>

    <!-- Bronze → Silver → Gold -->
    <line x1="237" y1="631" x2="280" y2="631" stroke="#a78bfa" stroke-width="1.5" marker-end="url(#ah-purple)"/>
    <line x1="472" y1="631" x2="515" y2="631" stroke="#a78bfa" stroke-width="1.5" marker-end="url(#ah-purple)"/>

    <!-- Silver → Exportador (through group) -->
    <line x1="376" y1="662" x2="376" y2="745" stroke="#6b7280" stroke-width="1.5" marker-end="url(#ah)"/>

    <!-- Gold → Power BI (through group) -->
    <line x1="611" y1="662" x2="611" y2="745" stroke="#6b7280" stroke-width="1.5" marker-end="url(#ah)"/>

    <!-- DB group → Jupyter (dashed, EDA) -->
    <line x1="141" y1="690" x2="141" y2="745" stroke="#94a3b8" stroke-width="1.3" stroke-dasharray="6,3" marker-end="url(#ah)"/>

    <!-- Exportador → SAP -->
    <line x1="376" y1="803" x2="376" y2="855" stroke="#6b7280" stroke-width="1.5" marker-end="url(#ah)"/>

    <!-- ==================== LEGEND ==================== -->
    <g transform="translate(95, 940)">
      <rect x="0" y="0" width="16" height="12" rx="3" fill="#e0f7f0" stroke="#34d399" stroke-width="1.2"/>
      <text x="22" y="10" font-size="10.5" fill="#4b5563">Backend</text>

      <rect x="130" y="0" width="16" height="12" rx="3" fill="#fffbeb" stroke="#f59e0b" stroke-width="1.2"/>
      <text x="152" y="10" font-size="10.5" fill="#4b5563">Validacion humana</text>

      <rect x="310" y="0" width="16" height="12" rx="3" fill="#ede9fe" stroke="#a78bfa" stroke-width="1.2"/>
      <text x="332" y="10" font-size="10.5" fill="#4b5563">Capas medallon</text>

      <rect x="460" y="0" width="16" height="12" rx="3" fill="#fef2f2" stroke="#f87171" stroke-width="1.2"/>
      <text x="482" y="10" font-size="10.5" fill="#4b5563">Monetizacion</text>

      <rect x="600" y="0" width="16" height="12" rx="3" fill="#faf5ff" stroke="#c084fc" stroke-width="1.2"/>
      <text x="622" y="10" font-size="10.5" fill="#4b5563">LLM externo</text>
    </g>
  </svg>
</template>
