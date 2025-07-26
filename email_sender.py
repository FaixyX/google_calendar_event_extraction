import os
import smtplib
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Email configuration from environment variables
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
EMAIL_USER = os.getenv('EMAIL_USER', '')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD', '')
RECIPIENT_EMAIL = os.getenv('RECIPIENT_EMAIL', '')

def format_calendar_data_for_email(calendar_data):
    """
    Format the calendar data into a readable HTML email format.
    
    :param calendar_data: Dictionary containing categorized events
    :return: HTML formatted string for email
    """
    if not calendar_data:
        return "<p>No calendar events found for the specified time period.</p>"
    
    html_content = """
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .date-section { margin-bottom: 30px; border-left: 4px solid #4285f4; padding-left: 15px; }
            .date-header { font-size: 18px; font-weight: bold; color: #333; margin-bottom: 10px; }
            .event { margin-bottom: 15px; padding: 10px; background-color: #f8f9fa; border-radius: 5px; }
            .event-header { font-weight: bold; font-size: 16px; margin-bottom: 8px; line-height: 1.3; }
            .event-title-link { color: #1a73e8; text-decoration: none; }
            .event-title-link:hover { text-decoration: underline; }
            .event-title-text { color: #333; }
            .event-location { color: #666; font-size: 14px; margin-bottom: 5px; }
            .event-description { color: #333; font-size: 14px; line-height: 1.4; }
            .event-booking { margin-top: 8px; padding-top: 8px; border-top: 1px solid #e0e0e0; }
            .event-booking a { display: inline-block; background-color: #1a73e8; color: white; padding: 6px 12px; text-decoration: none; border-radius: 4px; margin-right: 8px; margin-bottom: 4px; font-size: 13px; }
            .event-booking a:hover { background-color: #1557b0; }
            .ongoing-badge { background-color: #ff9800; color: white; padding: 2px 6px; border-radius: 3px; font-size: 12px; margin-left: 10px; }
            .one-time-badge { background-color: #4caf50; color: white; padding: 2px 6px; border-radius: 3px; font-size: 12px; margin-left: 10px; }
            .no-events { color: #666; font-style: italic; }
        </style>
    </head>
    <body>
        <h1>📅 Calendar Summary</h1>
        <p>Here's your calendar summary for the current week:</p>
    """
    
    # Sort dates
    sorted_dates = sorted(calendar_data.keys())
    
    for date in sorted_dates:
        date_obj = datetime.strptime(date, '%Y-%m-%d')
        formatted_date = date_obj.strftime('%A, %B %d, %Y')
        
        html_content += f'<div class="date-section">'
        html_content += f'<div class="date-header">{formatted_date}</div>'
        
        ongoing_events = calendar_data[date]['ongoing_events']
        one_time_events = calendar_data[date]['one_time_events']
        
        # Add ongoing events
        if ongoing_events:
            html_content += '<h3>🔄 Ongoing Events</h3>'
            for event in ongoing_events:
                html_content += format_single_event(event, is_ongoing=True)
        
        # Add one-time events
        if one_time_events:
            html_content += '<h3>📅 One-time Events</h3>'
            for event in one_time_events:
                html_content += format_single_event(event, is_ongoing=False)
        
        # If no events for this date
        if not ongoing_events and not one_time_events:
            html_content += '<p class="no-events">No events scheduled for this date.</p>'
        
        html_content += '</div>'
    
    html_content += """
        <hr>
        <p><em>This email was automatically generated from your Google Calendar data.</em></p>
    </body>
    </html>
    """
    
    return html_content

def format_single_event(event, is_ongoing=False):
    """
    Format a single event for HTML display.
    
    :param event: Event dictionary
    :param is_ongoing: Boolean indicating if this is an ongoing event
    :return: HTML string for the event
    """
    # Format date and time
    start_date = format_date(event['start'])
    start_time = format_time(event['start'])
    
    # Create title with optional link
    title = event["summary"]
    location = event.get('location', '')
    
    # Format: Title [Location] Date Time
    if location:
        title_with_location = f"{title} [{location}]"
    else:
        title_with_location = title
    
    if event.get('booking_links'):
        # Use the first booking link for the title
        booking_link = event['booking_links'][0]
        title_html = f'<a href="{booking_link}" target="_blank" class="event-title-link">{title_with_location}</a>'
    else:
        title_html = f'<span class="event-title-text">{title_with_location}</span>'
    
    html = f'<div class="event">'
    html += f'<div class="event-header">{title_html} {start_date} {start_time}</div>'
    html += '</div>'
    return html

def format_date(time_str):
    """
    Format date string for display.
    
    :param time_str: ISO format time string
    :return: Formatted date string
    """
    if 'T' in time_str:
        # Has time component
        try:
            dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
            return dt.strftime('%B %d')
        except:
            return time_str.split('T')[0]
    else:
        # Date only
        try:
            dt = datetime.strptime(time_str, '%Y-%m-%d')
            return dt.strftime('%B %d')
        except:
            return time_str

def format_time(time_str):
    """
    Format time string for display.
    
    :param time_str: ISO format time string
    :return: Formatted time string
    """
    if 'T' in time_str:
        # Has time component
        try:
            dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
            return dt.strftime('%I:%M%p')
        except:
            return time_str
    else:
        # Date only
        try:
            dt = datetime.strptime(time_str, '%Y-%m-%d')
            return dt.strftime('%B %d, %Y')
        except:
            return time_str

def send_calendar_email(calendar_data, subject=None):
    """
    Send calendar data via email.
    
    :param calendar_data: Dictionary containing categorized events
    :param subject: Email subject (optional)
    :return: Boolean indicating success/failure
    """
    if not all([EMAIL_USER, EMAIL_PASSWORD, RECIPIENT_EMAIL]):
        print("❌ Email configuration missing. Please set EMAIL_USER, EMAIL_PASSWORD, and RECIPIENT_EMAIL in your .env file.")
        return False
    
    if not subject:
        subject = f"📅 Calendar Summary - Week of {datetime.now().strftime('%B %d, %Y')}"
    
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = EMAIL_USER
        msg['To'] = RECIPIENT_EMAIL
        
        # Create HTML content
        html_content = format_calendar_data_for_email(calendar_data)
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)
        
        # Create plain text version
        text_content = create_plain_text_version(calendar_data)
        text_part = MIMEText(text_content, 'plain')
        msg.attach(text_part)
        
        # Send email
        print(f"📧 Sending email to {RECIPIENT_EMAIL}...")
        
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASSWORD)
            server.send_message(msg)
        
        print("✅ Email sent successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send email: {str(e)}")
        return False

def create_plain_text_version(calendar_data):
    """
    Create a plain text version of the calendar data for email fallback.
    
    :param calendar_data: Dictionary containing categorized events
    :return: Plain text string
    """
    if not calendar_data:
        return "No calendar events found for the specified time period."
    
    text_content = "CALENDAR SUMMARY\n"
    text_content += "=" * 50 + "\n\n"
    
    sorted_dates = sorted(calendar_data.keys())
    
    for date in sorted_dates:
        date_obj = datetime.strptime(date, '%Y-%m-%d')
        formatted_date = date_obj.strftime('%A, %B %d, %Y')
        
        text_content += f"{formatted_date}\n"
        text_content += "-" * len(formatted_date) + "\n"
        
        ongoing_events = calendar_data[date]['ongoing_events']
        one_time_events = calendar_data[date]['one_time_events']
        
        if ongoing_events:
            text_content += "\nOngoing Events:\n"
            for event in ongoing_events:
                text_content += format_event_text(event, is_ongoing=True)
        
        if one_time_events:
            text_content += "\nOne-time Events:\n"
            for event in one_time_events:
                text_content += format_event_text(event, is_ongoing=False)
        
        if not ongoing_events and not one_time_events:
            text_content += "No events scheduled for this date.\n"
        
        text_content += "\n"
    
    text_content += "\nThis email was automatically generated from your Google Calendar data."
    return text_content

def format_event_text(event, is_ongoing=False):
    """
    Format a single event for plain text display.
    
    :param event: Event dictionary
    :param is_ongoing: Boolean indicating if this is an ongoing event
    :return: Plain text string for the event
    """
    start_date = format_date(event['start'])
    start_time = format_time(event['start'])
    
    # Format: Title [Location] Date Time
    title = event['summary']
    location = event.get('location', '')
    
    if location:
        title_with_location = f"{title} [{location}]"
    else:
        title_with_location = title
    
    if event.get('booking_links'):
        booking_link = event['booking_links'][0]
        text = f"  {title_with_location} {start_date} {start_time} (Booking: {booking_link})\n"
    else:
        text = f"  {title_with_location} {start_date} {start_time}\n"
    
    text += "\n"
    return text 