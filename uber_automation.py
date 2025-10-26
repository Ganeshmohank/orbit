import asyncio
import os
from typing import Optional, Tuple
from playwright.async_api import async_playwright
from simple_storage import load_session, record_booking
from browser_pool import browser_pool

# Create snapshots folder if it doesn't exist
SNAPSHOTS_DIR = "snapshots"
if not os.path.exists(SNAPSHOTS_DIR):
    os.makedirs(SNAPSHOTS_DIR)
    print(f"📁 Created {SNAPSHOTS_DIR} folder")


class UberAutomation:
    """Handles automated Uber ride booking using Playwright."""
    
    async def _capture_screenshot(self, page, uid: str, step_name: str):
        """Capture and save screenshot to snapshots folder."""
        try:
            # Create user-specific folder
            user_snapshots_dir = os.path.join(SNAPSHOTS_DIR, uid)
            if not os.path.exists(user_snapshots_dir):
                os.makedirs(user_snapshots_dir)
            
            # Save screenshot with step name
            screenshot_path = os.path.join(user_snapshots_dir, f"{step_name}.png")
            await page.screenshot(path=screenshot_path)
            print(f"📸 Screenshot saved: {screenshot_path}")
            return screenshot_path
        except Exception as e:
            print(f"⚠️ Error capturing screenshot: {e}")
            return None

    async def book_ride(self, uid: str, start_location: str, end_location: str, auto_request: bool = False) -> Tuple[bool, str, Optional[str], Optional[str]]:
        """
        Book an Uber ride from start_location to end_location.
        Uses persistent browser pool to maintain sessions.
        Returns: (success, message, driver_name, eta)
        """
        try:
            # Load saved session
            session_data = load_session(uid)
            if not session_data:
                return False, "❌ No saved session. Please authenticate first.", None, None

            # Get or create persistent browser for this user
            page = await browser_pool.get_or_create_browser(uid, session_data)

            # Navigate to Uber (use desktop site, mobile is slower)
            try:
                await page.goto("https://www.uber.com", wait_until="domcontentloaded", timeout=30000)
            except Exception as e:
                print(f"Navigation error: {e}, trying reload...")
                try:
                    await page.reload(wait_until="domcontentloaded")
                except:
                    pass
            
            # Wait for page to stabilize
            await asyncio.sleep(2)

            # Handle any security challenges
            challenge_handled = await self._handle_security_challenges(page)
            if not challenge_handled:
                return False, "⚠️ Security challenge detected. Please try again.", None, None

            # Wait for the page to fully render and inputs to be visible
            print("Waiting for inputs to render...")
            try:
                await page.wait_for_selector('input[placeholder*="Where"]', timeout=10000)
            except:
                try:
                    await page.wait_for_selector('input[type="text"]', timeout=10000)
                except:
                    pass
            
            # Find and fill pickup location (start)
            pickup_input = None
            selectors = [
                'input[placeholder*="Where"]',
                'input[placeholder*="where"]',
                'input[placeholder*="pickup"]',
                'input[placeholder*="Pickup"]',
                'input[data-testid*="pickup"]',
                'input[type="text"]',
            ]
            
            for selector in selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements and len(elements) > 0:
                        # Check if element is visible
                        is_visible = await elements[0].is_visible()
                        if is_visible:
                            pickup_input = elements[0]
                            print(f"Found visible pickup input with selector: {selector}")
                            break
                except:
                    pass
            
            if not pickup_input:
                return False, "❌ Could not find pickup location input.", None, None

            # Fill pickup location using specific data-testid
            print(f"Filling pickup with: {start_location}")
            await pickup_input.click()
            await asyncio.sleep(1)  # Wait before typing
            await pickup_input.fill(start_location)
            await asyncio.sleep(2)  # Wait for autocomplete
            await self._capture_screenshot(page, uid, "01_pickup_filled")

            # Wait for autocomplete suggestions and click the list item
            print("Waiting for pickup suggestions...")
            try:
                # Wait for suggestions to appear
                await page.wait_for_selector('[role="option"]', timeout=3000)
                await asyncio.sleep(0.5)
            except:
                # Suggestions might already be visible
                pass
            
            # Try to click the first suggestion list item
            try:
                # Get all suggestion items
                suggestion_items = await page.query_selector_all('[data-tracking-name="list-item"]')
                print(f"Found {len(suggestion_items)} pickup suggestion items")
                
                if suggestion_items and len(suggestion_items) > 0:
                    # Click first item using JavaScript
                    first_item = suggestion_items[0]
                    print("Clicking first pickup suggestion item via JavaScript...")
                    await first_item.evaluate("el => el.click()")
                    await asyncio.sleep(2)
                    await self._capture_screenshot(page, uid, "02_pickup_selected")
                else:
                    print("⚠️ No suggestion items found")
            except Exception as e:
                print(f"Error clicking pickup suggestion: {e}")
                await asyncio.sleep(1)

            # Find and fill dropoff location (end)
            print("Looking for dropoff input...")
            await asyncio.sleep(1)  # Wait for dropdown to close
            
            # Look for the destination input specifically using data-testid
            dropoff_input = None
            try:
                # Try to find the destination input with specific data-testid pattern
                dropoff_input = await page.query_selector('input[data-testid*="destination.drop"]')
                if dropoff_input:
                    print("Found dropoff input via data-testid (destination.drop)")
            except:
                pass
            
            # If not found, try the generic destination selector
            if not dropoff_input:
                try:
                    dropoff_input = await page.query_selector('input[data-testid*="destination"]')
                    if dropoff_input:
                        print("Found dropoff input via data-testid (destination)")
                except:
                    pass
            
            # If still not found, try finding by looking for inputs with specific aria attributes
            if not dropoff_input:
                try:
                    all_inputs = await page.query_selector_all('input[role="combobox"]')
                    if len(all_inputs) > 1:
                        dropoff_input = all_inputs[1]
                        print(f"Found dropoff input as second combobox")
                except:
                    pass
            
            if dropoff_input:
                print(f"Filling dropoff with: {end_location}")
                # Just fill directly without clicking (like pickup)
                await dropoff_input.fill(end_location)
                await asyncio.sleep(2)  # Wait for autocomplete
                await self._capture_screenshot(page, uid, "03_dropoff_filled")

                # Wait for autocomplete and select first suggestion
                print("Waiting for dropoff suggestions...")
                try:
                    # Wait for suggestions to appear
                    await page.wait_for_selector('[role="option"]', timeout=3000)
                    await asyncio.sleep(0.5)
                except:
                    # Suggestions might already be visible
                    pass
                
                # Try to click the first suggestion list item
                try:
                    # Get all suggestion items
                    suggestion_items = await page.query_selector_all('[data-tracking-name="list-item"]')
                    print(f"Found {len(suggestion_items)} dropoff suggestion items")
                    
                    if suggestion_items and len(suggestion_items) > 0:
                        # Click first item using JavaScript
                        first_item = suggestion_items[0]
                        print("Clicking first dropoff suggestion item via JavaScript...")
                        await first_item.evaluate("el => el.click()")
                        await asyncio.sleep(2)
                        await self._capture_screenshot(page, uid, "04_dropoff_selected")
                    else:
                        print("⚠️ No dropoff suggestion items found")
                except Exception as e:
                    print(f"Error clicking dropoff suggestion: {e}")
            else:
                print("⚠️ Could not find dropoff input")

            # Wait for ride details to load
            await asyncio.sleep(2)
            await self._capture_screenshot(page, uid, "05_ride_details")

            # Look for "See prices" button
            print("Looking for 'See prices' button...")
            see_prices_btn = None
            
            # Try multiple selectors for the button
            selectors = [
                'a[aria-label="See prices"]',
                'button:has-text("See prices")',
                'a:has-text("See prices")',
                '[data-testid="button"]:has-text("See prices")',
            ]
            
            for selector in selectors:
                try:
                    btn = await page.query_selector(selector)
                    if btn and await btn.is_visible():
                        see_prices_btn = btn
                        print(f"Found 'See prices' button with selector: {selector}")
                        break
                except:
                    pass
            
            if see_prices_btn:
                print("Clicking 'See prices' button...")
                # Try JavaScript click instead of regular click (avoids overlay issues)
                try:
                    await see_prices_btn.evaluate("el => el.click()")
                    print("Clicked via JavaScript")
                except:
                    # Fallback to regular click
                    await see_prices_btn.click()
                
                # Wait for new page to load
                print("⏳ Waiting for new page to load...")
                try:
                    await page.wait_for_load_state("networkidle", timeout=15000)
                    print("✅ New page loaded")
                except:
                    print("⚠️ Page load timeout, proceeding anyway...")
                
                # Dismiss cookie consent dialog if present
                print("🍪 Checking for cookie consent dialog...")
                try:
                    # Look for "Got it" or "Opt out" button
                    cookie_btn = await page.query_selector('button:has-text("Got it")')
                    if not cookie_btn:
                        cookie_btn = await page.query_selector('button:has-text("Opt out")')
                    if not cookie_btn:
                        cookie_btn = await page.query_selector('[aria-label*="cookie"]')
                    
                    if cookie_btn and await cookie_btn.is_visible():
                        print("🍪 Dismissing cookie dialog...")
                        await cookie_btn.click()
                        await asyncio.sleep(2)
                        print("✅ Cookie dialog dismissed")
                except:
                    pass
                
                # Check if page is blank and retry if needed
                print("🔍 Checking if page loaded content...")
                try:
                    body_text = await page.text_content("body")
                    if not body_text or len(body_text.strip()) < 100:
                        print("⚠️ Page appears blank, waiting 5 seconds then reloading...")
                        await asyncio.sleep(5)
                        print("🔄 Reloading page...")
                        await page.reload(wait_until="networkidle")
                        print("✅ Page reloaded")
                except:
                    pass
                
                # Wait additional 15 seconds after page loads
                print("⏳ Waiting 15 seconds after page load...")
                await asyncio.sleep(15)
                print("✅ 15 seconds elapsed, taking screenshot")
                await self._capture_screenshot(page, uid, "06_ride_options")
                
                # Look for "Request" or available ride options
                print(f"auto_request flag: {auto_request}")
                auto_request = True
                if not auto_request:
                    # If auto_request is False, just return ready state without clicking anything
                    print("✅ Ride options loaded and ready to request!")
                    return True, f"✅ Ride ready! Pickup: {start_location} → Dropoff: {end_location}. Ready to request (auto_request=False).", None, None
                
                else :
                    # First, click on a ride option (e.g., UberX)
                    print("Looking for ride option to select...")
                    ride_option = None
                    
                    try:
                        # Look for ride option containers - try multiple selectors
                        selectors = [
                            '[data-testid*="ride_option"]',
                            '[role="button"]:has-text("UberX")',
                            'div[role="button"]:has-text("Uber")',
                            '[aria-label*="UberX"]',
                            'li:has-text("UberX")',
                            '[data-testid*="product"]',
                        ]
                        
                        ride_options = []
                        for selector in selectors:
                            try:
                                options = await page.query_selector_all(selector)
                                print(f"Selector '{selector}' found {len(options)} elements")
                                if options and len(options) > 0:
                                    ride_options = options
                                    break
                            except:
                                pass
                        
                        print(f"Found {len(ride_options)} ride options total")
                        
                        if ride_options and len(ride_options) > 0:
                            # Click the first ride option
                            first_option = ride_options[0]
                            option_text = await first_option.text_content()
                            print(f"Clicking ride option: {option_text}")
                            await first_option.evaluate("el => el.click()")
                            await asyncio.sleep(2)
                            await self._capture_screenshot(page, uid, "07_ride_selected")
                            
                            # Wait 5 seconds after clicking ride option
                            print("⏳ Waiting 5 seconds after clicking ride option...")
                            await asyncio.sleep(5)
                            print("✅ 5 seconds elapsed, taking screenshot")
                            await self._capture_screenshot(page, uid, "07a_ride_selected_5sec")
                            
                            # Wait another 10 seconds
                            print("⏳ Waiting 10 more seconds...")
                            await asyncio.sleep(10)
                            print("✅ 10 seconds elapsed, taking final screenshot before request")
                            await self._capture_screenshot(page, uid, "07b_ride_selected_15sec")
                        else:
                            print("⚠️ No ride options found, proceeding to request button")
                    except Exception as e:
                        print(f"Error selecting ride option: {e}")
                    
                    # Check for "Confirm and request" button (pickup confirmation page)
                    print("🔍 Looking for 'Confirm and request' button...")
                    confirm_btn = None
                    try:
                        confirm_btn = await page.query_selector('button:has-text("Confirm and request")')
                        if confirm_btn and await confirm_btn.is_visible():
                            print("✅ Found 'Confirm and request' button")
                            await confirm_btn.click()
                            print("⏳ Waiting 5 seconds after clicking 'Confirm and request'...")
                            await asyncio.sleep(5)
                            print("✅ 5 seconds elapsed, taking screenshot")
                            await self._capture_screenshot(page, uid, "08_confirm_and_request")
                    except:
                        pass
                    
                    # Now try to find and click the request button
                    print("Looking for request button...")
                    request_btn = None
                    
                    try:
                        # Look for the request button with data-testid
                        request_btn = await page.query_selector('button[data-testid="request_trip_button"]')
                        if not request_btn:
                            # Fallback to other selectors
                            request_btn = await page.query_selector('button[aria-label*="Request"]')
                        if not request_btn:
                            request_btn = await page.query_selector('button:has-text("Request")')
                    except Exception as e:
                        print(f"Error finding request button: {e}")
                    
                    if request_btn:
                        try:
                            btn_text = await request_btn.text_content()
                            print(f"🚗 Clicking Request button: {btn_text}")
                            await request_btn.evaluate("el => el.click()")
                            
                            # Wait 5 seconds after clicking request button
                            print("⏳ Waiting 5 seconds after clicking request button...")
                            await asyncio.sleep(5)
                            print("✅ 5 seconds elapsed, taking screenshot")
                            await self._capture_screenshot(page, uid, "08_booking_confirmation")
                            
                            print("✅ Ride booked successfully!")
                            return True, f"✅ Ride booked! From {start_location} to {end_location}.", None, None
                        except Exception as e:
                            print(f"Error clicking request button: {e}")
                    else:
                        print("⚠️ Request button not found")
            else:
                print("⚠️ 'See prices' button not found, but ride details are filled")
                return True, f"✅ Ride details ready: {start_location} → {end_location}. Awaiting price options.", None, None

            # Extract ride details
            driver_name, eta = await self._extract_ride_details(page)

            # Record booking
            record_booking(uid, f"{start_location} → {end_location}", driver_name, eta)

            # Keep browser alive for next request (don't close)
            message = f"🚗 Booked from {start_location} to {end_location}!"
            if driver_name:
                message += f" Driver: {driver_name}"
            if eta:
                message += f" ETA: {eta}"

            return True, message, driver_name, eta

        except asyncio.TimeoutError:
            return False, "⏱️ Request timed out. Please try again.", None, None
        except Exception as e:
            print(f"Error booking ride: {e}")
            return False, f"❌ Error: {str(e)}", None, None

    async def _check_login_required(self, page) -> bool:
        """Check if login is required (session expired)."""
        try:
            current_url = page.url
            # Only fail if explicitly on auth page
            if "auth.uber.com" in current_url.lower():
                return True
            
            return False  # Assume logged in, let booking attempt fail if needed

        except Exception as e:
            print(f"Error checking login: {e}")
            return False

    async def _handle_security_challenges(self, page) -> bool:
        """Handle Uber's security challenges like device verification."""
        try:
            # Check for common security challenge selectors
            challenge_selectors = [
                'text="Verify it\'s you"',
                'text="Verify your identity"',
                'text="Unusual activity"',
                'button:has-text("Verify")',
            ]

            for selector in challenge_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        # For now, we'll just wait and hope it passes
                        await asyncio.sleep(3)
                        break
                except:
                    pass

            return True

        except Exception as e:
            print(f"Error handling security challenges: {e}")
            return False

    async def _extract_ride_details(self, page) -> Tuple[Optional[str], Optional[str]]:
        """Extract driver name and ETA from confirmation page."""
        try:
            driver_name = None
            eta = None

            # Wait for confirmation page to load
            await asyncio.sleep(2)

            # Try to extract driver name
            driver_selectors = [
                'text=/Driver.*/',
                'text=/Your driver/',
                '[data-testid="driver-name"]',
            ]

            for selector in driver_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        driver_name = await element.text_content()
                        break
                except:
                    pass

            # Try to extract ETA
            eta_selectors = [
                'text=/ETA.*/',
                'text=/Arriving/',
                '[data-testid="eta"]',
            ]

            for selector in eta_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        eta = await element.text_content()
                        break
                except:
                    pass

            return driver_name, eta

        except Exception as e:
            print(f"Error extracting ride details: {e}")
            return None, None


# Global instance
uber_automation = UberAutomation()
