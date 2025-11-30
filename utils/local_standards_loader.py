"""
Local standards loader - reads curriculum documents from local standards/ folder.
Supports both PDF and DOCX formats.
"""

import os
from typing import Dict, List, Any, Optional
from pathlib import Path
from utils.observability import get_logger

logger = get_logger(__name__)


class LocalStandardsLoader:
    """Loads curriculum standards from local files instead of web."""
    
    def __init__(self, standards_dir: str = "standards"):
        self.standards_dir = Path(standards_dir)
        self.logger = logger
        
        # Create standards directory if it doesn't exist
        if not self.standards_dir.exists():
            self.standards_dir.mkdir(parents=True, exist_ok=True)
            self.logger.info("standards_directory_created", path=str(self.standards_dir))
    
    def find_standard_file(self, grade: int, subject: str) -> Optional[Path]:
        """
        Find a curriculum file for the given grade and subject.
        
        Args:
            grade: Grade level (1-11)
            subject: Subject name in Ukrainian
            
        Returns:
            Path to the standards file, or None if not found
        """
        # Normalize subject name for searching
        subject_lower = subject.lower()
        
        # Search patterns to try
        patterns = [
            f"*{grade}*{subject_lower}*.pdf",
            f"*{grade}*{subject_lower}*.docx",
            f"*{subject_lower}*{grade}*.pdf",
            f"*{subject_lower}*{grade}*.docx",
            f"*клас*{grade}*.pdf",
            f"*клас*{grade}*.docx",
        ]
        
        # Try each pattern
        for pattern in patterns:
            matches = list(self.standards_dir.glob(pattern))
            if matches:
                self.logger.info(
                    "standard_file_found",
                    grade=grade,
                    subject=subject,
                    file=str(matches[0])
                )
                return matches[0]
        
        # If no exact match, return any file that might be relevant
        all_files = list(self.standards_dir.glob("*.pdf")) + list(self.standards_dir.glob("*.docx"))
        
        for file in all_files:
            filename_lower = file.name.lower()
            # Check if filename contains grade or subject keywords
            if (str(grade) in filename_lower or 
                any(keyword in filename_lower for keyword in subject_lower.split())):
                self.logger.info(
                    "standard_file_matched",
                    grade=grade,
                    subject=subject,
                    file=str(file)
                )
                return file
        
        self.logger.warning(
            "no_standard_file_found",
            grade=grade,
            subject=subject,
            available_files=len(all_files)
        )
        return None
    
    def list_available_files(self) -> List[Dict[str, Any]]:
        """List all available standards files."""
        files = []
        
        for file_path in self.standards_dir.iterdir():
            if file_path.suffix.lower() in ['.pdf', '.docx']:
                files.append({
                    'filename': file_path.name,
                    'path': str(file_path),
                    'type': file_path.suffix[1:].upper(),
                    'size': file_path.stat().st_size
                })
        
        self.logger.info("available_standards_listed", count=len(files))
        return files
    
    def extract_text_from_docx(self, file_path: Path) -> str:
        """
        Extract text from DOCX file.
        
        Args:
            file_path: Path to DOCX file
            
        Returns:
            Extracted text
        """
        try:
            from docx import Document
            
            doc = Document(file_path)
            text_parts = []
            
            for para in doc.paragraphs:
                if para.text.strip():
                    text_parts.append(para.text)
            
            text = '\n'.join(text_parts)
            
            self.logger.info(
                "docx_text_extracted",
                file=str(file_path),
                length=len(text)
            )
            
            return text
            
        except ImportError:
            self.logger.error("python_docx_not_installed")
            return f"Error: python-docx not installed. Run: pip install python-docx"
        except Exception as e:
            self.logger.error("docx_extraction_failed", error=str(e))
            return f"Error extracting DOCX: {str(e)}"
    
    def load_standard(self, grade: int, subject: str) -> Dict[str, Any]:
        """
        Load curriculum standard from local file.
        
        Args:
            grade: Grade level
            subject: Subject name
            
        Returns:
            Dictionary with success status and extracted content
        """
        # Find the file
        file_path = self.find_standard_file(grade, subject)
        
        if not file_path:
            return {
                'success': False,
                'message': f'Стандарти для {grade} класу ({subject}) не знайдено в локальних файлах',
                'available_files': self.list_available_files()
            }
        
        # Extract text based on file type
        if file_path.suffix.lower() == '.pdf':
            from tools.pdf_processor_tool import PDFProcessorTool
            
            pdf_tool = PDFProcessorTool()
            result = pdf_tool.process_pdf_file(str(file_path))
            
            if result.get('success'):
                return {
                    'success': True,
                    'source': 'local_pdf',
                    'file': str(file_path),
                    'filename': file_path.name,
                    'text': result.get('text', ''),
                    'standards': result.get('standards', {})
                }
            else:
                return {
                    'success': False,
                    'message': f"Помилка читання PDF: {result.get('error')}",
                    'file': str(file_path)
                }
        
        elif file_path.suffix.lower() == '.docx':
            text = self.extract_text_from_docx(file_path)
            
            if text and not text.startswith('Error'):
                return {
                    'success': True,
                    'source': 'local_docx',
                    'file': str(file_path),
                    'filename': file_path.name,
                    'text': text,
                    'standards': {}  # DOCX parsing can be added later
                }
            else:
                return {
                    'success': False,
                    'message': text if text.startswith('Error') else 'Помилка читання DOCX',
                    'file': str(file_path)
                }
        
        else:
            return {
                'success': False,
                'message': f'Непідтримуваний формат файлу: {file_path.suffix}'
            }
