# 📚 Book Agent

**AI-powered Book Review Generator — Python GraphQL Backend + Next.js Web + React Native Mobile**

Book Agent is a cross-platform project designed to learn and build end-to-end AI products across Web, iOS, and Android.
Users can search for books, fetch metadata, upload reference text/PDFs, choose an AI model, and generate both spoiler-friendly and spoiler-free book reviews.

---

## 🚀 Tech Stack

### **Backend**

- Python 3.11+
- FastAPI + Strawberry GraphQL
- httpx for external API calls
- pdfplumber for PDF extraction
- OpenAI / Perplexity / Google Models (provider-agnostic adapter)

### **Web (Frontend)**

- Next.js (App Router)
- React 18 + TypeScript
- React Query
- graphql-request

### **Mobile**

- React Native (Expo)
- React Query
- GraphQL client shared via workspace

### **Monorepo Structure**

```
book-agent/
└─ packages/
 ├─ backend/        # Python FastAPI + Strawberry GraphQL
 ├─ web-next/       # Next.js Web App
 ├─ mobile/         # Expo React Native App
 └─ shared/         # Shared GraphQL queries, types, utils
```

---

## ✨ Features (MVP)

- Search books (Google Books API)
- Fetch book metadata
- Spoiler / No-spoiler review generation
- Upload PDF/Text documents as context
- Choose model provider (OpenAI, Perplexity, Google)
- Configurable prefix/postfix prompts
- Works across Web, Android, and iOS

---

## 🔧 Getting Started

### Clone repository

```bash
git clone git@github.com:YOUR_USERNAME/book-agent.git
cd book-agent
```

---

# Create project structure

```bash
mkdir -p packages/backend packages/web-next packages/mobile packages/shared
```

---

# Environment variables

Create .env inside packages/backend:

```bash
PORT=4000
OPENAI_KEY=
GOOGLE_API_KEY=
PROMPT_PREFIX=You are an expert book reviewer.
PROMPT_POSTFIX=Keep it concise and helpful.
```

---

# 📦 Backlog / Future Enhancements

• OAuth (Login with Google / GitHub)
• RAG pipeline for deeper context from long PDFs
• Inline citations for reviews
• Book summary + rating + critique modes
• Offline support (mobile)
• i18n (multi-language output)

---

# 🧠 Purpose

This project is intentionally crafted as a learning curve to master:
• Python backend architecture
• GraphQL schemas & mutations
• Next.js App Router
• React Native + Expo fundamentals
• LLM provider abstractions
• Multi-platform folder structures
• API design & prompt engineering
• CI/CD + containerization (later phases)

---

# 📄 License

MIT License.
