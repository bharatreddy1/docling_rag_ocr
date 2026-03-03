import os
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter

class VectorStoreManager:
    def __init__(self, persist_directory: str = "./chroma_db"):
        self.persist_directory = persist_directory
        # Automatically detects OPENAI_API_KEY from .env
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        
        self.vectorstore = Chroma(
            collection_name="delhi_police_docs",
            embedding_function=self.embeddings,
            persist_directory=self.persist_directory
        )

    def file_exists(self, file_hash: str) -> bool:
        results = self.vectorstore.get(where={"file_hash": file_hash}, limit=1)
        return len(results['ids']) > 0

    def add_documents(self, documents, file_hash: str):
        chunks = self.text_splitter.split_documents(documents)
        for chunk in chunks:
            chunk.metadata["file_hash"] = file_hash
        self.vectorstore.add_documents(chunks)

    def get_all_filenames(self):
        data = self.vectorstore.get(include=['metadatas'])
        if not data['metadatas']: return []
        return sorted(list({m['filename'] for m in data['metadatas'] if 'filename' in m}))