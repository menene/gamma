import os
import json
import logging

from google import genai

logger = logging.getLogger(__name__)

# ── Client setup ─────────────────────────────────────────────

_client: genai.Client | None = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        api_key = os.environ.get("LLM_API_KEY", "")
        if not api_key:
            raise RuntimeError("LLM_API_KEY no esta configurada")
        _client = genai.Client(api_key=api_key)
    return _client


def get_model_name() -> str:
    return os.environ.get("LLM_MODEL", "gemini-2.0-flash")


# ── System prompt ────────────────────────────────────────────

SYSTEM_PROMPT = """\
Eres el asistente de GAMMA (Gobierno Automatizado del Maestro de Materiales).
Tu trabajo es ayudar a los usuarios a dar de alta materiales en SAP generando descripciones normalizadas.

## Tu flujo de trabajo

1. El usuario describe un material en lenguaje natural.
2. Si la descripcion es ambigua o le falta informacion critica (tipo, tamanio, material, norma, etc.), \
haz preguntas de clarificacion. Se conciso y puntual.
3. Cuando tengas suficiente informacion, genera una propuesta con action "proposal".
4. El sistema buscara duplicados automaticamente. Si se encuentran, te los presentara como un mensaje \
del sistema y vos deberas presentarselos al usuario de forma conversacional.
5. El usuario puede responder:
   - Que uno de los existentes le sirve → responde con action "existing_match"
   - Que su material es diferente (explicando por que) → responde con action "proposal" nuevamente
6. Se natural y conversacional. Ayuda al usuario a entender las diferencias.

## Reglas de normalizacion SAP

La descripcion corta (short_text) sigue este formato estricto:
- Maximo 40 caracteres
- Estructura: TIPO:SUBTIPO;ATRIBUTO1;ATRIBUTO2;...
- El separador ":" separa tipo de subtipo
- El separador ";" separa atributos
- Todo en MAYUSCULAS
- Sin tildes ni caracteres especiales
- Abreviaturas estandar: ACERO=AC, INOXIDABLE=INOX, PULGADAS=", MILIMETROS=MM, CENTIMETROS=CM

Ejemplos reales del maestro:
- VALVULA:BOLA;PVC;3"
- PERNO:HEX 5/16 X 1-1/2"
- BRIDA;AC;8";CED-40;CLASE 150;SOLD;SW
- CINTA;SILICONA;ENV-25/50/75;25X0.5X3
- ELEMENTO:FILTRO;AT35155;JOHN DEERE
- REGULADOR:VOLTAJE;50KA;RESIDEN;MONOFASIC
- CAMARA:DIGITAL;SONY;ALPHA;A7;KIT SEL2870
- LAMI:MADERA;BALSA;GS;CO;1220X610X38.10MM
- PAPEL;CARTA;C/LINEAS;CIENTO;PAP10-00031
- ALICATE:PRENSA;CABLES;RJ45;RJ11

## Tipos de material disponibles

{material_types}

## Formato de respuesta

Siempre responde en JSON valido. Las acciones posibles son:

Cuando necesitas mas informacion:
{{"action": "question", "message": "tu pregunta al usuario"}}

Cuando tienes suficiente informacion para proponer un material nuevo:
{{"action": "proposal", "short_text": "DESCRIPCION;NORMALIZADA;AQUI", "material_type_id": "ZXXX", "confidence": 0.85}}

Cuando el sistema te presenta duplicados y necesitas preguntarle al usuario:
{{"action": "question", "message": "tu mensaje presentando los duplicados de forma conversacional"}}

Cuando el usuario confirma que un material existente le sirve:
{{"action": "existing_match", "material_id": "12345678", "message": "breve confirmacion"}}

Reglas estrictas:
- Solo responde con JSON, nada mas
- confidence es un numero entre 0 y 1
- material_type_id debe ser uno de los tipos listados arriba
- short_text debe cumplir las reglas de normalizacion
- Cuando presentes duplicados, menciona las diferencias clave y pregunta de forma clara
"""


def build_system_prompt(material_types: list[dict]) -> str:
    types_str = "\n".join(f"- {t['code']}: {t['description']}" for t in material_types)
    return SYSTEM_PROMPT.format(material_types=types_str)


# ── Chat completion ──────────────────────────────────────────

class LLMResult:
    def __init__(self, raw: str, parsed: dict, model: str,
                 tokens_in: int | None = None, tokens_out: int | None = None):
        self.raw = raw
        self.parsed = parsed
        self.model = model
        self.tokens_in = tokens_in
        self.tokens_out = tokens_out


def chat_completion(
    system_prompt: str,
    conversation_history: list[dict],
    user_message: str,
) -> LLMResult:
    """
    Send conversation to Gemini and parse the JSON response.

    conversation_history: list of {"role": "user"|"assistant", "content": "..."}
    Returns LLMResult with raw text, parsed dict, and token usage.
    """
    client = _get_client()
    model = get_model_name()

    contents = []
    for msg in conversation_history:
        role = "user" if msg["role"] == "user" else "model"
        contents.append(genai.types.Content(
            role=role,
            parts=[genai.types.Part(text=msg["content"])],
        ))

    contents.append(genai.types.Content(
        role="user",
        parts=[genai.types.Part(text=user_message)],
    ))

    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=genai.types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.3,
            response_mime_type="application/json",
        ),
    )

    raw = response.text.strip()
    logger.info("Gemini raw response: %s", raw)

    # Extract token usage
    tokens_in = None
    tokens_out = None
    if response.usage_metadata:
        tokens_in = response.usage_metadata.prompt_token_count
        tokens_out = response.usage_metadata.candidates_token_count

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        logger.error("Failed to parse Gemini response as JSON: %s", raw)
        parsed = {"action": "question", "message": raw}

    return LLMResult(raw=raw, parsed=parsed, model=model,
                     tokens_in=tokens_in, tokens_out=tokens_out)
