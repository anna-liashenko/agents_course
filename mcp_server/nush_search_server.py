"""
MCP Server for НУШ curriculum search and PDF processing.
Implements Model Context Protocol for curriculum standards retrieval.
"""

import asyncio
from typing import Any, Dict, List, Optional
from mcp import Server, Resource
from mcp.server.stdio import stdio_server
from tools.web_search_tool import WebSearchTool
from tools.pdf_processor_tool import PDFProcessorTool
from mcp_server.search_cache import SearchCache
from utils.observability import get_logger

logger = get_logger(__name__)


class NUSHSearchServer:
    """
    MCP Server for НУШ curriculum standards search and retrieval.
    Exposes web search and PDF processing capabilities via MCP protocol.
    """
    
    def __init__(self):
        self.search_tool = WebSearchTool()
        self.pdf_tool = PDFProcessorTool()
        self.cache = SearchCache()
        self.logger = logger
        self.server = Server("nush-curriculum-server")
        
        # Register resources and tools
        self._register_resources()
        self._register_tools()
    
    def _register_resources(self):
        """Register MCP resources."""
        
        @self.server.list_resources()
        async def list_resources() -> List[Resource]:
            """List available curriculum resources."""
            return [
                Resource(
                    uri="nush://curriculum/search",
                    name="НУШ Curriculum Search",
                    description="Search for НУШ curriculum standards by grade and subject",
                    mimeType="application/json"
                ),
                Resource(
                    uri="nush://curriculum/pdf",
                    name="НУШ PDF Processor",
                    description="Download and process curriculum PDF documents",
                    mimeType="application/json"
                )
            ]
        
        @self.server.read_resource()
        async def read_resource(uri: str) -> str:
            """Read a curriculum resource."""
            if uri.startswith("nush://curriculum/"):
                # Return cached data if available
                cached = self.cache.get_cache_info()
                return str(cached)
            
            return "Resource not found"
    
    def _register_tools(self):
        """Register MCP tools."""
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[Any]:
            """Handle tool calls."""
            
            self.logger.info("mcp_tool_called", tool=name, args=arguments)
            
            if name == "search_curriculum":
                return await self._search_curriculum(arguments)
            
            elif name == "process_pdf":
                return await self._process_pdf(arguments)
            
            elif name == "get_standards":
                return await self._get_standards(arguments)
            
            else:
                return [{"error": f"Unknown tool: {name}"}]
    
    async def _search_curriculum(self, args: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Search for curriculum documents.
        
        Args:
            args: {"grade": int, "subject": str}
            
        Returns:
            List of search results
        """
        grade = args.get("grade")
        subject = args.get("subject")
        
        if not grade or not subject:
            return [{"error": "Missing grade or subject"}]
        
        # Check cache first
        cached = self.cache.get_cached_search(grade, subject)
        if cached:
            self.logger.info("search_cache_hit", grade=grade, subject=subject)
            return cached
        
        # Perform search
        results = self.search_tool.search_nush_standards(grade, subject)
        
        # Cache results
        self.cache.cache_search_results(grade, subject, results)
        
        return results
    
    async def _process_pdf(self, args: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Download and process a PDF document.
        
        Args:
            args: {"url": str}
            
        Returns:
            Processed PDF data
        """
        url = args.get("url")
        
        if not url:
            return [{"error": "Missing URL"}]
        
        # Check cache first
        cached = self.cache.get_cached_pdf(url)
        if cached:
            self.logger.info("pdf_cache_hit", url=url)
            return [cached]
        
        # Process PDF
        result = self.pdf_tool.process_pdf(url)
        
        # Cache result
        if result['success']:
            self.cache.cache_pdf_result(url, result)
        
        return [result]
    
    async def _get_standards(self, args: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get curriculum standards (combined search + PDF processing).
        
        Args:
            args: {"grade": int, "subject": str}
            
        Returns:
            Fully processed curriculum standards
        """
        grade = args.get("grade")
        subject = args.get("subject")
        
        if not grade or not subject:
            return [{"error": "Missing grade or subject"}]
        
        # Search for documents
        search_results = await self._search_curriculum(args)
        
        if not search_results or "error" in search_results[0]:
            return search_results
        
        # Process the first PDF found
        for result in search_results:
            if result.get('type') == 'pdf':
                pdf_result = await self._process_pdf({"url": result['url']})
                if pdf_result and pdf_result[0].get('success'):
                    return [{
                        'grade': grade,
                        'subject': subject,
                        'document': result,
                        'standards': pdf_result[0].get('standards', {}),
                        'text_preview': pdf_result[0].get('text', '')[:500]
                    }]
        
        return [{"error": "No valid PDF documents found"}]
    
    async def run(self):
        """Run the MCP server."""
        self.logger.info("mcp_server_starting")
        
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )


async def main():
    """Main entry point for MCP server."""
    server = NUSHSearchServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
