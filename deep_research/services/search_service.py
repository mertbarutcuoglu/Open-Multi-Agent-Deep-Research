"""
Search service for the Deep Search Agent system.

This module provides a clean interface to the Tavily API for search and extract operations,
handling authentication, error management, and response formatting.
"""

import os
from typing import Dict, List, Any, Optional

from tavily import TavilyClient


class SearchError(Exception):
    """Exception raised when search operations fail."""

    pass


class SearchService:
    """
    Wrapper for Tavily API client with error handling and response formatting.

    This class provides a clean interface to Tavily's search and extract APIs,
    handling authentication, parameter validation, and error management.
    """

    def __init__(self) -> None:
        """
        Initialize the service

        Raises:
            TavilyClientError: If API key is not provided or invalid
        """
        self.api_key = os.getenv("TAVILY_API_KEY")
        if not self.api_key:
            raise SearchError(
                "Tavily API key not provided and TAVILY_API_KEY env var not set"
            )

        try:
            self.client = TavilyClient(api_key=self.api_key)
        except Exception as e:
            raise SearchError(f"Failed to initialize Tavily client: {e}")

    def search(
        self,
        query: str,
        search_depth: str = "basic",
        max_results: int = 5,
        include_answer: bool = False,
        include_raw_content: bool = False,
        include_domains: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Perform a web search using Tavily API.

        Args:
            query: Search query string
            search_depth: Search depth ('basic' or 'advanced')
            max_results: Maximum number of results (1-20)
            include_answer: Whether to include AI-generated answer
            include_raw_content: Whether to include full raw content
            include_domains: List of domains to include
            exclude_domains: List of domains to exclude

        Returns:
            Dictionary containing search results and metadata

        Raises:
            TavilyClientError: If the search fails
        """
        try:
            # Prepare search parameters
            search_params = {
                "query": query,
                "search_depth": search_depth,
                "max_results": max_results,
                "include_answer": include_answer,
                "include_raw_content": include_raw_content,
            }

            # Add domain filters if provided
            if include_domains:
                search_params["include_domains"] = include_domains
            if exclude_domains:
                search_params["exclude_domains"] = exclude_domains

            # Perform the search
            results = self.client.search(**search_params)

            # Ensure we have a consistent response format
            if not isinstance(results, dict):
                raise SearchError("Invalid response format from Tavily API")

            return results

        except Exception as e:
            if isinstance(e, SearchError):
                raise
            raise SearchError(f"Search failed for query '{query}': {e}")

    def extract(
        self,
        urls: List[str],
        include_images: bool = False,
        extract_depth: str = "basic",
        format: str = "markdown",
    ) -> Dict[str, Any]:
        """
        Extract content from specific URLs using Tavily API.

        Args:
            urls: List of URLs to extract content from
            include_images: Whether to include images
            extract_depth: Extraction depth ('basic' or 'advanced')
            format: Output format ('markdown' or 'text')

        Returns:
            Dictionary containing extraction results

        Raises:
            TavilyClientError: If the extraction fails
        """
        try:
            # Prepare extraction parameters
            extract_params = {
                "urls": urls,
                "include_images": include_images,
                "extract_depth": extract_depth,
                "format": format,
            }

            # Perform the extraction
            results = self.client.extract(**extract_params)

            # Ensure we have a consistent response format
            if not isinstance(results, dict):
                raise SearchError("Invalid response format from Tavily API")

            return results

        except Exception as e:
            if isinstance(e, SearchError):
                raise
            raise SearchError(f"Extract failed for URLs {urls}: {e}")

    def format_search_results(self, results: Dict[str, Any]) -> str:
        """
        Format search results into a readable string for agents.

        Args:
            results: Raw search results from Tavily API

        Returns:
            Formatted search results as a string
        """
        if not results.get("results"):
            return "No relevant search results found."

        formatted_parts = []

        # Add direct answer if available
        if results.get("answer"):
            formatted_parts.append(f"**Direct Answer:** {results['answer']}\n")

        # Add search results
        formatted_parts.append("**Search Results:**")

        for i, result in enumerate(results["results"], 1):
            result_text = f"{i}. **{result.get('title', 'No title')}**\n"
            result_text += f"   URL: {result.get('url', 'No URL')}\n"

            # Add content if available
            content = result.get("content", "")
            if content:
                # Truncate very long content for readability
                if len(content) > 800:
                    content = content[:800] + "..."
                result_text += f"   Content: {content}\n"

            formatted_parts.append(result_text)

        return "\n".join(formatted_parts)

    def format_extract_results(self, results: Dict[str, Any]) -> str:
        """
        Format extraction results into a readable string for agents.

        Args:
            results: Raw extraction results from Tavily API

        Returns:
            Formatted extraction results as a string
        """
        if not results.get("results"):
            return "No content could be extracted from the provided URLs."

        formatted_parts = []

        # Process successful extractions
        for i, result in enumerate(results["results"], 1):
            url = result.get("url", "Unknown URL")
            content = result.get("raw_content", "")

            formatted_parts.append(f"**Content from {url}:**")

            if content:
                # Truncate extremely long content
                if len(content) > 5000:
                    content = (
                        content[:5000] + "\n\n[Content truncated due to length...]"
                    )
                formatted_parts.append(content)
            else:
                formatted_parts.append("No content available.")

            formatted_parts.append("")  # Add spacing between results

        # Add information about failed extractions
        if results.get("failed_results"):
            formatted_parts.append("**Failed Extractions:**")
            for failed in results["failed_results"]:
                url = failed.get("url", "Unknown URL")
                error = failed.get("error", "Unknown error")
                formatted_parts.append(f"- {url}: {error}")

        return "\n".join(formatted_parts)

    def get_client_info(self) -> Dict[str, Any]:
        """
        Get information about the Tavily client configuration.

        Returns:
            Dictionary with client information
        """
        return {
            "service": "Tavily API",
            "api_configured": bool(self.api_key),
            "client_initialized": self.client is not None,
        }
