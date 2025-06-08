import streamlit as st
from core.sec_fetcher import fetch_latest_filing
from core.parser import parse_sec_htm_file
from pipeline.manual.qa import answer_question as manual_answer
from pipeline.langchain.chain import answer_question as langchain_answer
import os

st.set_page_config(page_title="SEC RAG App", layout="wide")
st.title("🗞 Pre-IPO RAG Evaluator")

# --- Cost Estimation Constants ---
COST_PER_1K_EMBED_TOKENS = 0.00002  # text-embedding-3-small
COST_PER_1K_INPUT_TOKENS_GPT4O = 0.005
COST_PER_1K_OUTPUT_TOKENS_GPT4O = 0.015

# --- Session Cost Tracker ---
if "embedding_tokens" not in st.session_state:
    st.session_state.embedding_tokens = 0
if "qa_input_tokens" not in st.session_state:
    st.session_state.qa_input_tokens = 0
if "qa_output_tokens" not in st.session_state:
    st.session_state.qa_output_tokens = 0

# --- Layout with sidebar and right cost column ---
main_col, cost_col = st.columns([6, 2])

# --- Sidebar for parameter controls (restores collapsibility) ---
with st.sidebar:
    st.markdown("### 🔧 Model Parameters")
    st.markdown("<small><i>Select your generation model for answering questions.</i></small>", unsafe_allow_html=True)
    rag_mode = st.radio("Choose RAG mode:", ["Manual", "LangChain"], horizontal=True)

    model = st.selectbox("Model", ["gpt-4o", "gpt-3.5-turbo"], help="LLM used to answer questions. GPT-4o is more accurate, GPT-3.5 is cheaper.")
    st.session_state.model = model
    embedding_model = st.selectbox(
        "Embedding Model",
        ["text-embedding-3-small", "text-embedding-ada-002"],
        help=(
            """
            - `text-embedding-3-small`: Fast, cheaper, best for most use cases.
            - `text-embedding-ada-002`: Older but more widely supported.
            """
        )
    )
    temperature = st.slider("Temperature", 0.0, 1.5, 0.2, 0.05, help="Controls randomness. Lower = more focused, higher = more creative.")
    top_p = st.slider("Top-p (nucleus sampling)", 0.0, 1.0, 1.0, 0.05, help="Limits token selection to top probability mass p. Use with temperature.")
    max_tokens = st.slider("Max tokens", 100, 4096, 1024, 100, help="Maximum number of tokens the model is allowed to generate in its response.")

    st.markdown("### 🧠 Retrieval Settings")
    top_k = st.slider("Top K chunks", 1, 20, 5, help="Number of most relevant text chunks to retrieve and include as context.")
    context_window = st.slider("Context window (max tokens)", 500, 10000, 3000, 500, help="Maximum total token count for all retrieved chunks combined.")

    params = {
        "model": model,
        "embedding_model": embedding_model,
        "temperature": temperature,
        "top_p": top_p,
        "max_tokens": max_tokens,
        "top_k": top_k,
        "context_window": context_window
    }

# --- Main section in center ---
with main_col:
    st.markdown("Use this assistant to analyze a company's registration filings before its IPO. Information is directly pulled from the SEC. Enter the company ticker below to automatically retrieve its S-1, S-1/A, and final prospectus.")
    st.markdown("*This application is not liable for any decisions made by the user based on the output.*")

    ipo_ticker = st.text_input("Pre-IPO company ticker", placeholder="e.g., BIRD", key="ipo_ticker")

    if ipo_ticker:
        st.markdown("#### 📊 Estimated Embedding Cost (all documents)")
        avg_tokens = 100_000 * 3  # Assume 3 docs × 100k each
        if embedding_model == "text-embedding-3-small":
            cost_per_1k = 0.00002
        elif embedding_model == "text-embedding-ada-002":
            cost_per_1k = 0.0001
        else:
            cost_per_1k = 0.0
        estimated_cost = (avg_tokens / 1000) * cost_per_1k
        st.info(f"Estimated cost to embed S-1, S-1/A, and Prospectus: **~${estimated_cost:.4f}** for ~{avg_tokens:,} tokens.")

    if st.button("Generate Pre-IPO Summary") and ipo_ticker:
        with st.spinner("Gathering S-1, S-1/A, and Prospectus..."):
            form_types = ["S-1", "S-1/A", "424B4"]
            answers = []

            for form in form_types:
                try:
                    doc_info = fetch_latest_filing(ipo_ticker, form)
                    doc_path = doc_info["main_doc_path"]

                    chunks = parse_sec_htm_file(doc_path)

                    print("number of chunks", len(chunks))

                    if rag_mode == "Manual":
                        answer = manual_answer(doc_path, "What are the major risks, financials, and use of proceeds?", params=params)
                    else:
                        answer = langchain_answer(doc_path, "What are the major risks, financials, and use of proceeds?", params=params)
                    answers.append(f"**{form}**:\n\n{answer}")

                except Exception as e:
                    answers.append(f"**{form}**: Error - {e}")

            st.success("Pre-IPO Summary")
            for ans in answers:
                st.markdown(ans)

# --- Right column for cost tracking ---
with cost_col:
    st.markdown("### 💲 Cost Estimation")
    if params['embedding_model'] == 'text-embedding-3-small':
        embed_cost = (st.session_state.embedding_tokens / 1000) * 0.00002
    elif params['embedding_model'] == 'text-embedding-ada-002':
        embed_cost = (st.session_state.embedding_tokens / 1000) * 0.0001
    else:
        embed_cost = 0
    if model == "gpt-4o":
        input_cost = (st.session_state.qa_input_tokens / 1000) * COST_PER_1K_INPUT_TOKENS_GPT4O
        output_cost = (st.session_state.qa_output_tokens / 1000) * COST_PER_1K_OUTPUT_TOKENS_GPT4O
    else:
        input_cost = (st.session_state.qa_input_tokens / 1000) * 0.001
        output_cost = (st.session_state.qa_output_tokens / 1000) * 0.002

    qa_cost = input_cost + output_cost

    st.markdown(f"**Embedding tokens:** {st.session_state.embedding_tokens} (~${embed_cost:.4f})")
    st.markdown(f"**Q&A input tokens:** {st.session_state.qa_input_tokens} (~${input_cost:.4f})")
    st.markdown(f"**Q&A output tokens:** {st.session_state.qa_output_tokens} (~${output_cost:.4f})")
    st.markdown(f"**Total Estimated Cost:** ~${embed_cost + qa_cost:.4f}")
