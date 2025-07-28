import os, pickle, json, html, re
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from datetime import datetime, timedelta, timezone
import argparse
import calendar

from email_sender import send_calendar_email

from dotenv import load_dotenv
# Load environment variables from .env file
load_dotenv()

# Get configuration from environment variables
GOOGLE_CALENDAR_NAME = os.getenv('GOOGLE_CALENDAR_NAME', '')
GOOGLE_CREDENTIALS_FILE = os.getenv('GOOGLE_CREDENTIALS_FILE', '')
GOOGLE_TOKEN_FILE = os.getenv('GOOGLE_TOKEN_FILE', '')
OUTPUT_JSON_FILE = os.getenv('OUTPUT_JSON_FILE', '')
MAX_RESULTS = int(os.getenv('MAX_RESULTS', '100000'))
ENABLE_HTML_CLEANING = os.getenv('ENABLE_HTML_CLEANING', 'false').lower() == 'true'

# Define the scopes required
SCOPES = [os.getenv('GOOGLE_CALENDAR_SCOPES', 'https://www.googleapis.com/auth/calendar.readonly')]

# Pacific Time timezone (Los Angeles)
PACIFIC_TZ = timezone(timedelta(hours=-8))  # PST (UTC-8)
PACIFIC_DT_TZ = timezone(timedelta(hours=-7))  # PDT (UTC-7) - Daylight Saving Time

def get_pacific_time():
    """
    Get current time in Pacific Time (Los Angeles).
    Automatically handles Daylight Saving Time.
    """
    utc_now = datetime.now(timezone.utc)
    # Pacific Time is UTC-8 (PST) or UTC-7 (PDT)
    # We'll use UTC-7 as default (PDT) since most of the year is daylight saving
    pacific_now = utc_now.astimezone(PACIFIC_DT_TZ)
    return pacific_now

def parse_datetime_with_timezone(date_time_str):
    """
    Parse datetime string with timezone information.
    Handles both date-only and datetime strings.
    Converts all times to Pacific Time.
    
    :param date_time_str: String like "2025-07-21" or "2025-07-21T10:30:00-07:00"
    :return: datetime object in Pacific Time
    """
    if 'T' in date_time_str:
        # Has time component, parse with timezone
        try:
            # Parse the datetime string
            dt = datetime.fromisoformat(date_time_str.replace('Z', '+00:00'))
            # Convert to Pacific Time
            if dt.tzinfo is None:
                # If no timezone info, assume it's in Pacific Time
                dt = dt.replace(tzinfo=PACIFIC_DT_TZ)
            else:
                # Convert to Pacific Time
                dt = dt.astimezone(PACIFIC_DT_TZ)
            return dt
        except ValueError as e:
            print(f"Warning: Could not parse datetime '{date_time_str}': {e}")
            return None
    else:
        # Date only, assume start of day in Pacific Time
        try:
            dt = datetime.strptime(date_time_str, '%Y-%m-%d')
            dt = dt.replace(tzinfo=PACIFIC_DT_TZ)
            return dt
        except ValueError as e:
            print(f"Warning: Could not parse date '{date_time_str}': {e}")
            return None

def clean_html_text(text):
    """Remove HTML tags and decode HTML entities from text."""
    if not text:
        return ''
    
    # Decode HTML entities (like &amp;, &lt;, etc.)
    text = html.unescape(text)
    
    # Simple HTML tag removal (you can use a more robust library like BeautifulSoup if needed)
    import re
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def extract_booking_links(description):
    """
    Extract booking links from event description.
    Looks for common booking link patterns and button text.
    
    :param description: Event description text
    :return: List of booking links found
    """
    if not description:
        return []
    
    booking_links = []
    
    # Common patterns for booking links
    patterns = [
        # Look for "Book Now" or similar text followed by URLs
        r'(?:book\s+now|book\s+here|reserve\s+now|book\s+appointment|schedule\s+now)[\s:]*([^\s\n]+)',
        # Look for URLs that might be booking links
        r'(https?://[^\s\n]+(?:book|reserve|appointment|schedule)[^\s\n]*)',
        # Look for common booking platforms
        r'(https?://[^\s\n]*(?:calendly|acuity|square|booksy|mindbody|zenoti)[^\s\n]*)',
        # Look for button-style links in HTML
        r'<a[^>]*href=["\']([^"\']+)["\'][^>]*>(?:[^<]*book[^<]*|[^<]*reserve[^<]*|[^<]*schedule[^<]*)</a>',
        # Look for any URL that contains booking-related keywords
        r'(https?://[^\s\n]*(?:booking|appointment|reservation|schedule)[^\s\n]*)'
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, description, re.IGNORECASE)
        for match in matches:
            # Clean up the URL
            url = match.strip()
            if url.startswith('http'):
                booking_links.append(url)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_links = []
    for link in booking_links:
        if link not in seen:
            seen.add(link)
            unique_links.append(link)
    
    return unique_links

def authenticate_google_calendar():
    """Authenticates and returns a Google Calendar API service instance."""
    creds = None

    # Token file stores the user's access and refresh tokens
    if os.path.exists(GOOGLE_TOKEN_FILE):
        with open(GOOGLE_TOKEN_FILE, 'rb') as token:
            creds = pickle.load(token)

    # If no valid credentials, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                GOOGLE_CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save credentials for next run
        with open(GOOGLE_TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)

    service = build('calendar', 'v3', credentials=creds)
    return service

def get_calendar_id_by_name(service, calendar_name):
    """Finds the calendar ID by its name."""
    calendar_list = service.calendarList().list().execute()
    for calendar_item in calendar_list['items']:
        if calendar_item['summary'] == calendar_name:
            return calendar_item['id']
    return None

def get_events_from_calendar(calendar_name, time_min=None, time_max=None, max_results=None):
    """
    Fetch events from a specific calendar by name.
    
    :param calendar_name: Name of the Calendar (e.g., "Work")
    :param time_min: Start of the time range (ISO format string)
    :param time_max: End of the time range (ISO format string)
    :param max_results: Max number of events to return (None for all events)
    """
    service = authenticate_google_calendar()

    # Get calendar ID by name
    calendar_id = get_calendar_id_by_name(service, calendar_name)
    if not calendar_id:
        print(f"Calendar with name '{calendar_name}' not found.")
        return

    # Set default time range (current week - Monday to Sunday) in Pacific Time
    if not time_min:
        # Use Pacific Time for all calculations
        today = get_pacific_time()
        print(f"📅 Week calculation (Pacific Time):")
        print(f"   Today (Pacific): {today.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print(f"   Today weekday: {today.weekday()} (0=Monday, 6=Sunday)")
        
        # Get Monday of current week (weekday 0 = Monday)
        monday = today - timedelta(days=today.weekday())
        monday = monday.replace(hour=0, minute=0, second=0, microsecond=0)
        time_min = monday.isoformat()
        print(f"   Monday (Pacific): {monday.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print(f"   Time range start: {time_min}")
    if not time_max:
        today = get_pacific_time()
        # Get Sunday of current week (weekday 6 = Sunday)
        sunday = today + timedelta(days=6-today.weekday())
        sunday = sunday.replace(hour=23, minute=59, second=59, microsecond=999999)
        time_max = sunday.isoformat()
        print(f"   Sunday (Pacific): {sunday.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print(f"   Time range end: {time_max}")
        print(f"   Total days in range: 7 days (Monday to Sunday)")
        print()

    # Fetch events
    params = {
        'calendarId': calendar_id,
        'timeMin': time_min,
        'timeMax': time_max,
        'singleEvents': True,
        'orderBy': 'startTime'
    }
    
    # Add maxResults parameter only if specified
    if max_results:
        params['maxResults'] = max_results
    elif MAX_RESULTS:
        params['maxResults'] = MAX_RESULTS
    
    events_result = service.events().list(**params).execute()

    events = events_result.get('items', [])
    if not events:
        print("No upcoming events found in this calendar.")
        return []
    
    # Extract the required fields from events and categorize by date
    categorized_events = {}
    
    print(f"📊 Processing events within week range...")
    
    # Parse the week boundaries for comparison using Pacific Time
    week_start_dt = parse_datetime_with_timezone(time_min.split('T')[0])
    week_end_dt = parse_datetime_with_timezone(time_max.split('T')[0])
    
    if week_start_dt and week_end_dt:
        week_start = week_start_dt.strftime('%Y-%m-%d')
        week_end = week_end_dt.strftime('%Y-%m-%d')
        print(f"   Week range: {week_start} to {week_end}")
    else:
        print("   Warning: Could not parse week boundaries")
        return []
    
    events_in_range = 0
    for event in events:
        print(event)
        
        # Get the original description for link extraction
        original_description = event.get('description', '')
        
        # Clean the description for display
        cleaned_description = clean_html_text(original_description) if ENABLE_HTML_CLEANING else original_description
        
        # Extract booking links from the original description
        booking_links = extract_booking_links(original_description)
        
        event_data = {
            'summary': event.get('summary', ''), # This is the title of the event
            'location': event.get('location', ''), # This is the location of the event
            'description': cleaned_description, # This is the text description of the event
            'booking_links': booking_links, # This is the list of booking links found
            'start': event['start'].get('dateTime', event['start'].get('date')), # This is the start time of the event
            'end': event['end'].get('dateTime', event['end'].get('date')) # This is the end time of the event
        }
        
        # Parse start and end dates with proper timezone handling (Pacific Time)
        start_dt = parse_datetime_with_timezone(event_data['start'])
        end_dt = parse_datetime_with_timezone(event_data['end'])
        
        if not start_dt or not end_dt:
            print(f"   ⚠️  Skipping: {event_data['summary']} (could not parse dates)")
            continue
        
        start_date = start_dt.strftime('%Y-%m-%d')
        end_date = end_dt.strftime('%Y-%m-%d')
        
        # Check if event overlaps with the week range
        # Include events that: start_date <= week_end AND end_date >= week_start
        if end_date < week_start or start_date > week_end:
            print(f"   ⏭️  Skipping: {event_data['summary']} (outside week range: {start_date} to {end_date})")
            continue
            
        events_in_range += 1
        
        # Determine if it's an ongoing event (spans multiple days)
        is_ongoing = start_date != end_date
        
        print(f"   ✅ Event: {event_data['summary']}")
        print(f"      Start: {event_data['start']} → Date: {start_date}")
        print(f"      End: {event_data['end']} → Date: {end_date}")
        print(f"      Type: {'Ongoing' if is_ongoing else 'One-time'}")
        
        # For ongoing events, add to every day they overlap with the week
        if is_ongoing:
            # Calculate the actual overlap dates within our week range
            
            overlap_start = max(start_date, week_start)
            overlap_end = min(end_date, week_end)
            
            # Convert to datetime for iteration
            current_date = datetime.strptime(overlap_start, '%Y-%m-%d')
            end_datetime = datetime.strptime(overlap_end, '%Y-%m-%d')
            
            print(f"      Overlap with week: {overlap_start} to {overlap_end}")
            
            # Add event to each day it overlaps with the week
            while current_date <= end_datetime:
                date_key = current_date.strftime('%Y-%m-%d')
                
                # Initialize date entry if it doesn't exist
                if date_key not in categorized_events:
                    categorized_events[date_key] = {
                        'ongoing_events': [],
                        'one_time_events': []
                    }
                
                categorized_events[date_key]['ongoing_events'].append(event_data)
                current_date += timedelta(days=1)
        else:
            # For one-time events, add only to the start date
            if start_date not in categorized_events:
                categorized_events[start_date] = {
                    'ongoing_events': [],
                    'one_time_events': []
                }
            
            categorized_events[start_date]['one_time_events'].append(event_data)
    
    print(f"   📈 Processed {events_in_range} events within week range (out of {len(events)} total)")
    
    # Save to JSON file
    with open(OUTPUT_JSON_FILE, 'w', encoding='utf-8') as f:
        json.dump(categorized_events, f, indent=4, ensure_ascii=False)
    
    print(f"Extracted and categorized {len(events)} events by date and saved to {OUTPUT_JSON_FILE}")
    return categorized_events

def parse_custom_date_range(date_input):
    """
    Parse custom date range input and return time_min and time_max in ISO format.
    
    Supports various input formats:
    - "2024-08-01 to 2024-08-04" (specific date range)
    - "august 2024" (whole month)
    - "aug 2024" (whole month)
    - "2024-08" (whole month)
    - "next week" (next week from today)
    - "this month" (current month)
    - "next month" (next month)
    
    :param date_input: String describing the date range
    :return: tuple (time_min, time_max) in ISO format
    """
    date_input = date_input.lower().strip()
    
    # Pacific Time timezone for calculations
    pacific_tz = timezone(timedelta(hours=-7))  # PDT
    
    # Handle "to" format: "2024-08-01 to 2024-08-04"
    if " to " in date_input:
        try:
            start_date_str, end_date_str = date_input.split(" to ")
            start_date = datetime.strptime(start_date_str.strip(), '%Y-%m-%d')
            end_date = datetime.strptime(end_date_str.strip(), '%Y-%m-%d')
            
            # Set start time to beginning of start date
            time_min = start_date.replace(tzinfo=pacific_tz).isoformat()
            # Set end time to end of end date
            time_max = end_date.replace(hour=23, minute=59, second=59, microsecond=999999, tzinfo=pacific_tz).isoformat()
            
            return time_min, time_max
        except ValueError as e:
            print(f"❌ Error parsing date range '{date_input}': {e}")
            return None, None
    
    # Handle month formats: "august 2024", "aug 2024", "2024-08"
    month_keywords = ['january', 'jan', 'february', 'feb', 'march', 'mar', 'april', 'apr', 
                     'may', 'june', 'jul', 'july', 'august', 'aug', 'september', 'sep', 
                     'october', 'oct', 'november', 'nov', 'december', 'dec']
    
    # Check if input contains month keywords
    if any(keyword in date_input for keyword in month_keywords) or (len(date_input.split()) == 2 and date_input.split()[1].isdigit()):
        try:
            # Parse month and year
            if len(date_input.split()) == 2:
                month_str, year_str = date_input.split()
                year = int(year_str)
                
                # Handle month names
                if month_str in month_keywords:
                    month_map = {
                        'january': 1, 'jan': 1, 'february': 2, 'feb': 2, 'march': 3, 'mar': 3,
                        'april': 4, 'apr': 4, 'may': 5, 'june': 6, 'jul': 7, 'july': 7,
                        'august': 8, 'aug': 8, 'september': 9, 'sep': 9, 'october': 10, 'oct': 10,
                        'november': 11, 'nov': 11, 'december': 12, 'dec': 12
                    }
                    month = month_map[month_str]
                else:
                    raise ValueError(f"Invalid month: {month_str}")
            else:
                # Handle "2024-08" format
                year, month = map(int, date_input.split('-'))
            
            # Get first and last day of month
            first_day = datetime(year, month, 1, tzinfo=pacific_tz)
            last_day = datetime(year, month, calendar.monthrange(year, month)[1], 
                              hour=23, minute=59, second=59, microsecond=999999, tzinfo=pacific_tz)
            
            return first_day.isoformat(), last_day.isoformat()
            
        except ValueError as e:
            print(f"❌ Error parsing month '{date_input}': {e}")
            return None, None
    
    # Handle relative time periods
    today = datetime.now(pacific_tz)
    
    if date_input == "next week":
        # Next Monday to Sunday
        days_until_monday = (7 - today.weekday()) % 7
        if days_until_monday == 0:  # Today is Monday
            days_until_monday = 7
        monday = today + timedelta(days=days_until_monday)
        monday = monday.replace(hour=0, minute=0, second=0, microsecond=0)
        sunday = monday + timedelta(days=6)
        sunday = sunday.replace(hour=23, minute=59, second=59, microsecond=999999)
        return monday.isoformat(), sunday.isoformat()
    
    elif date_input == "this month":
        # Current month
        first_day = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_day = today.replace(day=calendar.monthrange(today.year, today.month)[1], 
                               hour=23, minute=59, second=59, microsecond=999999)
        return first_day.isoformat(), last_day.isoformat()
    
    elif date_input == "next month":
        # Next month
        if today.month == 12:
            next_month = today.replace(year=today.year + 1, month=1, day=1, 
                                     hour=0, minute=0, second=0, microsecond=0)
        else:
            next_month = today.replace(month=today.month + 1, day=1, 
                                     hour=0, minute=0, second=0, microsecond=0)
        
        last_day = next_month.replace(day=calendar.monthrange(next_month.year, next_month.month)[1], 
                                    hour=23, minute=59, second=59, microsecond=999999)
        return next_month.isoformat(), last_day.isoformat()
    
    else:
        print(f"❌ Unrecognized date format: '{date_input}'")
        print("Supported formats:")
        print("  - '2024-08-01 to 2024-08-04' (specific date range)")
        print("  - 'august 2024' or 'aug 2024' (whole month)")
        print("  - '2024-08' (whole month)")
        print("  - 'next week' (next week from today)")
        print("  - 'this month' (current month)")
        print("  - 'next month' (next month)")
        return None, None

def get_events_for_custom_range(calendar_name, date_range=None):
    """
    Get events for a custom date range.
    
    :param calendar_name: Name of the calendar
    :param date_range: String describing the date range (optional)
    :return: Dictionary of categorized events
    """
    time_min = None
    time_max = None
    
    if date_range:
        print(f"📅 Parsing custom date range: '{date_range}'")
        time_min, time_max = parse_custom_date_range(date_range)
        
        if not time_min or not time_max:
            print("❌ Failed to parse date range. Using default (current week).")
            return get_events_from_calendar(calendar_name)
        
        print(f"✅ Date range parsed successfully:")
        print(f"   Start: {time_min}")
        print(f"   End: {time_max}")
        print()
    
    return get_events_from_calendar(calendar_name, time_min, time_max)

def get_date_range_interactively():
    """
    Ask user for date range interactively.
    
    :return: String describing the date range or None for default
    """
    print("\n" + "="*60)
    print("📅 GOOGLE CALENDAR EVENT FETCHER")
    print("="*60)
    print("Choose a date range option:")
    print()
    print("1. Current week (Monday to Sunday) - DEFAULT")
    print("2. Next week")
    print("3. This month")
    print("4. Next month")
    print("5. Custom date range (e.g., Aug 1 to Aug 4)")
    print("6. Specific month (e.g., August 2024)")
    print()
    
    while True:
        try:
            choice = input("Enter your choice (1-6, or press Enter for default): ").strip()
            
            if not choice or choice == "1":
                return None  # Default current week
                
            elif choice == "2":
                return "next week"
                
            elif choice == "3":
                return "this month"
                
            elif choice == "4":
                return "next month"
                
            elif choice == "5":
                return get_custom_date_range_input()
                
            elif choice == "6":
                return get_specific_month_input()
                
            else:
                print("❌ Invalid choice. Please enter a number between 1 and 6.")
                continue
                
        except KeyboardInterrupt:
            print("\n\n👋 Cancelled by user.")
            return None

def get_custom_date_range_input():
    """Get custom date range from user input."""
    print("\n📅 Custom Date Range")
    print("-" * 30)
    print("Enter dates in YYYY-MM-DD format")
    print("Examples: 2024-08-01, 2024-12-25")
    print()
    
    while True:
        try:
            start_date = input("Start date (YYYY-MM-DD): ").strip()
            if not start_date:
                return None
            
            end_date = input("End date (YYYY-MM-DD): ").strip()
            if not end_date:
                return None
            
            # Validate dates
            datetime.strptime(start_date, '%Y-%m-%d')
            datetime.strptime(end_date, '%Y-%m-%d')
            
            return f"{start_date} to {end_date}"
            
        except ValueError:
            print("❌ Invalid date format. Please use YYYY-MM-DD format.")
            continue
        except KeyboardInterrupt:
            print("\n\n👋 Cancelled by user.")
            return None

def get_specific_month_input():
    """Get specific month from user input."""
    print("\n📅 Specific Month")
    print("-" * 20)
    print("Enter month and year")
    print("Examples: august 2024, aug 2024, 2024-08")
    print()
    
    while True:
        try:
            month_input = input("Month and year: ").strip()
            if not month_input:
                return None
            
            # Test if the input is valid by trying to parse it
            time_min, time_max = parse_custom_date_range(month_input)
            
            if time_min and time_max:
                return month_input
            else:
                print("❌ Invalid month format. Please try again.")
                continue
                
        except KeyboardInterrupt:
            print("\n\n👋 Cancelled by user.")
            return None

# Example usage
if __name__ == '__main__':
    # Get calendar name from environment
    calendar_name = GOOGLE_CALENDAR_NAME
    
    if not calendar_name:
        print("❌ Error: GOOGLE_CALENDAR_NAME not set in environment variables.")
        print("Please set it in your .env file or environment.")
        exit(1)
    
    print(f"📅 Connected to calendar: {calendar_name}")
    
    # Ask user for date range interactively
    date_range_input = get_date_range_interactively()
    
    if date_range_input:
        print(f"\n🎯 Fetching events for: {date_range_input}")
        events = get_events_for_custom_range(calendar_name, date_range_input)
    else:
        print(f"\n📅 Fetching events for default date range (Current Week).")
        events = get_events_from_calendar(calendar_name)
    
    # Send email with calendar data
    if events:
        print("\n📧 Attempting to send email...")
        email_sent = send_calendar_email(events)
        if email_sent:
            print("🎉 Calendar data has been sent via email!")
        else:
            print("⚠️  Email sending failed, but calendar data was saved to JSON file.")
    else:
        print("📭 No events found, skipping email sending.")