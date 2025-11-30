"""
PDF processor tool for downloading and extracting text from НУШ curriculum PDFs.
Custom ADK tool implementation.
"""

import os
import requests
from typing import Dict, Any, Optional
from pathlib import Path
import PyPDF2
import pdfplumber
from utils.observability import get_logger

logger = get_logger(__name__)


class PDFProcessorTool:
    """
    Custom tool for downloading and extracting text from PDF documents.
    Implements ADK tool pattern for PDF processing.
    """
    
    def __init__(self, cache_dir: str = "./cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.logger = logger
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def download_pdf(self, url: str, filename: Optional[str] = None) -> Optional[str]:
        """
        Download a PDF file from URL.
        
        Args:
            url: URL of the PDF file
            filename: Optional custom filename
            
        Returns:
            Path to downloaded file, or None if download failed
        """
        try:
            # Generate filename from URL if not provided
            if not filename:
                filename = url.split('/')[-1]
                if not filename.endswith('.pdf'):
                    filename = f"{hash(url)}.pdf"
            
            filepath = self.cache_dir / filename
            
            # Check if already cached
            if filepath.exists():
                self.logger.info("pdf_cache_hit", filepath=str(filepath))
                return str(filepath)
            
            # Download the file
            self.logger.info("pdf_download_started", url=url)
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Save to cache
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            self.logger.info(
                "pdf_downloaded",
                url=url,
                filepath=str(filepath),
                size_kb=len(response.content) / 1024
            )
            
            return str(filepath)
            
        except Exception as e:
            self.logger.error(
                "pdf_download_failed",
                url=url,
                error=str(e)
            )
            return None
    
    def extract_text_pypdf2(self, filepath: str) -> str:
        """
        Extract text from PDF using PyPDF2.
        
        Args:
            filepath: Path to PDF file
            
        Returns:
            Extracted text content
        """
        try:
            text = []
            with open(filepath, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                
                for page_num, page in enumerate(pdf_reader.pages):
                    page_text = page.extract_text()
                    if page_text:
                        text.append(page_text)
            
            full_text = '\n\n'.join(text)
            self.logger.info(
                "text_extracted_pypdf2",
                filepath=filepath,
                pages=len(text),
                chars=len(full_text)
            )
            
            return full_text
            
        except Exception as e:
            self.logger.error(
                "text_extraction_failed_pypdf2",
                filepath=filepath,
                error=str(e)
            )
            return ""
    
    def extract_text_pdfplumber(self, filepath: str) -> str:
        """
        Extract text from PDF using pdfplumber (better for complex layouts).
        
        Args:
            filepath: Path to PDF file
            
        Returns:
            Extracted text content
        """
        try:
            text = []
            with pdfplumber.open(filepath) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    page_text = page.extract_text()
                    if page_text:
                        text.append(page_text)
            
            full_text = '\n\n'.join(text)
            self.logger.info(
                "text_extracted_pdfplumber",
                filepath=filepath,
                pages=len(text),
                chars=len(full_text)
            )
            
            return full_text
            
        except Exception as e:
            self.logger.error(
                "text_extraction_failed_pdfplumber",
                filepath=filepath,
                error=str(e)
            )
            return ""
    
    def extract_text(self, filepath: str, method: str = "pdfplumber") -> str:
        """
        Extract text from PDF using specified method.
        
        Args:
            filepath: Path to PDF file
            method: Extraction method ("pdfplumber" or "pypdf2")
            
        Returns:
            Extracted text content
        """
        if method == "pdfplumber":
            text = self.extract_text_pdfplumber(filepath)
            # Fallback to PyPDF2 if pdfplumber fails
            if not text:
                text = self.extract_text_pypdf2(filepath)
        else:
            text = self.extract_text_pypdf2(filepath)
        
        return text
    
    def process_pdf_file(self, filepath: str) -> Dict[str, Any]:
        """
        Process a local PDF file (already downloaded or from local folder).
        
        Args:
            filepath: Local path to PDF file
            
        Returns:
            Dictionary with extracted text and parsed standards
        """
        if not os.path.exists(filepath):
            return {
                'success': False,
                'filepath': filepath,
                'text': '',
                'error': f'File not found: {filepath}'
            }
        
        text = self.extract_text(filepath)
        
        if text:
            standards = self.parse_curriculum_standards(text)
            
            return {
                'success': True,
                'filepath': filepath,
                'text': text,
                'char_count': len(text),
                'standards': standards
            }
        else:
            return {
                'success': False,
                'filepath': filepath,
                'text': '',
                'error': 'No text extracted from PDF'
            }
    
    def process_pdf(self, url: str) -> Dict[str, Any]:
        """
        Download and extract text from a PDF in one operation.
        
        Args:
            url: URL of the PDF document
            
        Returns:
            Dictionary with filepath and extracted text
        """
        filepath = self.download_pdf(url)
        
        if not filepath:
            return {
                'success': False,
                'filepath': None,
                'text': '',
                'error': 'Download failed'
            }
        
        text = self.extract_text(filepath)
        
        return {
            'success': True,
            'filepath': filepath,
            'text': text,
            'url': url,
            'char_count': len(text)
        }
    
    def parse_curriculum_standards(self, text: str) -> Dict[str, Any]:
        """
        Parse curriculum standards from extracted text.
        Looks for common patterns in НУШ documents.
        
        Args:
            text: Extracted text from PDF
            
        Returns:
            Structured curriculum data
        """
        standards = {
            'competencies': [],
            'learning_outcomes': [],
            'content_lines': [],
            'assessment_criteria': []
        }
        
        # Split into lines for analysis
        lines = text.split('\n')
        
        # Look for key sections (simple pattern matching)
        current_section = None
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Identify sections
            if 'компетентност' in line.lower():
                current_section = 'competencies'
            elif 'результат' in line.lower() and 'навчан' in line.lower():
                current_section = 'learning_outcomes'
            elif 'зміст' in line.lower():
                current_section = 'content_lines'
            elif 'оцінюван' in line.lower():
                current_section = 'assessment_criteria'
            
            # Add content to appropriate section
            if current_section and len(line) > 20:  # Ignore very short lines
                if line not in standards[current_section]:
                    standards[current_section].append(line)
        
        self.logger.info(
            "curriculum_parsed",
            competencies=len(standards['competencies']),
            outcomes=len(standards['learning_outcomes'])
        )
        
        return standards


# Tool function interface for ADK
def process_curriculum_pdf(url: str) -> Dict[str, Any]:
    """
    ADK tool function for downloading and processing curriculum PDFs.
    
    Args:
        url: URL of the curriculum PDF
        
    Returns:
        Processed curriculum data with extracted standards
    """
    tool = PDFProcessorTool()
    result = tool.process_pdf(url)
    
    if result['success']:
        # Parse the extracted text
        standards = tool.parse_curriculum_standards(result['text'])
        result['standards'] = standards
    
    return result
