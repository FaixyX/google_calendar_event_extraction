#!/usr/bin/env python3
"""
Demo script showing the interactive date selection functionality

This script demonstrates how the interactive date selection works
without actually connecting to Google Calendar or sending emails.
"""

from datetime import datetime, timedelta, timezone
import calendar

def parse_custom_date_range(date_input):
    """
    Parse custom date range input and return time_min and time_max in ISO format.
    (Same function as in script.py)
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
        return None, None

def get_date_range_interactively():
    """
    Ask user for date range interactively.
    (Same function as in script.py)
    """
    print("\n" + "="*60)
    print("📅 GOOGLE CALENDAR EVENT FETCHER - DEMO")
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

def main():
    """Demo the interactive date selection."""
    print("🎯 DEMO: Interactive Date Selection")
    print("This demo shows how the interactive date selection works.")
    print("No actual calendar data will be fetched or emails sent.")
    
    # Get date range from user
    date_range_input = get_date_range_interactively()
    
    if date_range_input:
        print(f"\n🎯 Selected date range: '{date_range_input}'")
        
        # Parse the date range
        time_min, time_max = parse_custom_date_range(date_range_input)
        
        if time_min and time_max:
            # Convert back to readable format for display
            start_dt = datetime.fromisoformat(time_min.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(time_max.replace('Z', '+00:00'))
            
            print(f"✅ Date range parsed successfully:")
            print(f"   Start: {start_dt.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            print(f"   End:   {end_dt.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            
            # Calculate duration
            duration = (end_dt - start_dt).days + 1
            print(f"   Duration: {duration} day(s)")
            
            print(f"\n📧 In the real application, this would:")
            print(f"   1. Fetch events from Google Calendar for this date range")
            print(f"   2. Save the data to a JSON file")
            print(f"   3. Send a formatted email with the calendar data")
            
        else:
            print("❌ Failed to parse date range.")
    else:
        print(f"\n📅 Using default date range (Current Week).")
        print(f"📧 In the real application, this would fetch the current week's events.")
    
    print(f"\n🎉 Demo completed!")
    print(f"To use the real functionality, run: python script.py")

if __name__ == "__main__":
    main() 