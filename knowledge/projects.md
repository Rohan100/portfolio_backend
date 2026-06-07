# Projects

## PortfolioBot
**Tech Stack:** Python, FastAPI, Groq API (LLaMA 3.3), Next.js, Tailwind CSS

An AI-powered chatbot that acts as Alex's digital representative on his portfolio website.
Visitors can ask questions about his skills, experience, and projects in natural language.

- Supports streaming responses via Server-Sent Events
- Built with a swappable LLM architecture (Groq → OpenAI → Gemini)
- Deployed on Railway; frontend on Vercel
- GitHub: https://github.com/alexjohnson/portfoliobot

---

## TaskFlow
**Tech Stack:** Next.js 14, Node.js, PostgreSQL, Prisma, Redis, Docker

A full-stack task management platform for teams, inspired by Linear and Notion.

- Real-time updates via WebSockets
- Role-based access control (RBAC)
- Drag-and-drop Kanban board
- 500+ active users in beta
- GitHub: https://github.com/alexjohnson/taskflow

---

## ShopSense
**Tech Stack:** React, FastAPI, MongoDB, OpenAI API, Stripe

An AI-powered e-commerce recommendation engine. Users describe what they're looking for
in natural language and ShopSense surfaces relevant products.

- Integrated with Stripe for checkout
- Achieved 38% improvement in click-through rates vs. traditional search
- Featured in ProductHunt's "Products of the Week"
- GitHub: https://github.com/alexjohnson/shopsense

---

## DevMetrics
**Tech Stack:** Go, PostgreSQL, Grafana, Docker, GitHub Actions

A developer productivity dashboard that aggregates GitHub, Jira, and CI/CD metrics.

- Processes 10,000+ events/day with sub-100ms query times
- Deployed as a self-hosted Docker Compose stack
- GitHub: https://github.com/alexjohnson/devmetrics
