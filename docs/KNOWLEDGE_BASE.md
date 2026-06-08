# Knowledge Base

## Overview

The knowledge app (`apps/knowledge/`) stores business content that agents use during conversations.

## Source Types

| Type | Use case |
|------|----------|
| text | General business information |
| faq | Question and answer pairs |
| pricing | Pricing plans and tiers |
| policy | Refund, privacy, terms |
| upload | File upload (text extracted) |
| url | URL reference (content stored as text) |

## Chunks

When a source is created or updated, `create_chunks_for_source()` splits content into ~500 character paragraph-aware chunks stored in `KnowledgeChunk`.

Each chunk has:
- `chunk_text` — searchable text
- `embedding` — JSON field reserved for pgvector (not populated in MVP)
- `metadata_json` — index, source_type

## Search Fallback (MVP)

**File:** `apps/knowledge/services.py` — `search_knowledge_for_agent()`

Keyword-based search using Django `icontains` on `chunk_text`:

1. Tokenize query into words (length > 2)
2. Match chunks containing any token
3. Boost chunks from `pricing` type sources for pricing queries
4. Return top N results (default 5)

No vector embeddings in MVP. Design is pgvector-ready via `embedding` JSON field.

## Agent Knowledge Search

**File:** `apps/agent_engine/services/knowledge_search.py`

Two-tier search:

1. **Agent settings** — keyword match on business_description, services_json, pricing_json
2. **Knowledge chunks** — delegates to knowledge service

Results formatted as bullet list and injected into system prompt via `PromptBuilder`.

## How Agent Uses Snippets

```
Customer: "What is your refund policy?"
  -> KnowledgeSearchService.search()
  -> Finds chunk from "Refund Policy" source
  -> PromptBuilder adds to system prompt context
  -> AI generates reply citing policy content
```

## Adding Knowledge

### Via UI

1. Go to `/knowledge/`
2. Click "Add Source"
3. Enter title, type, and content
4. Chunks are created automatically

### Via API

```bash
curl -X POST http://localhost:8000/api/knowledge/ \
  -H "Content-Type: application/json" \
  -d '{"title": "FAQ", "content": "...", "source_type": "faq"}'
```

### Via seed script

```bash
python scripts/seed_knowledge_demo.py
```

### Agent-scoped vs tenant-wide

- `agent_instance` set — visible only to that agent's search
- `agent_instance` null — tenant-wide, all agents can search

## Future: pgvector

To enable semantic search:

1. Install pgvector extension in PostgreSQL
2. Populate `embedding` field via OpenAI/local embedding model
3. Replace keyword search with cosine similarity query
4. Keep keyword fallback for missing embeddings
