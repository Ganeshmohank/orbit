import asyncio
from typing import Optional, Dict, Any
from playwright.async_api import async_playwright, Page, Browser
from simple_storage import (
    load_session,
    save_session,
    update_user_status,
    load_user_data,
    set_remember_device,
    save_uber_credentials,
)

# Global state for managing active browser instances during 2FA
active_browsers: Dict[str, Dict[str, Any]] = {}


class AuthManager:
    """Handles Uber authentication with 2FA support."""

    def __init__(self):
        self.playwright = None
        self.browser = None

    async def start_login_flow(self, uid: str) -> str:
        """
        Start the login flow and return the auth status.
        Returns: "waiting_login", "waiting_2fa", "completed", or "failed"
        """
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(headless=False)

            # Store browser instance for 2FA handling
            active_browsers[uid] = {
                "browser": self.browser,
                "playwright": self.playwright,
                "page": None,
                "status": "waiting_login",
                "2fa_code": None,
            }

            page = await self.browser.new_page()
            active_browsers[uid]["page"] = page

            # Navigate to Uber login (use v2 endpoint)
            await page.goto("https://auth.uber.com/v2", wait_until="domcontentloaded", timeout=30000)
            update_user_status(uid, "waiting_login")

            # Wait for either 2FA or successful login
            result = await self._wait_for_auth_completion(uid, page)
            return result

        except Exception as e:
            print(f"Error in login flow: {e}")
            update_user_status(uid, "failed")
            await self._cleanup_browser(uid)
            return "failed"

    async def _wait_for_auth_completion(self, uid: str, page: Page) -> str:
        """Wait for login to complete or 2FA to be required."""
        timeout = 5 * 60 * 1000  # 5 minutes
        start_time = asyncio.get_event_loop().time()

        while True:
            try:
                # Check if 2FA is required
                if await self._detect_2fa_prompt(page):
                    update_user_status(uid, "waiting_2fa")
                    active_browsers[uid]["status"] = "waiting_2fa"

                    # Wait for 2FA code submission (up to 5 minutes)
                    code_submitted = await self._wait_for_2fa_code(uid)
                    if code_submitted:
                        # Continue with verification
                        result = await self._verify_2fa_and_complete(uid, page)
                        return result
                    else:
                        return "failed"

                # Check if login was successful
                if await self._check_login_success(page):
                    # Check for "Remember this device" checkbox
                    await self._handle_remember_device(page)

                    # Save session
                    session_data = await page.context.storage_state()
                    save_session(uid, session_data)
                    update_user_status(uid, "completed", authenticated=True)
                    await self._cleanup_browser(uid)
                    return "completed"

                # Check timeout
                elapsed = asyncio.get_event_loop().time() - start_time
                if elapsed > timeout / 1000:
                    update_user_status(uid, "failed")
                    await self._cleanup_browser(uid)
                    return "failed"

                await asyncio.sleep(1)

            except Exception as e:
                print(f"Error waiting for auth: {e}")
                return "failed"

    async def _detect_2fa_prompt(self, page: Page) -> bool:
        """Detect if 2FA prompt is visible."""
        selectors = [
            'input[type="tel"]',
            'input[placeholder*="code"]',
            'input[placeholder*="verification"]',
            'input[placeholder*="Code"]',
            'button:has-text("Verify")',
            'text="Enter the code"',
        ]

        for selector in selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    return True
            except:
                pass

        return False

    async def _wait_for_2fa_code(self, uid: str, timeout_seconds: int = 300) -> bool:
        """Wait for user to submit 2FA code via endpoint."""
        start_time = asyncio.get_event_loop().time()

        while True:
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > timeout_seconds:
                return False

            if active_browsers[uid].get("2fa_code"):
                return True

            await asyncio.sleep(0.5)

    async def _verify_2fa_and_complete(self, uid: str, page: Page) -> str:
        """Fill 2FA code and complete authentication."""
        try:
            code = active_browsers[uid].get("2fa_code")
            if not code:
                return "failed"

            # Find and fill the 2FA input field
            selectors = [
                'input[type="tel"]',
                'input[placeholder*="code"]',
                'input[placeholder*="verification"]',
            ]

            filled = False
            for selector in selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        await element.fill(code)
                        filled = True
                        break
                except:
                    pass

            if not filled:
                return "failed"

            # Click verify button
            verify_selectors = [
                'button:has-text("Verify")',
                'button:has-text("Submit")',
                'button:has-text("Confirm")',
            ]

            for selector in verify_selectors:
                try:
                    button = await page.query_selector(selector)
                    if button:
                        await button.click()
                        break
                except:
                    pass

            # Wait for verification to complete
            await asyncio.sleep(2)

            # Check if login was successful
            if await self._check_login_success(page):
                await self._handle_remember_device(page)
                session_data = await page.context.storage_state()
                save_session(uid, session_data)
                update_user_status(uid, "completed", authenticated=True)
                await self._cleanup_browser(uid)
                return "completed"

            return "failed"

        except Exception as e:
            print(f"Error verifying 2FA: {e}")
            return "failed"

    async def _check_login_success(self, page: Page) -> bool:
        """Check if login was successful by looking for dashboard indicators."""
        try:
            # Wait for navigation to complete
            await asyncio.sleep(1)

            # Check if we're on the main Uber page (not login page)
            current_url = page.url
            if "login" not in current_url.lower() and "auth" not in current_url.lower():
                return True

            # Check for dashboard elements
            dashboard_selectors = [
                'text="Where to?"',
                'text="Request a ride"',
                'button:has-text("Request")',
            ]

            for selector in dashboard_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        return True
                except:
                    pass

            return False

        except Exception as e:
            print(f"Error checking login success: {e}")
            return False

    async def _handle_remember_device(self, page: Page):
        """Check and click 'Remember this device' checkbox if available."""
        try:
            selectors = [
                'input[type="checkbox"]',
                'text="Remember this device"',
                'text="Stay signed in"',
            ]

            for selector in selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        await element.click()
                        break
                except:
                    pass
        except Exception as e:
            print(f"Error handling remember device: {e}")

    async def submit_2fa_code(self, uid: str, code: str) -> bool:
        """Submit 2FA code from user."""
        if uid in active_browsers:
            active_browsers[uid]["2fa_code"] = code
            return True
        return False

    async def validate_session(self, uid: str) -> bool:
        """Validate if user's session is still active."""
        try:
            session_data = load_session(uid)
            if not session_data:
                return False

            self.playwright = await async_playwright().start()
            browser = await self.playwright.chromium.launch(headless=True)

            context = await browser.new_context(storage_state=session_data)
            page = await context.new_page()

            # Try to access Uber homepage
            await page.goto("https://m.uber.com", wait_until="networkidle", timeout=10000)

            # Check if we're logged in
            current_url = page.url
            is_logged_in = "login" not in current_url.lower()

            await browser.close()
            await self.playwright.stop()

            return is_logged_in

        except Exception as e:
            print(f"Error validating session: {e}")
            return False

    async def _cleanup_browser(self, uid: str):
        """Clean up browser instance."""
        try:
            if uid in active_browsers:
                browser_data = active_browsers[uid]
                if browser_data.get("page"):
                    await browser_data["page"].close()
                if browser_data.get("browser"):
                    await browser_data["browser"].close()
                if browser_data.get("playwright"):
                    await browser_data["playwright"].stop()
                del active_browsers[uid]
        except Exception as e:
            print(f"Error cleaning up browser: {e}")


# Global instance
auth_manager = AuthManager()
