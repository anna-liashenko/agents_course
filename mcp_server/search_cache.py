"""
Search cache for НУШ curriculum standards.
Caches search results and PDF content to reduce redundant operations.
"""

import json
import time
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime, timedelta
from utils.observability import get_logger

logger = get_logger(__name__)


class SearchCache:
    """
    Cache for search results and PDF content.
    Reduces redundant web searches and PDF downloads.
    """
    
    def __init__(self, cache_dir: str = "./cache", expiry_hours: int = 24):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.expiry_hours = expiry_hours
        self.logger = logger
        
        # In-memory cache
        self.search_cache: Dict[str, Dict[str, Any]] = {}
        self.pdf_cache: Dict[str, Dict[str, Any]] = {}
        
        # Load existing cache from disk
        self._load_cache()
    
    def _get_cache_key(self, grade: int, subject: str) -> str:
        """Generate cache key for search results."""
        return f"grade_{grade}_{subject.lower().replace(' ', '_')}"
    
    def _load_cache(self) -> None:
        """Load cache from disk."""
        search_cache_file = self.cache_dir / "search_cache.json"
        pdf_cache_file = self.cache_dir / "pdf_cache.json"
        
        try:
            if search_cache_file.exists():
                with open(search_cache_file, 'r', encoding='utf-8') as f:
                    self.search_cache = json.load(f)
                self.logger.info("search_cache_loaded", entries=len(self.search_cache))
            
            if pdf_cache_file.exists():
                with open(pdf_cache_file, 'r', encoding='utf-8') as f:
                    self.pdf_cache = json.load(f)
                self.logger.info("pdf_cache_loaded", entries=len(self.pdf_cache))
                
        except Exception as e:
            self.logger.error("cache_load_failed", error=str(e))
    
    def _save_cache(self) -> None:
        """Save cache to disk."""
        search_cache_file = self.cache_dir / "search_cache.json"
        pdf_cache_file = self.cache_dir / "pdf_cache.json"
        
        try:
            with open(search_cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.search_cache, f, indent=2, ensure_ascii=False)
            
            with open(pdf_cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.pdf_cache, f, indent=2, ensure_ascii=False)
            
            self.logger.debug("cache_saved")
            
        except Exception as e:
            self.logger.error("cache_save_failed", error=str(e))
    
    def _is_expired(self, timestamp: str) -> bool:
        """Check if cache entry is expired."""
        try:
            cached_time = datetime.fromisoformat(timestamp)
            expiry_time = cached_time + timedelta(hours=self.expiry_hours)
            return datetime.now() > expiry_time
        except:
            return True
    
    def cache_search_results(
        self, 
        grade: int, 
        subject: str, 
        results: List[Dict[str, Any]]
    ) -> None:
        """
        Cache search results.
        
        Args:
            grade: Grade level
            subject: Subject name
            results: Search results to cache
        """
        cache_key = self._get_cache_key(grade, subject)
        
        self.search_cache[cache_key] = {
            'grade': grade,
            'subject': subject,
            'results': results,
            'timestamp': datetime.now().isoformat()
        }
        
        self._save_cache()
        self.logger.info("search_results_cached", key=cache_key, count=len(results))
    
    def get_cached_search(self, grade: int, subject: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get cached search results.
        
        Args:
            grade: Grade level
            subject: Subject name
            
        Returns:
            Cached results if available and not expired, None otherwise
        """
        cache_key = self._get_cache_key(grade, subject)
        
        if cache_key in self.search_cache:
            entry = self.search_cache[cache_key]
            
            if not self._is_expired(entry['timestamp']):
                self.logger.info("search_cache_hit", key=cache_key)
                return entry['results']
            else:
                self.logger.info("search_cache_expired", key=cache_key)
                del self.search_cache[cache_key]
        
        return None
    
    def cache_pdf_result(self, url: str, result: Dict[str, Any]) -> None:
        """
        Cache PDF processing result.
        
        Args:
            url: PDF URL
            result: Processing result
        """
        # Don't cache the full text in JSON (too large)
        # Just cache metadata and standards
        cache_entry = {
            'url': url,
            'filepath': result.get('filepath'),
            'char_count': result.get('char_count'),
            'standards': result.get('standards', {}),
            'timestamp': datetime.now().isoformat()
        }
        
        self.pdf_cache[url] = cache_entry
        self._save_cache()
        self.logger.info("pdf_result_cached", url=url)
    
    def get_cached_pdf(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Get cached PDF result.
        
        Args:
            url: PDF URL
            
        Returns:
            Cached result if available and not expired, None otherwise
        """
        if url in self.pdf_cache:
            entry = self.pdf_cache[url]
            
            if not self._is_expired(entry['timestamp']):
                self.logger.info("pdf_cache_hit", url=url)
                
                # If PDF file still exists, read its content
                filepath = entry.get('filepath')
                if filepath and Path(filepath).exists():
                    from tools.pdf_processor_tool import PDFProcessorTool
                    pdf_tool = PDFProcessorTool()
                    text = pdf_tool.extract_text(filepath)
                    
                    return {
                        'success': True,
                        'filepath': filepath,
                        'text': text,
                        'url': url,
                        'standards': entry['standards'],
                        'char_count': len(text)
                    }
            else:
                self.logger.info("pdf_cache_expired", url=url)
                del self.pdf_cache[url]
        
        return None
    
    def get_cache_info(self) -> Dict[str, Any]:
        """
        Get information about cached data.
        
        Returns:
            Cache statistics
        """
        return {
            'search_entries': len(self.search_cache),
            'pdf_entries': len(self.pdf_cache),
            'cache_dir': str(self.cache_dir),
            'expiry_hours': self.expiry_hours
        }
    
    def clear_cache(self) -> None:
        """Clear all cached data."""
        self.search_cache = {}
        self.pdf_cache = {}
        self._save_cache()
        self.logger.info("cache_cleared")
