import sys
import os
import streamlit as st
import hashlib
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

# Ensure 'src' is discoverable
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.document_processor import DocumentProcessor
from src.vectorstore import VectorStoreManager
from src.agent import create_documentation_agent
from src.tools import create_search_tool
from src.structure_visualizer import DocumentStructureVisualizer

load_dotenv()
st.set_page_config(page_title="AI Document Intelligence", layout="wide")

# Initialize Managers
if "vs_manager" not in st.session_state:
    st.session_state.vs_manager = VectorStoreManager()
if "processor" not in st.session_state:
    st.session_state.processor = DocumentProcessor()

def get_hash(content):
    return hashlib.sha256(content).hexdigest()

# --- Sidebar ---
with st.sidebar:
    st.title("📚 Library")
    files = st.session_state.vs_manager.get_all_filenames()
    for f in files: st.caption(f"✅ {f}")
    
    st.divider()
    uploads = st.file_uploader("Upload PDFs", accept_multiple_files=True, type=["pdf"])
    if uploads and st.button("🚀 Hard-Read & Index"):
        new_data = []
        for f in uploads:
            f_hash = get_hash(f.getbuffer())
            if not st.session_state.vs_manager.file_exists(f_hash):
                with st.spinner(f"OCR Scanning {f.name}..."):
                    docs, d_data = st.session_state.processor.process_uploaded_files([f])
                    st.session_state.vs_manager.add_documents(docs, f_hash)
                    new_data.extend(d_data)
        if new_data: st.session_state['preview_data'] = new_data
        st.rerun()

# --- Agent Logic ---
if "agent" not in st.session_state and len(st.session_state.vs_manager.get_all_filenames()) > 0:
    tool = create_search_tool(st.session_state.vs_manager.vectorstore)
    st.session_state.agent = create_documentation_agent([tool])

# --- Main UI ---
tab1, tab2 = st.tabs(["💬 AI Chat", "📊 Document Insights"])

with tab1:
    if "messages" not in st.session_state: st.session_state.messages = []
    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    if prompt := st.chat_input("Ask anything..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        
        if "agent" in st.session_state:
            with st.chat_message("assistant"):
                resp = st.session_state.agent.invoke({"messages": [HumanMessage(content=prompt)]})
                ans = resp["messages"][-1].content
                st.markdown(ans)
                st.session_state.messages.append({"role": "assistant", "content": ans})
        else: st.warning("Please index documents first.")

with tab2:
    if 'preview_data' in st.session_state:
        for item in st.session_state['preview_data']:
            viz = DocumentStructureVisualizer(item['doc'])
            st.header(f"📄 {item['filename']}")
            
            c1, c2 = st.columns([1, 2])
            with c1:
                st.subheader("Hierarchy")
                for h in viz.get_document_hierarchy():
                    st.write(f"{'—' * h['level']} {h['text']} (p. {h['page']})")
            with c2:
                st.subheader("Tables")
                for t in viz.get_tables_info():
                    st.caption(f"Table {t['table_number']} (p. {t['page']})")
                    st.dataframe(t['dataframe'])
    else: st.info("Upload documents to see insights.")