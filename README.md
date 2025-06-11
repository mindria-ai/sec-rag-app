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
│   │   |   ├── embedder.py
│   │   |   ├── retriever.py
│   │   |   └── qa.py
|   |   |
|   |   ├── langchain/            # LangChain-specific pipeline
│   │   |   ├── chain.py          # LangChain RetrievalQAChain setup
│   │   |   ├── callbacks.py      # Optional Mindria or logging hooks
│   │   |   └── utils.py
|   |   |
|   |   ├── llama_index/          # LlamaIndex-specific pipeline
|   |   |   └── TODO
|   |
│   ├── core/                     # Shared logic between both pipelines
│   │   ├── sec_fetcher.py        # Download S-1, S-1/A, 424B4 (Prospectus)
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

