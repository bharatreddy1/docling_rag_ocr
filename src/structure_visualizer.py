"""
Document structure visualization for Docling processed documents.
"""
from typing import List, Dict, Any, Optional
import pandas as pd
from docling_core.types.doc import DoclingDocument


class DocumentStructureVisualizer:
    """Extracts and organizes document structure from Docling documents."""

    def __init__(self, docling_document: DoclingDocument):
        """
        Initialize with a Docling document.

        Args:
            docling_document: The DoclingDocument object from conversion
        """
        self.doc = docling_document

    def get_document_hierarchy(self) -> List[Dict[str, Any]]:
        hierarchy = []
        for item, level in self.doc.iterate_items():
            label = getattr(item, 'label', '')
            if 'header' in label.lower() or 'title' in label.lower():
                hierarchy.append({
                    'level': level,
                    'text': getattr(item, 'text', 'Section'),
                    'page': item.prov[0].page_no if item.prov else 1
                })
        return hierarchy

    def _infer_heading_level(self, label: str) -> int:
        """Infer heading level from label."""
        if 'title' in label.lower():
            return 1
        elif 'section' in label.lower():
            return 2
        elif 'subsection' in label.lower():
            return 3
        else:
            return 4

    def get_tables_info(self) -> List[Dict[str, Any]]:
        tables_info = []
        for i, table in enumerate(getattr(self.doc, 'tables', [])):
            try:
                # 1. Pass self.doc to fix the deprecation warning
                df = table.export_to_dataframe(doc=self.doc)
                
                # 2. Fix duplicate columns for Streamlit/PyArrow
                if not df.columns.is_unique:
                    # This renames duplicates from ['A', 'A'] to ['A', 'A.1']
                    new_cols = []
                    counts = {}
                    for col in df.columns:
                        col_str = str(col)
                        if col_str in counts:
                            counts[col_str] += 1
                            new_cols.append(f"{col_str}.{counts[col_str]}")
                        else:
                            counts[col_str] = 0
                            new_cols.append(col_str)
                    df.columns = new_cols

                tables_info.append({
                    'table_number': i + 1,
                    'dataframe': df,
                    'page': table.prov[0].page_no if table.prov else 1
                })
            except Exception as e:
                print(f"Error processing table {i}: {e}")
                continue
            return tables_info

    def get_pictures_info(self) -> List[Dict[str, Any]]:
        """
        Extract picture/image metadata and image data.

        Returns:
            List of dictionaries with picture information and PIL images
        """
        pictures_info = []

        if not hasattr(self.doc, 'pictures') or not self.doc.pictures:
            return pictures_info

        for i, pic in enumerate(self.doc.pictures, 1):
            prov = getattr(pic, 'prov', [])

            if prov:
                page_no = prov[0].page_no
                bbox = prov[0].bbox

                # Get caption if available
                caption_text = getattr(pic, 'caption_text', None)
                caption = caption_text if caption_text and not callable(caption_text) else None

                # Get PIL image if available
                pil_image = None
                try:
                    if hasattr(pic, 'image') and pic.image is not None:
                        if hasattr(pic.image, 'pil_image'):
                            pil_image = pic.image.pil_image
                except Exception as e:
                    print(f"Warning: Could not extract image {i}: {e}")

                pictures_info.append({
                    'picture_number': i,
                    'page': page_no,
                    'caption': caption,
                    'pil_image': pil_image,  # Add PIL image
                    'bounding_box': {
                        'left': bbox.l,
                        'top': bbox.t,
                        'right': bbox.r,
                        'bottom': bbox.b
                    } if bbox else None
                })

        return pictures_info

    def get_document_summary(self) -> Dict[str, Any]:
        """
        Get overall document summary statistics.

        Returns:
            Dictionary with document statistics
        """
        pages = getattr(self.doc, 'pages', {})
        texts = getattr(self.doc, 'texts', [])
        tables = getattr(self.doc, 'tables', [])
        pictures = getattr(self.doc, 'pictures', [])

        # Count different text types
        text_types = {}
        for item in texts:
            label = getattr(item, 'label', 'unknown')
            text_types[label] = text_types.get(label, 0) + 1

        return {
            'name': self.doc.name,
            'num_pages': len(pages) if pages else 0,
            'num_texts': len(texts),
            'num_tables': len(tables),
            'num_pictures': len(pictures),
            'text_types': text_types
        }

    def export_full_structure(self) -> Dict[str, Any]:
        """
        Export complete document structure.

        Returns:
            Dictionary containing all structure information
        """
        return {
            'summary': self.get_document_summary(),
            'hierarchy': self.get_document_hierarchy(),
            'tables': self.get_tables_info(),
            'pictures': self.get_pictures_info()
        }
