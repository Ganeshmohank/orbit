# Changelog

All notable changes to the Omi Uber App project are documented here.

## [1.0.0] - 2025-10-25

### Added
- ✅ **Sliding Window Segment Collection** - Collects voice segments for 5 seconds of silence before processing
  - Each new segment restarts the 5-second countdown
  - Monitoring task checks every 500ms for silence
  - Non-blocking webhook returns immediately
  
- ✅ **LLM-Powered Destination Extraction** - Uses OpenAI GPT-3.5-turbo
  - Corrects spelling mistakes (SJS → SJSU, Cal Trane → Cal Train)
  - Rejects generic terms (Current Location, Office, Home, My Place, Work)
  - Extracts both start and end locations
  - Handles single location bookings
  
- ✅ **Comprehensive Screenshot Capture** - Captures at each booking step
  - 01_pickup_filled - After entering pickup location
  - 02_pickup_selected - After selecting pickup suggestion
  - 03_dropoff_filled - After entering dropoff location
  - 04_dropoff_selected - After selecting dropoff suggestion
  - 05_ride_details - Ride details page
  - 06_ride_options - Available ride options
  - 07_ride_selected - After selecting a ride
  - 08_booking_confirmation - After clicking request button
  - Stored in `/snapshots/{uid}/` folder
  
- ✅ **Login Button Detection** - Warns if login button detected
  - Indicates authentication issue
  - Provides re-authentication link
  - Helps debug session problems
  
- ✅ **User Authentication Validation** - Checks before processing
  - Validates user is authenticated before booking
  - Clears bucket if user not authenticated
  - Prevents unauthorized bookings
  
- ✅ **Default User Support** - All requests use `default_user`
  - Simplifies testing and deployment
  - Ignores uid in request body
  - Consistent user experience

### Changed
- Updated webhook to use sliding window instead of fixed timer
- Improved LLM prompt for better location extraction
- Enhanced error messages with actionable guidance
- Refactored segment collection logic for clarity

### Fixed
- Fixed function signature mismatch in `_process_bucket_delayed`
- Fixed bucket clearing logic to prevent double processing
- Fixed screenshot path handling for user-specific folders

### Documentation
- Created comprehensive README.md with all features
- Created TECHNICAL.md with architecture and implementation details
- Created CHANGELOG.md (this file)
- Added API endpoint documentation
- Added segment collection flow diagrams
- Added timing behavior examples

## [0.9.0] - 2025-10-24

### Added
- Initial browser automation with Playwright
- Session persistence with cookies
- Basic destination extraction
- Screenshot capture at booking completion

### Known Issues
- Segment collection not working correctly
- Timer logic causing missed segments
- No multi-segment support

## Roadmap

### v1.1.0 (Planned)
- [ ] Database integration (PostgreSQL)
- [ ] User preferences (ride type, payment method)
- [ ] Ride history and analytics
- [ ] WebSocket for real-time updates
- [ ] Multi-language support

### v1.2.0 (Planned)
- [ ] Cancellation support
- [ ] Estimated price display
- [ ] Driver rating display
- [ ] Favorite locations
- [ ] Scheduled rides

### v2.0.0 (Future)
- [ ] Mobile app (React Native)
- [ ] Multiple ride services (Lyft, etc.)
- [ ] AI-powered route optimization
- [ ] Voice feedback and notifications
- [ ] Integration with calendar

---

**Current Version:** 1.0.0  
**Last Updated:** October 25, 2025
