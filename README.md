# Portfolio AI Chatbot — FastAPI Backend

A production-ready FastAPI backend powering a personal portfolio chatbot.
Visitors to the portfolio can ask natural-language questions and get answers
grounded in your knowledge base — no hallucination, no guesswork.

---

## ✨ Features

| Feature | Details |
|---|---|
| **Streaming** | SSE streaming via `POST /api/chat/stream` |
| **Conversation history** | Stateless — client sends last 10 messages |
| **Knowledge base** | Markdown files loaded + cached at startup |
| **Rate limiting** | 10 req/min per IP via `slowapi` |
| **Swappable LLM** | Abstract base — swap Groq → OpenAI/Gemini by changing one line |
| **CORS** | localhost:3000, localhost:5173 (Next.js & Vite) |
| **Auto-docs** | `/docs` (Swagger) and `/redoc` |

---

## 🗂 Project Structure

```
backend/
│
├── app/
│   ├── main.py              # FastAPI app, middleware, startup
│   ├── config.py            # Settings loaded from .env
│   ├── routes/
│   │   └── chat.py          # /api/chat, /api/chat/stream, /api/knowledge, /api/models
│   ├── schemas/
│   │   ├── chat_request.py  # ChatRequest, HistoryMessage
│   │   └── chat_response.py # ChatResponse, HealthResponse, etc.
│   ├── services/
│   │   ├── knowledge_service.py  # Reads & caches .md files
│   │   └── groq_service.py       # BaseLLMService + GroqService
│   ├── prompts/
│   │   └── system_prompt.txt     # Prompt template with {knowledge} placeholder
│   └── utils/
│       ├── prompt_loader.py      # Loads & renders the system prompt
│       └── message_builder.py   # Assembles messages list for the LLM
│
├── knowledge/
│   ├── about.md
│   ├── skills.md
│   ├── projects.md
│   ├── education.md
│   ├── experience.md
│   └── contact.md
│
├── .env                # Secret keys (never commit)
├── .env.example        # Template for new developers
├── requirements.txt
└── README.md
```

---

## 🚀 Quick Start

### 1. Clone & enter the backend

```bash
git clone <your-repo-url>
cd portfolio/backend
```

### 2. Create a virtual environment

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment

Copy `.env` and fill in your Groq API key:

```bash
# .env
GROQ_API_KEY=your_groq_api_key_here
MODEL=llama-3.3-70b-versatile
```

Get your free Groq API key at https://console.groq.com

### 5. Fill in your knowledge base

Edit the files in `knowledge/` — replace the placeholder content with your real info:

- `about.md` — who you are
- `skills.md` — your tech stack
- `projects.md` — what you've built
- `education.md` — degrees and certifications
- `experience.md` — work history
- `contact.md` — how to reach you

### 6. Run the server

```bash
uvicorn app.main:app --reload
```

Server starts at **http://localhost:8000**

---

## 📡 API Reference

### Health check
```
GET /health
→ { "status": "ok" }
```

### Non-streaming chat
```
POST /api/chat
Content-Type: application/json

{
  "message": "What projects have you built?",
  "history": [
    { "role": "user", "content": "Hi!" },
    { "role": "assistant", "content": "Hello! How can I help?" }
  ]
}

→ { "answer": "..." }
```

### Streaming chat (SSE)
```
POST /api/chat/stream
Content-Type: application/json

{ "message": "Tell me about your skills", "history": [] }

→ text/event-stream
data: I
data:  have
data:  experience in...
data: [DONE]
```

### List knowledge files
```
GET /api/knowledge
→ { "files": ["about.md", "skills.md", ...], "total": 6 }
```

### Current model
```
GET /api/models
→ { "current_model": "llama-3.3-70b-versatile", "provider": "groq" }
```

---

## 🔗 Frontend Integration (Next.js)

### Non-streaming (fetch)
```ts
const res = await fetch("http://localhost:8000/api/chat", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ message, history }),
});
const { answer } = await res.json();
```

### Streaming (ReadableStream)
```ts
const res = await fetch("http://localhost:8000/api/chat/stream", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ message, history }),
});

const reader = res.body!.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  const chunk = decoder.decode(value);
  const lines = chunk.split("\n\n").filter(Boolean);
  for (const line of lines) {
    const data = line.replace("data: ", "");
    if (data !== "[DONE]") setAnswer(prev => prev + data);
  }
}
```

### Vercel AI SDK
```ts
// In your Next.js route handler (app/api/chat/route.ts):
export async function POST(req: Request) {
  const body = await req.json();
  const upstream = await fetch("http://localhost:8000/api/chat/stream", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return new Response(upstream.body, {
    headers: { "Content-Type": "text/event-stream" },
  });
}
```

---

## ⚙️ Adding a New LLM Provider

1. Open `app/services/groq_service.py`
2. Create a class inheriting `BaseLLMService`
3. Implement `generate_response()` and `generate_stream()`
4. Return your new class from `get_llm_service()`

```python
# Example: switching to OpenAI
def get_llm_service() -> BaseLLMService:
    return OpenAIService()  # no route changes needed
```

---

## 🚢 Deployment (Railway / Render)

1. Push your code to GitHub (without `.env` — it's gitignored).
2. Create a new project on [Railway](https://railway.app) or [Render](https://render.com).
3. Connect your GitHub repo.
4. Set environment variables in the dashboard:
   - `GROQ_API_KEY`
   - `MODEL` (optional — defaults to `llama-3.3-70b-versatile`)
5. Set the start command:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```
6. Deploy ✅

---

## 📄 License

MIT
