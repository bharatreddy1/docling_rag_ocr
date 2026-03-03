import os
import tempfile
import shutil
import gc
from typing import List, Any
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, RapidOcrOptions
from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend 
from langchain_core.documents import Document

class DocumentProcessor:
    def __init__(self):
        # Force high-resolution full-page OCR
        ocr_options = RapidOcrOptions()
        ocr_options.force_full_page_ocr = True 

        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = True
        pipeline_options.ocr_options = ocr_options
        pipeline_options.do_table_structure = True
        pipeline_options.images_scale = 2.0  # Upscale for accuracy
        pipeline_options.generate_picture_images = True # Extract images for visualizer

        self.converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(
                    pipeline_options=pipeline_options,
                    backend=PyPdfiumDocumentBackend
                )
            }
        )

    def process_uploaded_files(self, uploaded_files) -> tuple[List[Document], List[Any]]:
        documents, docling_docs = [], []
        temp_dir = tempfile.mkdtemp()
        try:
            for uploaded_file in uploaded_files:
                temp_file_path = os.path.join(temp_dir, uploaded_file.name)
                with open(temp_file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                result = self.converter.convert(temp_file_path)
                md_content = result.document.export_to_markdown()

                if md_content.strip():
                    documents.append(Document(
                        page_content=md_content,
                        metadata={"filename": uploaded_file.name, "source": uploaded_file.name}
                    ))
                    docling_docs.append({'filename': uploaded_file.name, 'doc': result.document})
        finally:
            shutil.rmtree(temp_dir)
            gc.collect()
        return documents, docling_docs