"""
TerraQore Research Tool
Provides web search capabilities for agents to research topics.
Uses the ddgs (DuckDuckGo Search) package for free, no-API-key web searching.
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import time

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """A single search result."""
    title: str
    url: str
    snippet: str
    source: str = "duckduckgo"


class ResearchTool:
    """Tool for conducting web research."""
    
    def __init__(self, max_results: int = 5, timeout: int = 10):
        """Initialize research tool.
        
        Args:
            max_results: Maximum number of results to return.
            timeout: Timeout for search requests in seconds.
        """
        self.max_results = max_results
        self.timeout = timeout
        self._check_dependencies()
    
    def _check_dependencies(self):
        """Check if required dependencies are available."""
        try:
            from ddgs import DDGS
            self._ddgs_available = True
            logger.info("ddgs search provider available")
        except ImportError:
            self._ddgs_available = False
            logger.warning("ddgs package not installed. Run: pip install ddgs")
    
    def search(self, query: str, max_results: Optional[int] = None) -> List[SearchResult]:
        """Search the web for information.
        
        Args:
            query: Search query.
            max_results: Override default max results.
            
        Returns:
            List of SearchResult objects.
        """
        if not self._ddgs_available:
            logger.error("ddgs search not available. Install with: pip install ddgs")
            return []
        
        max_res = max_results or self.max_results
        results = []
        
        try:
            from ddgs import DDGS
            
            logger.info(f"Searching for: {query}")
            
            with DDGS() as ddgs:
                search_results = ddgs.text(query, max_results=max_res)
                
                for result in search_results:
                    results.append(SearchResult(
                        title=result.get('title', ''),
                        url=result.get('href', ''),
                        snippet=result.get('body', ''),
                        source='duckduckgo'
                    ))
            
            logger.info(f"Found {len(results)} results")
            
        except Exception as e:
            logger.error(f"Search error: {e}")
        
        return results
    
    def search_multiple(self, queries: List[str]) -> Dict[str, List[SearchResult]]:
        """Search multiple queries.
        
        Args:
            queries: List of search queries.
            
        Returns:
            Dictionary mapping query to results.
        """
        results = {}
        
        for query in queries:
            results[query] = self.search(query)
            # Small delay to be respectful to search provider
            time.sleep(1)
        
        return results
    
    def format_results(self, results: List[SearchResult], max_snippet_length: int = 150) -> str:
        """Format search results into a readable string.
        
        Args:
            results: List of search results.
            max_snippet_length: Maximum length of snippet to include.
            
        Returns:
            Formatted string of results.
        """
        if not results:
            return "No results found."
        
        formatted = []
        for i, result in enumerate(results, 1):
            snippet = result.snippet[:max_snippet_length]
            if len(result.snippet) > max_snippet_length:
                snippet += "..."
            
            formatted.append(
                f"{i}. {result.title}\n"
                f"   URL: {result.url}\n"
                f"   {snippet}\n"
            )
        
        return "\n".join(formatted)
    
    def get_trending_topics(self, domain: str = "agentic AI") -> List[str]:
        """Get trending topics in a domain.
        
        Args:
            domain: Domain to search for trends.
            
        Returns:
            List of trending topic strings.
        """
        # Search for recent trends
        queries = [
            f"latest {domain} trends 2024",
            f"new developments in {domain}",
            f"recent {domain} breakthroughs"
        ]
        
        all_results = self.search_multiple(queries)
        
        # Extract key topics from results (simplified - could use NLP)
        topics = set()
        for results in all_results.values():
            for result in results:
                # Simple extraction: look for capitalized phrases
                words = result.title.split()
                for i in range(len(words) - 1):
                    if words[i][0].isupper() and words[i+1][0].isupper():
                        topics.add(f"{words[i]} {words[i+1]}")
        
        return list(topics)[:10]  # Top 10 topics
    
    def research_topic(self, topic: str, aspects: Optional[List[str]] = None) -> Dict[str, Any]:
        """Conduct comprehensive research on a topic.
        
        Args:
            topic: Main topic to research.
            aspects: Specific aspects to investigate.
            
        Returns:
            Dictionary with research findings.
        """
        research = {
            "topic": topic,
            "overview": [],
            "aspects": {},
            "related_topics": []
        }
        
        # Main overview search
        overview_results = self.search(f"{topic} overview")
        research["overview"] = overview_results
        
        # Search specific aspects if provided
        if aspects:
            for aspect in aspects:
                query = f"{topic} {aspect}"
                research["aspects"][aspect] = self.search(query, max_results=3)
        
        # Find related topics
        related_query = f"{topic} related topics"
        related_results = self.search(related_query, max_results=5)
        research["related_topics"] = related_results
        
        return research


# Singleton instance
_research_tool: Optional[ResearchTool] = None


def get_research_tool() -> ResearchTool:
    """Get or create the global research tool.
    
    Returns:
        ResearchTool singleton instance.
    """
    global _research_tool
    if _research_tool is None:
        _research_tool = ResearchTool()
    return _research_tool