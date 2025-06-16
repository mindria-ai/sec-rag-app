# sec-rag-app
Demo RAG application in high compliance industry to showcase Mindria integrations

## Goal

Build a locally runnable, Dockerized RAG (Retrieval-Augmented Generation) application that lets users query the latest S-1, S-1/A, Prospectus SEC filings for a given company to evaluate Pre-IPO value. The user provides their OpenAI API key, and the app returns a trustworthy, source-attributed answer.

## DEMO

-- TO ADD --

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
|   ├── pipeline/
|   |   ├── manual/               # Manual RAG logic
│   │   |   ├── loader.py         # Manual loading
│   │   |   ├── chunker.py        # Manual chunking - unstructured.io
│   │   |   ├── embedder.py       # Embedding
│   │   |   ├── vectorstore.py    # Vector store handling
│   │   |   ├── retriever.py      # Retriever logic
│   │   |   └── qa.py             # Manual QA logic
|   |   |
|   |   ├── langchain/            # LangChain-specific pipeline
│   │   |   ├── loader.py         # LangChain loader wrapper
│   │   |   ├── chunker.py        # LangChain text splitter
│   │   |   ├── embedder.py       # LangChain embeddings
│   │   |   ├── vectorstore.py    # LangChain vector store
│   │   |   ├── retriever.py      # RetrievalQAChain setup
│   │   |   └── qa.py             # LangChain QA abstraction
|   |   |
|   |   ├── llama_index/          # LlamaIndex-specific pipeline
│   │   |   ├── loader.py         # LlamaIndex Document creation
│   │   |   ├── chunker.py        # NodeParser logic
│   │   |   ├── embedder.py       # LlamaIndex embedding
│   │   |   ├── vectorstore.py    # VectorStoreIndex
│   │   |   ├── retriever.py      # RetrieverQueryEngine
│   │   |   ├── qa.py             # LlamaIndex QA handling
|   |
│   ├── core/                     # Shared logic between both pipelines
│   │   ├── sec_fetcher.py        # Download S-1, S-1/A, 424B4 (Prospectus)
│   │   ├── parser.py             # Clean\
│   │   └── utils.py              # Shared
│
│   ├── requirements.txt
├── chroma_store/                 # Local persisted vector DB
├── Dockerfile
├── docker-compose.yml
├── .env
```

