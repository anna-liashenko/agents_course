"""
Web search tool for finding НУШ curriculum standards on Ministry of Education website.
Custom ADK tool implementation.
"""

from typing import Dict, List, Any, Optional
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, quote
from utils.observability import get_logger

logger = get_logger(__name__)


class WebSearchTool:
    """
    Custom tool for searching НУШ curriculum standards on mon.gov.ua.
    Implements ADK tool pattern for web searches.
    """
    
    def __init__(self):
        self.base_url = "https://mon.gov.ua"
        self.search_url = "https://mon.gov.ua/ua/search"
        self.logger = logger
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def search_nush_standards(
        self,
        grade: int,
        subject: str,
        search_type: str = "curriculum"
    ) -> Dict[str, Any]:
        """
        Search for НУШ curriculum standards.
        
        Args:
            grade: Grade level (1-11)
            subject: Subject name in Ukrainian (e.g., "Математика", "Українська мова")
            search_type: Type of search ("curriculum", "standards", "program")
            
        Returns:
            Dictionary with success status, results list, and error message
        """
        # Construct search query in Ukrainian
        query = f"НУШ {grade} клас {subject} стандарти"
        
        self.logger.info(
            "web_search_started",
            query=query,
            grade=grade,
            subject=subject
        )
        
        try:
            # Perform search using Google with site restriction
            # (Ministry website's internal search can be unreliable)
            google_search_url = f"https://www.google.com/search?q=site:mon.gov.ua+{quote(query)}+filetype:pdf"
            
            response = self.session.get(google_search_url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            results = []
            
            # Parse Google search results
            for result in soup.select('div.g'):
                link_elem = result.select_one('a')
                title_elem = result.select_one('h3')
                desc_elem = result.select_one('div.VwiC3b')
                
                if link_elem and title_elem:
                    url = link_elem.get('href', '')
                    
                    # Filter for PDF links from mon.gov.ua
                    if 'mon.gov.ua' in url and url.endswith('.pdf'):
                        results.append({
                            'title': title_elem.get_text(strip=True),
                            'url': url,
                            'description': desc_elem.get_text(strip=True) if desc_elem else '',
                            'type': 'pdf'
                        })
            
            # Fallback: Search for well-known НУШ curriculum pages
            if not results:
                fallback_results = self._fallback_search(grade, subject)
                results.extend(fallback_results)
            
            self.logger.info(
                "web_search_completed",
                query=query,
                results_count=len(results)
            )
            
            return {
                'success': True,
                'results': results[:5],  # Return top 5 results
                'count': len(results)
            }
            
        except Exception as e:
            self.logger.error(
                "web_search_failed",
                query=query,
                error=str(e)
            )
            # Return fallback results even on error
            fallback_results = self._fallback_search(grade, subject)
            return {
                'success': False,
                'results': fallback_results,
                'error': str(e),
                'count': len(fallback_results)
            }
    
    def _fallback_search(self, grade: int, subject: str) -> List[Dict[str, Any]]:
        """
        Fallback method using known НУШ curriculum URLs.
        
        Args:
            grade: Grade level
            subject: Subject name
            
        Returns:
            List of known curriculum document URLs
        """
        # Known НУШ curriculum document patterns
        # These are example URLs - you'd update these with actual Ministry URLs
        known_patterns = [
            {
                'title': f'Типова освітня програма НУШ для {grade} класу',
                'url': f'https://mon.gov.ua/storage/app/media/zagalna%20serednya/programy-1-4-klas/2019/11/1-2-dodatki.pdf',
                'description': f'Типова освітня програма для закладів загальної середньої освіти',
                'type': 'pdf'
            },
            {
                'title': f'Навчальна програма з {subject} для {grade} класу',
                'url': f'https://mon.gov.ua/ua/osvita/zagalna-serednya-osvita/navchalni-programi',
                'description': f'Навчальні програми для {grade} класу',
                'type': 'page'
            }
        ]
        
        self.logger.info("using_fallback_search", grade=grade, subject=subject)
        return known_patterns
    
    def extract_pdf_links(self, page_url: str) -> List[str]:
        """
        Extract PDF download links from a webpage.
        
        Args:
            page_url: URL of the page to scrape
            
        Returns:
            List of PDF URLs found on the page
        """
        try:
            response = self.session.get(page_url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            pdf_links = []
            
            # Find all links ending in .pdf
            for link in soup.find_all('a', href=True):
                href = link['href']
                if href.endswith('.pdf'):
                    full_url = urljoin(page_url, href)
                    pdf_links.append(full_url)
            
            self.logger.info(
                "pdf_links_extracted",
                page_url=page_url,
                count=len(pdf_links)
            )
            
            return pdf_links
            
        except Exception as e:
            self.logger.error(
                "pdf_extraction_failed",
                page_url=page_url,
                error=str(e)
            )
            return []


# Tool function interface for ADK
def search_nush_curriculum(grade: int, subject: str) -> List[Dict[str, Any]]:
    """
    ADK tool function for searching НУШ curriculum standards.
    
    Args:
        grade: Grade level (1-11)
        subject: Subject name in Ukrainian
        
    Returns:
        List of curriculum document results
    """
    tool = WebSearchTool()
    return tool.search_nush_standards(grade, subject)
