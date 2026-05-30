#  Sistema de triaje médico automático - PoC

Implementación de la prueba de concepto descrita en la Entrega 2 del proyecto:
extracción de entidades (T2), diagnóstico probable (T3), clasificación de gravedad (T4)
y resumen generativo (T5) sobre descripciones de pacientes en español. De esta form, se implementan C2, C3, C4 y C5 según se prometió en la memoria

(Para descargar datos y modelos, el siguiente [enlace](https://drive.google.com/drive/folders/1y73DAeSr_U1MRMD51E5z8C3Pa8S5G80F?usp=sharing))

---

## Arquitectura



- **Frontend**: Vite + React + TypeScript, sirviéndose tras nginx, que actúa además como proxy de `/api/`.
- **Backend**: FastAPI con los modelos cargados en memoria al arranque (lifespan).
- **Modelos**: Montados como volumen `:ro` desde [entrenamiento_modelos/modelos/](entrenamiento_modelos/modelos/). No se copian dentro de la imagen.
- **Informes**: Cada ejecución de `/api/report` genera un `.md` en `./reports/` (carpeta del host).

---

## Despliegue rápido

### Requisitos
- Docker Desktop con Docker Compose v2.
- Los modelos entrenados deben existir en [entrenamiento_modelos/modelos/](entrenamiento_modelos/modelos/).
- Conexión a internet solo en el primer arranque para descargar el modelo mT5 de HuggingFace, que quedan cacheados en el volumen `hf-cache`.

### Arranque

```bash
docker compose up --build
```

Tras varios minutos, los servicios estarán listos:

- Frontend en http://localhost:3000
- API en http://localhost:8000/api/health

### Configuración mediante `.env` (backend)

El backend lee variables desde [backend/.env](backend/.env). Hay un [backend/.env.example](backend/.env.example) de referencia:

```bash
cp backend/.env.example backend/.env   # solo la primera vez
```

| Variable | Valores | Por defecto | Descripción |
| -------- | ------- | ----------- | ----------- |
| `TRIAGE_MODEL` | `roberta` \| `baseline` | `roberta` | **Modelo activo para T4 (triaje de gravedad).** `roberta` usa el modelo sistema (RoBERTa biomédica con ajuste fino). `baseline` usa el clasificador TF-IDF + Regresión logística. |

Para cambiar de modelo basta con editar el `.env` y reiniciar **solo** el backend:

```bash
docker compose restart backend
```

El cambio no requiere `--build`: el `.env` se inyecta en tiempo de ejecución vía `env_file` en [docker-compose.yml](docker-compose.yml). El endpoint `GET /api/health` devuelve el backend de triaje activo para verificarlo.

### Acceso a los informes

Los `.md` generados se escriben directamente en la carpeta `./reports/` del host:

```
trabajo_pln/
├── reports/
│   ├── informe_20260520_143012.md
│   └── informe_20260520_152418.md
```

Puedes abrirlos con tu editor o renderizador favorito sin entrar al contenedor.

---

## Uso

1. Ve a [http://localhost:3000](http://localhost:3000).
2. Pulsa el botón de micrófono.
3. Escribe la descripción del paciente (en lugar del audio) y envía.
4. El sistema muestra los síntomas y enfermedades detectados. Confirma para continuar.
5. Se genera el informe completo y se guarda en `./reports/`. Sepuede descargar.
6. 
---

## Estructura

```
trabajo_pln/
├── docker-compose.yml
├── README.md
├── reports/                       ← informes .md generados (host)
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py
│   └── pipeline/
│       ├── ner.py
│       ├── diagnosis.py
│       ├── triage.py
│       ├── summarizer.py
│       └── report.py
├── frontend/
│   ├── Dockerfile
│   ├── nginx.conf
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── index.html
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── api.ts
│       ├── styles.css
│       └── components/
│           ├── RecordButton.tsx
│           ├── TextModal.tsx
│           ├── NERPreview.tsx
│           └── Results.tsx
└── entrenamiento_modelos/
    └── modelos/
        ├── t2_ner/
        ├── t3_diagnostico/
        └── t4_triaje/
```

---

## Desarrollo (sin Docker, no lo recomendamos)

### Backend

```bash
cd backend
uv venv
uv pip install -r requirements.txt
MODELS_DIR=../entrenamiento_modelos/modelos REPORTS_DIR=../reports uvicorn main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```
