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
    Format the calendar data into a clean, professional email format showing one-time events and ongoing events summary.
    
    :param calendar_data: Dictionary containing categorized events
    :return: HTML formatted string for email
    """
    if not calendar_data:
        return "<p>No calendar events found for the specified time period.</p>"
    
    # Get one-time events
    all_one_time_events = []
    all_ongoing_events = []
    
    for date in calendar_data:
        all_one_time_events.extend(calendar_data[date]['one_time_events'])
        all_ongoing_events.extend(calendar_data[date]['ongoing_events'])
    
    # Count total events for summary
    total_one_time = len(all_one_time_events)
    total_ongoing = len(all_ongoing_events)
    total_events = total_one_time + total_ongoing
    
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
    <body style="font-family: Arial, sans-serif; font-size: 16px; margin: 0; padding: 20px; background-color: #f5f5f5;">
        <div style="max-width: 800px; margin: 0 auto; background-color: white; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); overflow: hidden;">
            <!-- Professional Header -->
            <div style="background-color: #2c3e50; color: white; text-align: center; padding: 30px;">
                <h1 style="margin: 0; font-size: 32px; font-weight: 600;">📅 Calendar Summary</h1>
                <p style="margin: 10px 0 0 0; font-size: 16px; opacity: 0.9;">Here's your calendar summary for {date_range}</p>
            </div>
            
            <div style="padding: 30px;">
                <!-- Summary Section -->
                <div style="background-color: #ecf0f1; border-left: 4px solid #3498db; padding: 20px; margin-bottom: 30px; border-radius: 4px;">
                    <h3 style="margin: 0 0 10px 0; color: #2c3e50; font-size: 18px;">📊 Summary</h3>
                    <p style="margin: 0; color: #34495e; font-size: 16px;"><strong>{total_events} total events</strong> across {len(calendar_data)} days</p>
                    <p style="margin: 5px 0 0 0; color: #7f8c8d; font-size: 14px;">• {total_one_time} upcoming one-time events</p>
                    <p style="margin: 5px 0 0 0; color: #7f8c8d; font-size: 14px;">• {total_ongoing} ongoing events</p>
                </div>
    '''
    
    # Add one-time events if they exist
    if all_one_time_events:
        html_content += '''
                <!-- One-time Events Section -->
                <div style="margin-bottom: 30px;">
                    <h2 style="margin: 0 0 20px 0; color: #2c3e50; font-size: 22px; font-weight: 600; border-bottom: 2px solid #3498db; padding-bottom: 10px;">📅 Upcoming One-time Events</h2>
        '''
        
        # Group one-time events by date
        events_by_date = {}
        for event in all_one_time_events:
            date = format_date(event['start'])
            if date not in events_by_date:
                events_by_date[date] = []
            events_by_date[date].append(event)
        
        # Sort dates
        sorted_dates = sorted(events_by_date.keys(), key=lambda x: datetime.strptime(x, '%B %d'))
        
        for i, date in enumerate(sorted_dates):
            events = events_by_date[date]
            
            # Get full date for header
            try:
                # Find the original date from calendar_data
                for original_date in sorted(calendar_data.keys()):
                    date_obj = datetime.strptime(original_date, '%Y-%m-%d')
                    if date_obj.strftime('%B %d') == date:
                        full_date = date_obj.strftime('%A, %B %d')
                        break
                else:
                    full_date = date
            except:
                full_date = date
            
            html_content += f'''
                    <!-- Date Section -->
                    <div style="margin-bottom: 25px; border: 1px solid #e0e0e0; border-radius: 6px; overflow: hidden;">
                        <div style="background-color: #34495e; color: white; padding: 15px 20px;">
                            <h3 style="margin: 0; font-size: 18px; font-weight: 600;">{full_date}</h3>
                        </div>
                        <div style="padding: 20px; background-color: white;">
            '''
            
            for event in events:
                title = event["summary"]
                location = event.get('location', '')
                start_time = format_time(event['start'])
                end_time = format_end_time(event.get('end', ''))
                
                # Get emoji based on event title
                emoji = get_event_emoji(title)
                
                # Create event text
                event_text = f"{emoji} {title}"
                if location:
                    event_text += f" – {location}"
                
                # Add time information
                if end_time and end_time != start_time:
                    event_text += f" ({start_time} - {end_time})"
                else:
                    event_text += f" ({start_time})"
                
                # Add booking link separately if available
                if event.get('booking_links'):
                    cleaned_links = [clean_booking_url(link) for link in event['booking_links'] if clean_booking_url(link)]
                    if cleaned_links:
                        booking_link = cleaned_links[0]
                        event_text += f'<br><a href="{booking_link}" target="_blank" style="display: inline-block; background-color: #3498db; color: white; text-decoration: none; font-size: 12px; padding: 6px 12px; border-radius: 4px; margin-top: 8px; font-weight: 500;">🔗 Book Here</a>'
                        if len(cleaned_links) > 1:
                            event_text += f'<br><a href="{cleaned_links[1]}" target="_blank" style="display: inline-block; background-color: #27ae60; color: white; text-decoration: none; font-size: 12px; padding: 6px 12px; border-radius: 4px; margin-top: 5px; font-weight: 500;">🔗 Additional Booking</a>'
                
                html_content += f'''
                            <div style="margin-bottom: 12px; padding: 12px; background-color: #f8f9fa; border-left: 3px solid #3498db; border-radius: 3px;">
                                <div style="font-size: 15px; line-height: 1.4; color: #2c3e50;">• {event_text}</div>
                            </div>
                '''
            
            html_content += '''
                        </div>
                    </div>
            '''
        
        html_content += '''
                </div>
        '''
    
    # Add ongoing events summary if they exist
    if all_ongoing_events:
        html_content += '''
                <!-- Ongoing Events Summary Section -->
                <div style="margin-bottom: 30px;">
                    <h2 style="margin: 0 0 20px 0; color: #2c3e50; font-size: 22px; font-weight: 600; border-bottom: 2px solid #e67e22; padding-bottom: 10px;">📅 Ongoing Camps & Weekly Classes</h2>
                    <div style="background-color: #fef9e7; border: 1px solid #f39c12; border-radius: 6px; padding: 20px;">
        '''
        
        # Group ongoing events by category
        events_by_category = {
            'Summer Camps': [],
            'Weekly Programs': [],
            'Other Activities': []
        }
        
        for event in all_ongoing_events:
            title = event["summary"].lower()
            
            # Categorize events based on title keywords - check Summer Camps first
            if any(word in title for word in ['camp', 'summer', 'immersion', '2025']):
                events_by_category['Summer Camps'].append(event)
            elif any(word in title for word in ['weekly', 'club', 'program', 'class', 'basketball', 'volleyball', 'tennis', 'soccer', 'baseball', 'track']):
                events_by_category['Weekly Programs'].append(event)
            else:
                events_by_category['Other Activities'].append(event)
        
        # Display Summer Camps section
        if events_by_category['Summer Camps']:
            html_content += '''
                        <div style="margin-bottom: 20px;">
                            <h3 style="margin: 0 0 15px 0; color: #2c3e50; font-size: 18px; font-weight: 600;">😊 Summer Camps</h3>
            '''
            
            # Group by base title to consolidate similar events (e.g., basketball club by age groups)
            camps_by_base_title = {}
            for event in events_by_category['Summer Camps']:
                title = event["summary"]
                
                # Extract base title by removing age group brackets and extra details
                base_title = title
                # Remove age group patterns like [Ages X-X] or (Ages X-X)
                base_title = re.sub(r'\s*\[Ages?\s*\d+-\d+\]', '', base_title)
                base_title = re.sub(r'\s*\(Ages?\s*\d+-\d+\)', '', base_title)
                # Remove extra whitespace
                base_title = base_title.strip()
                
                # Extract age group if present
                age_match = re.search(r'\[Ages?\s*(\d+-\d+)\]|\(Ages?\s*(\d+-\d+)\)', title)
                age_group = age_match.group(1) or age_match.group(2) if age_match else None
                
                # Create unique key that includes age group to keep them separate
                if age_group:
                    unique_key = f"{base_title} [Ages {age_group}]"
                else:
                    unique_key = base_title
                
                if unique_key not in camps_by_base_title:
                    camps_by_base_title[unique_key] = {
                        'events': [],
                        'dates': set(),
                        'locations': set(),
                        'times': set(),
                        'base_title': base_title,
                        'age_group': age_group
                    }
                
                date = format_date(event['start'])
                time = format_time(event['start'])
                end_time = format_end_time(event.get('end', ''))
                camps_by_base_title[unique_key]['events'].append(event)
                camps_by_base_title[unique_key]['dates'].add(date)
                camps_by_base_title[unique_key]['times'].add(time)
                if event.get('end'):
                    camps_by_base_title[unique_key]['end_times'] = camps_by_base_title[unique_key].get('end_times', set())
                    camps_by_base_title[unique_key]['end_times'].add(end_time)
                if event.get('location'):
                    camps_by_base_title[unique_key]['locations'].add(event['location'])
            
            for unique_key, info in camps_by_base_title.items():
                events = info['events']
                dates = sorted(info['dates'], key=lambda x: datetime.strptime(x, '%B %d'))
                times = sorted(info['times'])
                end_times = sorted(info.get('end_times', set()))
                locations = list(info['locations'])
                base_title = info['base_title']
                age_group = info['age_group']
                
                # Create event text
                event_text = base_title
                
                # Add age group if present
                if age_group:
                    event_text += f" [Ages {age_group}]"
                
                if locations:
                    event_text += f" – {', '.join(locations)}"
                
                # Enhanced logic to determine if it's a daily/recurring event
                title_lower = base_title.lower()
                is_recurring_by_keywords = any(word in title_lower for word in ['camp', 'daily', 'weekly', 'ongoing', 'recurring', 'class', 'program', 'club'])
                
                # Check if events span multiple days or appear frequently
                date_objects = [datetime.strptime(date, '%B %d') for date in dates]
                date_range_days = (max(date_objects) - min(date_objects)).days + 1
                events_per_day = len(events) / len(dates) if dates else 0
                
                # Consider it daily if:
                # 1. Has recurring keywords, OR
                # 2. Spans multiple days, OR  
                # 3. Has multiple events per day (like different age groups)
                is_daily = (is_recurring_by_keywords or 
                           len(dates) > 1 or 
                           events_per_day > 1 or
                           'summer' in title_lower)
                
                if is_daily:
                    # Daily event - show as daily with all times
                    if end_times and len(end_times) == len(times):
                        # Show start-end time pairs
                        time_pairs = []
                        for i, start_time in enumerate(times):
                            if i < len(end_times):
                                time_pairs.append(f"{start_time}-{end_times[i]}")
                            else:
                                time_pairs.append(start_time)
                        event_text += f" (daily, {', '.join(time_pairs)})"
                    else:
                        # Just show start times
                        event_text += f" (daily, {', '.join(times)})"
                else:
                    # Single day event - show date and time
                    if end_times and len(end_times) == len(times):
                        # Show start-end time pairs
                        time_pairs = []
                        for i, start_time in enumerate(times):
                            if i < len(end_times):
                                time_pairs.append(f"{start_time}-{end_times[i]}")
                            else:
                                time_pairs.append(start_time)
                        event_text += f" ({dates[0]}, {', '.join(time_pairs)})"
                    else:
                        # Just show start times
                        event_text += f" ({dates[0]}, {', '.join(times)})"
                
                html_content += f'''
                            <div style="margin-bottom: 8px; font-size: 15px; line-height: 1.4; color: #2c3e50;">• {event_text}</div>
                '''
            
            html_content += '''
                        </div>
            '''
        
        # Display Weekly Programs section
        if events_by_category['Weekly Programs']:
            html_content += '''
                        <div style="margin-bottom: 20px;">
                            <h3 style="margin: 0 0 15px 0; color: #2c3e50; font-size: 18px; font-weight: 600;">🏀 Weekly Rec Center Programs</h3>
            '''
            
            # Group by base title to consolidate similar events
            programs_by_base_title = {}
            for event in events_by_category['Weekly Programs']:
                title = event["summary"]
                
                # Extract base title by removing age group brackets and extra details
                base_title = title
                # Remove age group patterns like [Ages X-X] or (Ages X-X)
                base_title = re.sub(r'\s*\[Ages?\s*\d+-\d+\]', '', base_title)
                base_title = re.sub(r'\s*\(Ages?\s*\d+-\d+\)', '', base_title)
                # Remove extra whitespace
                base_title = base_title.strip()
                
                # Extract age group if present
                age_match = re.search(r'\[Ages?\s*(\d+-\d+)\]|\(Ages?\s*(\d+-\d+)\)', title)
                age_group = age_match.group(1) or age_match.group(2) if age_match else None
                
                # Create unique key that includes age group to keep them separate
                if age_group:
                    unique_key = f"{base_title} [Ages {age_group}]"
                else:
                    unique_key = base_title
                
                if unique_key not in programs_by_base_title:
                    programs_by_base_title[unique_key] = {
                        'events': [],
                        'dates': set(),
                        'locations': set(),
                        'times': set(),
                        'base_title': base_title,
                        'age_group': age_group
                    }
                
                date = format_date(event['start'])
                time = format_time(event['start'])
                end_time = format_end_time(event.get('end', ''))
                programs_by_base_title[unique_key]['events'].append(event)
                programs_by_base_title[unique_key]['dates'].add(date)
                programs_by_base_title[unique_key]['times'].add(time)
                if event.get('end'):
                    programs_by_base_title[unique_key]['end_times'] = programs_by_base_title[unique_key].get('end_times', set())
                    programs_by_base_title[unique_key]['end_times'].add(end_time)
                if event.get('location'):
                    programs_by_base_title[unique_key]['locations'].add(event['location'])
            
            for unique_key, info in programs_by_base_title.items():
                events = info['events']
                dates = sorted(info['dates'], key=lambda x: datetime.strptime(x, '%B %d'))
                times = sorted(info['times'])
                end_times = sorted(info.get('end_times', set()))
                locations = list(info['locations'])
                base_title = info['base_title']
                age_group = info['age_group']
                
                # Create event text
                event_text = base_title
                
                # Add age group if present
                if age_group:
                    event_text += f" [Ages {age_group}]"
                
                if locations:
                    event_text += f" – {', '.join(locations)}"
                
                # Enhanced logic to determine if it's a daily/recurring event
                title_lower = base_title.lower()
                is_recurring_by_keywords = any(word in title_lower for word in ['camp', 'daily', 'weekly', 'ongoing', 'recurring', 'class', 'program', 'club'])
                
                # Check if events span multiple days or appear frequently
                date_objects = [datetime.strptime(date, '%B %d') for date in dates]
                date_range_days = (max(date_objects) - min(date_objects)).days + 1
                events_per_day = len(events) / len(dates) if dates else 0
                
                # Consider it daily if:
                # 1. Has recurring keywords, OR
                # 2. Spans multiple days, OR  
                # 3. Has multiple events per day (like different age groups)
                is_daily = (is_recurring_by_keywords or 
                           len(dates) > 1 or 
                           events_per_day > 1)
                
                if is_daily:
                    # Daily event - show as daily with all times
                    if end_times and len(end_times) == len(times):
                        # Show start-end time pairs
                        time_pairs = []
                        for i, start_time in enumerate(times):
                            if i < len(end_times):
                                time_pairs.append(f"{start_time}-{end_times[i]}")
                            else:
                                time_pairs.append(start_time)
                        event_text += f" (daily, {', '.join(time_pairs)})"
                    else:
                        # Just show start times
                        event_text += f" (daily, {', '.join(times)})"
                else:
                    # Single day event - show date and time
                    event_text += f" ({dates[0]}, {', '.join(times)})"
                
                html_content += f'''
                            <div style="margin-bottom: 8px; font-size: 15px; line-height: 1.4; color: #2c3e50;">• {event_text}</div>
                '''
            
            html_content += '''
                        </div>
            '''
        
        # Display Other Activities section
        if events_by_category['Other Activities']:
            html_content += '''
                        <div style="margin-bottom: 20px;">
                            <h3 style="margin: 0 0 15px 0; color: #2c3e50; font-size: 18px; font-weight: 600;">⛵ Other Activities</h3>
            '''
            
            # Group by base title to consolidate similar events
            activities_by_base_title = {}
            for event in events_by_category['Other Activities']:
                title = event["summary"]
                
                # Extract base title by removing age group brackets and extra details
                base_title = title
                # Remove age group patterns like [Ages X-X] or (Ages X-X)
                base_title = re.sub(r'\s*\[Ages?\s*\d+-\d+\]', '', base_title)
                base_title = re.sub(r'\s*\(Ages?\s*\d+-\d+\)', '', base_title)
                # Remove extra whitespace
                base_title = base_title.strip()
                
                # Extract age group if present
                age_match = re.search(r'\[Ages?\s*(\d+-\d+)\]|\(Ages?\s*(\d+-\d+)\)', title)
                age_group = age_match.group(1) or age_match.group(2) if age_match else None
                
                # Create unique key that includes age group to keep them separate
                if age_group:
                    unique_key = f"{base_title} [Ages {age_group}]"
                else:
                    unique_key = base_title
                
                if unique_key not in activities_by_base_title:
                    activities_by_base_title[unique_key] = {
                        'events': [],
                        'dates': set(),
                        'locations': set(),
                        'times': set(),
                        'base_title': base_title,
                        'age_group': age_group
                    }
                
                date = format_date(event['start'])
                time = format_time(event['start'])
                end_time = format_end_time(event.get('end', ''))
                activities_by_base_title[unique_key]['events'].append(event)
                activities_by_base_title[unique_key]['dates'].add(date)
                activities_by_base_title[unique_key]['times'].add(time)
                if event.get('end'):
                    activities_by_base_title[unique_key]['end_times'] = activities_by_base_title[unique_key].get('end_times', set())
                    activities_by_base_title[unique_key]['end_times'].add(end_time)
                if event.get('location'):
                    activities_by_base_title[unique_key]['locations'].add(event['location'])
            
            for unique_key, info in activities_by_base_title.items():
                events = info['events']
                dates = sorted(info['dates'], key=lambda x: datetime.strptime(x, '%B %d'))
                times = sorted(info['times'])
                end_times = sorted(info.get('end_times', set()))
                locations = list(info['locations'])
                base_title = info['base_title']
                age_group = info['age_group']
                
                # Create event text
                event_text = base_title
                
                # Add age group if present
                if age_group:
                    event_text += f" [Ages {age_group}]"
                
                if locations:
                    event_text += f" – {', '.join(locations)}"
                
                # Enhanced logic to determine if it's a daily/recurring event
                title_lower = base_title.lower()
                is_recurring_by_keywords = any(word in title_lower for word in ['camp', 'daily', 'weekly', 'ongoing', 'recurring', 'class', 'program', 'club', 'ride', 'bus'])
                
                # Check if events span multiple days or appear frequently
                date_objects = [datetime.strptime(date, '%B %d') for date in dates]
                date_range_days = (max(date_objects) - min(date_objects)).days + 1
                events_per_day = len(events) / len(dates) if dates else 0
                
                # Consider it daily if:
                # 1. Has recurring keywords, OR
                # 2. Spans multiple days, OR  
                # 3. Has multiple events per day (like different age groups)
                is_daily = (is_recurring_by_keywords or 
                           len(dates) > 1 or 
                           events_per_day > 1)
                
                if is_daily:
                    # Daily event - show as daily with all times
                    if end_times and len(end_times) == len(times):
                        # Show start-end time pairs
                        time_pairs = []
                        for i, start_time in enumerate(times):
                            if i < len(end_times):
                                time_pairs.append(f"{start_time}-{end_times[i]}")
                            else:
                                time_pairs.append(start_time)
                        event_text += f" (daily, {', '.join(time_pairs)})"
                    else:
                        # Just show start times
                        event_text += f" (daily, {', '.join(times)})"
                else:
                    # Single day event - show date and time
                    if end_times and len(end_times) == len(times):
                        # Show start-end time pairs
                        time_pairs = []
                        for i, start_time in enumerate(times):
                            if i < len(end_times):
                                time_pairs.append(f"{start_time}-{end_times[i]}")
                            else:
                                time_pairs.append(start_time)
                        event_text += f" ({dates[0]}, {', '.join(time_pairs)})"
                    else:
                        # Just show start times
                        event_text += f" ({dates[0]}, {', '.join(times)})"
                
                html_content += f'''
                            <div style="margin-bottom: 8px; font-size: 15px; line-height: 1.4; color: #2c3e50;">• {event_text}</div>
                '''
            
            html_content += '''
                        </div>
            '''
        
        html_content += '''
                    </div>
                </div>
        '''
    
    html_content += '''
                <!-- Professional Footer -->
                <div style="text-align: center; color: #7f8c8d; margin-top: 30px; padding: 20px; border-top: 1px solid #ecf0f1; background-color: #f8f9fa;">
                    <p style="margin: 0; font-size: 14px;">This email was automatically generated from your Google Calendar data.</p>
                    <p style="margin: 5px 0 0 0; font-size: 12px; opacity: 0.7;">Powered by Calendar Summary Bot</p>
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

def format_end_time(time_str):
    """
    Format end time string for display.
    
    :param time_str: ISO format time string
    :return: Formatted end time string
    """
    if 'T' in time_str:
        # Has time component
        try:
            dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
            return dt.strftime('%I:%M%p')
        except:
            return time_str
    else:
        # Date only - return empty string since no end time
        return ""

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

def get_event_emoji(title):
    """
    Get appropriate emoji based on event title.
    
    :param title: Event title
    :return: Emoji string
    """
    title_lower = title.lower()
    
    # Storytime and reading events
    if any(word in title_lower for word in ['storytime', 'story', 'read', 'book', 'tale']):
        return '📚'
    
    # Music events
    if any(word in title_lower for word in ['music', 'musica', 'jam', 'song', 'sing']):
        return '🎵'
    
    # Yoga and fitness events
    if any(word in title_lower for word in ['yoga', 'zen', 'fit', 'exercise', 'workout']):
        return '🧘'
    
    # Art and craft events
    if any(word in title_lower for word in ['art', 'craft', 'paint', 'draw', 'creative']):
        return '🎨'
    
    # Games and activities
    if any(word in title_lower for word in ['game', 'chess', 'play', 'activity']):
        return '🎲'
    
    # Bike and outdoor events
    if any(word in title_lower for word in ['bike', 'bicycle', 'outdoor', 'beach']):
        return '🚲'
    
    # Photo and media events
    if any(word in title_lower for word in ['photo', 'picture', 'frame', 'media']):
        return '🖼️'
    
    # Baby and toddler events
    if any(word in title_lower for word in ['baby', 'toddler', 'infant', 'child']):
        return '👶'
    
    # Teen events
    if any(word in title_lower for word in ['teen', 'adolescent', 'youth']):
        return '👨‍🎓'
    
    # Adult events
    if any(word in title_lower for word in ['adult', 'grown']):
        return '👤'
    
    # Default emoji
    return '📅' 