# sec-rag-app
Demo RAG application for high compliance industry to showcase Mindria integrations

## Goal

Build a locally runnable, Dockerized RAG (Retrieval-Augmented Generation) application that lets users query the latest 10-K, 10-Q, 8-K SEC filings for a given company. The user provides their OpenAI API key, and the app returns a trustworthy, source-attributed answer.

## To Run
1. `make up`
-- clean up using `make down`

## Learnings

1. TO WRITE

## Project Structure

```
sec-rag-app/
├── app/
│   ├── main.py                   # Streamlit UI (chooses between manual/langchain)
│   ├── config.py                 # Global constants, env loading
│
│   ├── pipeline_manual/          # Manual RAG logic
│   │   ├── embedder.py
│   │   ├── retriever.py
│   │   └── qa.py
│
│   ├── pipeline_langchain/       # LangChain-specific pipeline
│   │   ├── chain.py              # LangChain RetrievalQAChain setup
│   │   ├── callbacks.py          # Optional Mindria or logging hooks
│   │   └── utils.py
│
│   ├── core/                     # Shared logic between both pipelines
│   │   ├── sec_fetcher.py        # Download 10-K/10-Q/8-K
│   │   ├── parser.py             # Clean + chunk with Unstructured
│   │   ├── vectorstore.py        # Chroma init and metadata mgmt
│   │   └── file_cache.py         # Local document caching
│
│   ├── requirements.txt
├── chroma_store/                 # Local persisted vector DB
├── Dockerfile
├── docker-compose.yml
├── .env
```

