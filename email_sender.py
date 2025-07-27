import os
import smtplib
import json
from email.message import EmailMessage
from datetime import datetime
from dotenv import load_dotenv
import re

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
    Format the calendar data into a readable HTML email format with tabular layout.
    
    :param calendar_data: Dictionary containing categorized events
    :return: HTML formatted string for email
    """
    if not calendar_data:
        return "<p>No calendar events found for the specified time period.</p>"
    
    # Count total events for summary
    total_events = sum(len(calendar_data[date]['ongoing_events']) + len(calendar_data[date]['one_time_events']) for date in calendar_data)
    
    # Get date range
    sorted_dates = sorted(calendar_data.keys())
    start_date = datetime.strptime(sorted_dates[0], '%Y-%m-%d')
    end_date = datetime.strptime(sorted_dates[-1], '%Y-%m-%d')
    
    # Format date range
    if start_date == end_date:
        date_range = start_date.strftime('%A, %B %d, %Y')
    else:
        date_range = f"{start_date.strftime('%B %d')} - {end_date.strftime('%B %d, %Y')}"
    
    html_content = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Calendar Summary</title>
    </head>
    <body style="font-family: Arial, sans-serif; font-size: 16px; margin: 0; padding: 0; background-color: #F5F8FA;">
        <div style="margin: auto; width: 800px; background-color: #fff;">
            <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
                <tr>
                    <td style="background-color: #4285f4; color: white; text-align: center; padding: 30px;">
                        <h1 style="margin: 0; font-size: 36px; font-weight: 900;">📅 Calendar Summary</h1>
                        <p style="margin: 10px 0 0 0; font-size: 18px;">Here's your calendar summary for {date_range}</p>
                    </td>
                </tr>
            </table>
            
            <div style="padding: 30px;">
                <!-- Summary Section -->
                <div style="background-color: #e3f2fd; border: 2px solid #2196f3; border-radius: 8px; padding: 20px; margin-bottom: 30px; text-align: center;">
                    <h3 style="margin: 0 0 10px 0; color: #1976d2; font-size: 20px;">📊 Summary</h3>
                    <p style="margin: 0; color: #333; font-size: 16px;"><strong>{total_events} total events</strong> across {len(calendar_data)} days</p>
                </div>
    '''
    
    for date in sorted_dates:
        date_obj = datetime.strptime(date, '%Y-%m-%d')
        formatted_date = date_obj.strftime('%A, %B %d, %Y')
        
        ongoing_events = calendar_data[date]['ongoing_events']
        one_time_events = calendar_data[date]['one_time_events']
        
        # Only show date if there are events
        if ongoing_events or one_time_events:
            html_content += f'''
                <!-- Date Section -->
                <div style="background-color: #4285f4; color: white; padding: 15px; font-size: 18px; font-weight: bold; border-radius: 5px 5px 0 0; margin-bottom: 0;">
                    Date: {formatted_date}
                </div>
            '''
        
        # Add ongoing events table
        if ongoing_events:
            html_content += f'''
                <div style="color: #555; font-size: 16px; font-weight: bold; margin: 20px 0 10px 0;">🔄 Ongoing Events ({len(ongoing_events)} events)</div>
                {create_events_table(ongoing_events)}
            '''
        
        # Add one-time events table
        if one_time_events:
            html_content += f'''
                <div style="color: #555; font-size: 16px; font-weight: bold; margin: 20px 0 10px 0;">📅 One-time Events ({len(one_time_events)} events)</div>
                {create_events_table(one_time_events)}
            '''
        
        # If no events for this date
        if not ongoing_events and not one_time_events:
            html_content += '''
                <div style="color: #666; font-style: italic; padding: 20px; text-align: center; background-color: #f8f9fa; border: 1px solid #ddd; border-radius: 5px;">
                    No events scheduled for this date.
                </div>
            '''
    
    html_content += '''
                <div style="text-align: center; color: #666; font-style: italic; margin-top: 40px; padding-top: 20px; border-top: 2px solid #ddd;">
                    This email was automatically generated from your Google Calendar data.
                </div>
            </div>
        </div>
    </body>
    </html>
    '''
    
    return html_content

def clean_booking_url(url):
    """
    Clean booking URL by removing HTML tags and extra characters.
    
    :param url: Raw booking URL
    :return: Cleaned URL
    """
    if not url:
        return ""
    
    # Remove HTML tags and their content
    import re
    
    # Remove HTML tags like <b>BOOK</b>, <b>Check</b>, etc.
    url = re.sub(r'<[^>]+>', '', url)
    
    # Remove common text that might be appended to URLs
    url = re.sub(r'">[^"]*$', '', url)  # Remove "> followed by any text
    url = re.sub(r'">$', '', url)       # Remove just "> at the end
    
    # Clean up any remaining quotes or special characters
    url = url.strip('"').strip("'").strip()
    
    # Ensure URL starts with http/https
    if url and not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    return url

def create_events_table(events):
    """
    Create an HTML table for events with proper borders and auto-fitted content.
    
    :param events: List of event dictionaries
    :return: HTML table string
    """
    table_html = '''
    <table style="width: 100%; border-collapse: collapse; margin-bottom: 25px; border: 2px solid #ddd; border-radius: 8px; overflow: hidden;">
        <thead>
            <tr>
                <th style="width: 50%; background-color: #4285f4; color: white; padding: 15px 12px; text-align: left; font-weight: bold; font-size: 14px; border: 1px solid #2a5aa0;">Title</th>
                <th style="width: 25%; background-color: #4285f4; color: white; padding: 15px 12px; text-align: left; font-weight: bold; font-size: 14px; border: 1px solid #2a5aa0;">Date</th>
                <th style="width: 25%; background-color: #4285f4; color: white; padding: 15px 12px; text-align: left; font-weight: bold; font-size: 14px; border: 1px solid #2a5aa0;">Start Time</th>
            </tr>
        </thead>
        <tbody>
    '''
    
    for i, event in enumerate(events):
        title = event["summary"]
        location = event.get('location', '')
        
        # Format date and time
        start_date = format_date(event['start'])
        start_time = format_time(event['start'])
        
        # Alternate row colors
        bg_color = "#f8f9fa" if i % 2 == 0 else "white"
        
        # Create title with optional link and location
        if event.get('booking_links'):
            # Clean the booking links
            cleaned_links = [clean_booking_url(link) for link in event['booking_links'] if clean_booking_url(link)]
            
            if cleaned_links:
                booking_link = cleaned_links[0]
                title_html = f'<a href="{booking_link}" target="_blank" style="color: #1a73e8; text-decoration: none; font-weight: 500;">{title}</a>'
                if len(cleaned_links) > 1:
                    title_html += f'<br><a href="{cleaned_links[1]}" target="_blank" style="display: inline-block; background-color: #1a73e8; color: white; padding: 4px 8px; text-decoration: none; border-radius: 3px; font-size: 11px; margin-top: 4px; font-weight: 500;">Additional Booking</a>'
            else:
                title_html = f'<span style="font-weight: 500; color: #333;">{title}</span>'
        else:
            title_html = f'<span style="font-weight: 500; color: #333;">{title}</span>'
        
        # Add location if available
        if location:
            title_html += f'<div style="color: #666; font-size: 12px; margin-top: 4px;">📍 {location}</div>'
        
        table_html += f'''
            <tr style="background-color: {bg_color};">
                <td style="padding: 12px; border: 1px solid #ddd; vertical-align: top; font-size: 13px; width: 50%;">{title_html}</td>
                <td style="padding: 12px; border: 1px solid #ddd; vertical-align: top; font-size: 13px; width: 25%;">{start_date}</td>
                <td style="padding: 12px; border: 1px solid #ddd; vertical-align: top; font-size: 13px; width: 25%;">{start_time}</td>
            </tr>
        '''
    
    table_html += '''
        </tbody>
    </table>
    '''
    
    return table_html

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
        # Create subject with date range
        if calendar_data:
            sorted_dates = sorted(calendar_data.keys())
            start_date = datetime.strptime(sorted_dates[0], '%Y-%m-%d')
            end_date = datetime.strptime(sorted_dates[-1], '%Y-%m-%d')
            
            if start_date == end_date:
                date_range = start_date.strftime('%b %d')
            else:
                date_range = f"{start_date.strftime('%b %d')}-{end_date.strftime('%b %d')}"
            
            subject = f"📅 Calendar Summary - {date_range}"
        else:
            subject = f"📅 Calendar Summary - {datetime.now().strftime('%b %d')}"
    
    try:
        # Create message using EmailMessage
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = EMAIL_USER
        msg['To'] = RECIPIENT_EMAIL
        
        # Create HTML content
        html_content = format_calendar_data_for_email(calendar_data)
        msg.set_content(html_content, subtype='html')
        
        # Send email
        print(f"📧 Sending email to {RECIPIENT_EMAIL}...")
        
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls() # Use STARTTLS
            server.login(EMAIL_USER, EMAIL_PASSWORD)
            server.send_message(msg)
        
        print("✅ Email sent successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send email: {str(e)}")
        return False

def create_plain_text_version(calendar_data):
    """
    Create a plain text version of the calendar data for email fallback with tabular format.
    
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
        
        text_content += f"Date: {formatted_date}\n"
        text_content += "-" * len(f"Date: {formatted_date}") + "\n\n"
        
        ongoing_events = calendar_data[date]['ongoing_events']
        one_time_events = calendar_data[date]['one_time_events']
        
        if ongoing_events:
            text_content += "🔄 Ongoing Events:\n"
            text_content += create_plain_text_table(ongoing_events)
        
        if one_time_events:
            text_content += "📅 One-time Events:\n"
            text_content += create_plain_text_table(one_time_events)
        
        if not ongoing_events and not one_time_events:
            text_content += "No events scheduled for this date.\n"
        
        text_content += "\n"
    
    text_content += "\nThis email was automatically generated from your Google Calendar data."
    return text_content

def create_plain_text_table(events):
    """
    Create a plain text table for events.
    
    :param events: List of event dictionaries
    :return: Plain text table string
    """
    if not events:
        return "No events\n\n"
    
    # Calculate column widths
    max_title_width = max(len(event.get('summary', '') + (f" [{event.get('location', '')}]" if event.get('location') else '') + 
                         (f" (Booking: {event.get('booking_links', [''])[0]})" if event.get('booking_links') else '')) for event in events)
    max_title_width = max(max_title_width, 5)  # Minimum width for "Title"
    
    # Create header
    table_text = f"{'Title':<{max_title_width}} | {'Date':<10} | {'Start Time':<12}\n"
    table_text += "-" * max_title_width + "-+-" + "-" * 10 + "-+-" + "-" * 12 + "\n"
    
    for event in events:
        title = event['summary']
        location = event.get('location', '')
        
        if location:
            title_with_location = f"{title} [{location}]"
        else:
            title_with_location = title
        
        # Add booking link if available
        if event.get('booking_links'):
            title_with_location += f" (Booking: {event['booking_links'][0]})"
        
        start_date = format_date(event['start'])
        start_time = format_time(event['start'])
        
        # Truncate title if too long
        if len(title_with_location) > max_title_width:
            title_with_location = title_with_location[:max_title_width-3] + "..."
        
        table_text += f"{title_with_location:<{max_title_width}} | {start_date:<10} | {start_time:<12}\n"
    
    table_text += "\n"
    return table_text 