"""
Document Parser for various file formats
"""

import logging
import os
from typing import Dict, Any

logger = logging.getLogger(__name__)

class DocumentParser:
    """Simple document parser for common file formats"""
    
    def __init__(self):
        self.supported_extensions = {'.txt', '.md', '.csv'}
        
        # Try to import additional libraries
        try:
            import PyPDF2
            self.supported_extensions.add('.pdf')
            self._pdf_available = True
        except ImportError:
            self._pdf_available = False
            logger.warning("PyPDF2 not available - PDF parsing disabled")
        
        try:
            import docx
            self.supported_extensions.add('.docx')
            self._docx_available = True
        except ImportError:
            self._docx_available = False
            logger.warning("python-docx not available - DOCX parsing disabled")
    
    def is_supported_file(self, file_path: str) -> bool:
        """Check if file type is supported"""
        _, ext = os.path.splitext(file_path.lower())
        return ext in self.supported_extensions
    
    def parse_document(self, file_path: str) -> Dict[str, Any]:
        """Parse document and extract text content"""
        try:
            if not os.path.exists(file_path):
                return {"status": "error", "error": "File not found"}
            
            _, ext = os.path.splitext(file_path.lower())
            
            if ext == '.txt' or ext == '.md':
                return self._parse_text_file(file_path)
            elif ext == '.csv':
                return self._parse_csv_file(file_path)
            elif ext == '.pdf' and self._pdf_available:
                return self._parse_pdf_file(file_path)
            elif ext == '.docx' and self._docx_available:
                return self._parse_docx_file(file_path)
            else:
                return {"status": "error", "error": f"Unsupported file type: {ext}"}
        
        except Exception as e:
            logger.error(f"Error parsing document {file_path}: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    def _parse_text_file(self, file_path: str) -> Dict[str, Any]:
        """Parse plain text or markdown file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            return {
                "status": "success",
                "content": content,
                "metadata": {
                    "file_type": "text",
                    "file_size": os.path.getsize(file_path),
                    "character_count": len(content)
                }
            }
        except Exception as e:
            return {"status": "error", "error": f"Error reading text file: {str(e)}"}
    
    def _parse_csv_file(self, file_path: str) -> Dict[str, Any]:
        """Parse CSV file"""
        try:
            import csv
            content_lines = []
            
            with open(file_path, 'r', encoding='utf-8') as file:
                csv_reader = csv.reader(file)
                for row in csv_reader:
                    content_lines.append(', '.join(row))
            
            content = '\n'.join(content_lines)
            
            return {
                "status": "success",
                "content": content,
                "metadata": {
                    "file_type": "csv",
                    "file_size": os.path.getsize(file_path),
                    "row_count": len(content_lines)
                }
            }
        except Exception as e:
            return {"status": "error", "error": f"Error reading CSV file: {str(e)}"}
    
    def _parse_pdf_file(self, file_path: str) -> Dict[str, Any]:
        """Parse PDF file"""
        try:
            import PyPDF2
            content_pages = []
            
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    content_pages.append(page.extract_text())
            
            content = '\n\n'.join(content_pages)
            
            return {
                "status": "success",
                "content": content,
                "metadata": {
                    "file_type": "pdf",
                    "file_size": os.path.getsize(file_path),
                    "page_count": len(content_pages)
                }
            }
        except Exception as e:
            return {"status": "error", "error": f"Error reading PDF file: {str(e)}"}
    
    def _parse_docx_file(self, file_path: str) -> Dict[str, Any]:
        """Parse DOCX file"""
        try:
            import docx
            doc = docx.Document(file_path)
            content_paragraphs = []
            
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    content_paragraphs.append(paragraph.text)
            
            content = '\n\n'.join(content_paragraphs)
            
            return {
                "status": "success",
                "content": content,
                "metadata": {
                    "file_type": "docx",
                    "file_size": os.path.getsize(file_path),
                    "paragraph_count": len(content_paragraphs)
                }
            }
        except Exception as e:
            return {"status": "error", "error": f"Error reading DOCX file: {str(e)}"}