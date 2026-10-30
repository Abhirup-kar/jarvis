import aiohttp
import re
from urllib.parse import quote_plus
from tools.base_tool import BaseTool
from tools.registry import tool_registry

@tool_registry.register
class WebBrowserTool(BaseTool):
    name = "web_search"
    description = "Searches the web and extracts summary content from search results."
    risk_level = "medium"

    def get_parameters_schema(self):
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query keywords"}
            },
            "required": ["query"]
        }

    async def execute(self, query: str, **kwargs):
        # Try playwright first if available
        try:
            from playwright.async_api import async_playwright
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                await page.goto(f"https://duckduckgo.com/html/?q={quote_plus(query)}")
                snippet = await page.locator(".result__snippet").first.text_content()
                await browser.close()
                if snippet:
                    return {"query": query, "summary": snippet.strip(), "engine": "playwright"}
        except Exception:
            pass

        # Fallback to direct HTTP search
        url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=6) as resp:
                    if resp.status == 200:
                        html = await resp.text()
                        # Extract first snippet text
                        matches = re.findall(r'<a class="result__snippet[^>]*>(.*?)</a>', html, re.DOTALL)
                        if matches:
                            clean_text = re.sub(r'<[^>]+>', '', matches[0]).strip()
                            return {"query": query, "summary": clean_text, "engine": "http_fallback"}
                    return {"query": query, "summary": f"Search completed for '{query}'.", "status": "no_snippets"}
        except Exception as e:
            return {"query": query, "summary": f"Could not perform web search: {str(e)}", "error": True}