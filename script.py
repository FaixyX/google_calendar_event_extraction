import os, pickle, json, html, re
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from datetime import datetime, timedelta

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

    # Set default time range (current week - Monday to Sunday)
    if not time_min:
        from datetime import datetime, timedelta
        # Use local time instead of UTC to avoid timezone issues
        today = datetime.now()
        print(f"📅 Week calculation:")
        print(f"   Today (local): {today.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   Today weekday: {today.weekday()} (0=Monday, 6=Sunday)")
        
        # Get Monday of current week (weekday 0 = Monday)
        monday = today - timedelta(days=today.weekday())
        time_min = monday.replace(hour=0, minute=0, second=0, microsecond=0).isoformat() + 'Z'
        print(f"   Monday (local): {monday.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   Time range start: {time_min}")
    if not time_max:
        from datetime import datetime, timedelta
        today = datetime.now()
        # Get Sunday of current week (weekday 6 = Sunday)
        sunday = today + timedelta(days=6-today.weekday())
        time_max = sunday.replace(hour=23, minute=59, second=59, microsecond=999999).isoformat() + 'Z'
        print(f"   Sunday (local): {sunday.strftime('%Y-%m-%d %H:%M:%S')}")
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
    
    # Parse the week boundries for comparison
    week_start = time_min.split('T')[0]
    week_end = time_max.split('T')[0]
    print(f"   Week range: {week_start} to {week_end}")
    
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
        
        # Parse start and end dates
        from datetime import datetime
        start_date = event_data['start'].split('T')[0] if 'T' in event_data['start'] else event_data['start']
        end_date = event_data['end'].split('T')[0] if 'T' in event_data['end'] else event_data['end']
        
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

# Example usage
if __name__ == '__main__':
    # Replace with your calendar name
    calendar_name = GOOGLE_CALENDAR_NAME  # Change this to your calendar's name
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