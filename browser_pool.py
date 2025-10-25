"""
Persistent browser pool to maintain Uber sessions across requests.
Keeps browsers alive to avoid session expiration.
"""

import asyncio
from typing import Optional, Dict, Any
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

class BrowserPool:
    """Manages persistent browser contexts for each user."""
    
    def __init__(self):
        self.browsers: Dict[str, Dict[str, Any]] = {}
        self.playwright = None
    
    async def initialize(self):
        """Initialize Playwright."""
        if not self.playwright:
            self.playwright = await async_playwright().start()
    
    async def get_or_create_browser(self, uid: str, session_data: Dict[str, Any]) -> Page:
        """Get existing browser or create new one for user."""
        await self.initialize()
        
        # If browser exists and is still alive, reuse it
        if uid in self.browsers:
            browser_info = self.browsers[uid]
            try:
                # Test if browser is still alive
                if browser_info["page"] and not browser_info["page"].is_closed():
                    print(f"Reusing existing browser for {uid}")
                    return browser_info["page"]
            except:
                pass
        
        # Create new browser
        print(f"Creating new browser for {uid}")
        browser = await self.playwright.chromium.launch(headless=True)
        context = await browser.new_context(storage_state=session_data)
        page = await context.new_page()
        
        # Store browser info
        self.browsers[uid] = {
            "browser": browser,
            "context": context,
            "page": page,
            "created_at": asyncio.get_event_loop().time(),
        }
        
        return page
    
    async def close_browser(self, uid: str):
        """Close browser for user."""
        if uid in self.browsers:
            browser_info = self.browsers[uid]
            try:
                await browser_info["context"].close()
                await browser_info["browser"].close()
            except:
                pass
            del self.browsers[uid]
    
    async def cleanup_old_browsers(self, max_age_seconds: int = 3600):
        """Close browsers older than max_age_seconds."""
        current_time = asyncio.get_event_loop().time()
        uids_to_close = []
        
        for uid, browser_info in self.browsers.items():
            age = current_time - browser_info["created_at"]
            if age > max_age_seconds:
                uids_to_close.append(uid)
        
        for uid in uids_to_close:
            print(f"Closing old browser for {uid}")
            await self.close_browser(uid)
    
    async def shutdown(self):
        """Close all browsers and Playwright."""
        for uid in list(self.browsers.keys()):
            await self.close_browser(uid)
        
        if self.playwright:
            await self.playwright.stop()

# Global browser pool
browser_pool = BrowserPool()
