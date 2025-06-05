import streamlit as st
from core.sec_fetcher import fetch_latest_filing
from pipeline.manual.qa import answer_question as manual_answer
from pipeline.langchain.chain import answer_question as langchain_answer

st.set_page_config(page_title="SEC RAG App", layout="centered")
st.title("🧾 SEC RAG Assistant")

# --- Pipeline Selection ---
rag_mode = st.radio("Choose RAG mode:", ["Manual", "LangChain"], horizontal=True)

# --- Filing Input ---
ticker = st.text_input("Enter stock ticker:", placeholder="e.g., AAPL")
form_type = st.selectbox("Form type:", ["10-K", "10-Q", "8-K"])

# --- Question Input ---
question = st.text_input("Ask a question:", placeholder="e.g., What were total revenues in 2023?")
submit = st.button("Run RAG")

# --- Main Flow ---
if submit and ticker and question:
    with st.spinner("Fetching and analyzing filing..."):

        # Step 1: Download latest SEC filing
        doc_path = fetch_latest_filing(ticker, form_type)

        # Step 2: RAG pipeline
        if rag_mode == "Manual":
            answer = manual_answer(doc_path, question)
        else:
            answer = langchain_answer(doc_path, question)

        # Step 3: Show Result
        st.success("Answer:")
        st.write(answer)
