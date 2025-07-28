#!/usr/bin/env python3
"""
Interactive Google Calendar Event Fetcher

This script provides a user-friendly interface for fetching calendar events
for custom date ranges without needing to remember command line arguments.
"""

import os
import sys
from datetime import datetime, timedelta, timezone
import calendar
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import the main calendar functions
from script import get_events_for_custom_range, send_calendar_email, GOOGLE_CALENDAR_NAME

def display_menu():
    """Display the main menu options."""
    print("\n" + "="*60)
    print("📅 GOOGLE CALENDAR EVENT FETCHER")
    print("="*60)
    print("Choose a date range option:")
    print()
    print("1. Current week (Monday to Sunday)")
    print("2. Next week")
    print("3. This month")
    print("4. Next month")
    print("5. Custom date range (e.g., Aug 1 to Aug 4)")
    print("6. Specific month (e.g., August 2024)")
    print("7. Exit")
    print()

def get_custom_date_range():
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

def get_specific_month():
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
            from script import parse_custom_date_range
            time_min, time_max = parse_custom_date_range(month_input)
            
            if time_min and time_max:
                return month_input
            else:
                print("❌ Invalid month format. Please try again.")
                continue
                
        except KeyboardInterrupt:
            print("\n\n👋 Cancelled by user.")
            return None

def get_email_preference():
    """Ask user if they want to send email."""
    print("\n📧 Email Options")
    print("-" * 15)
    print("1. Send email with calendar data")
    print("2. Save to JSON file only (no email)")
    print()
    
    while True:
        choice = input("Choose option (1 or 2): ").strip()
        if choice == "1":
            return True
        elif choice == "2":
            return False
        else:
            print("❌ Please enter 1 or 2.")

def main():
    """Main interactive function."""
    # Check if calendar name is configured
    calendar_name = GOOGLE_CALENDAR_NAME
    if not calendar_name:
        print("❌ Error: GOOGLE_CALENDAR_NAME not set in environment variables.")
        print("Please set it in your .env file or environment.")
        return
    
    print(f"📅 Connected to calendar: {calendar_name}")
    
    while True:
        display_menu()
        
        try:
            choice = input("Enter your choice (1-7): ").strip()
            
            if choice == "1":
                date_range = None  # Default current week
                print("\n🎯 Fetching events for current week...")
                
            elif choice == "2":
                date_range = "next week"
                print("\n🎯 Fetching events for next week...")
                
            elif choice == "3":
                date_range = "this month"
                print("\n🎯 Fetching events for this month...")
                
            elif choice == "4":
                date_range = "next month"
                print("\n🎯 Fetching events for next month...")
                
            elif choice == "5":
                date_range = get_custom_date_range()
                if not date_range:
                    continue
                print(f"\n🎯 Fetching events for: {date_range}")
                
            elif choice == "6":
                date_range = get_specific_month()
                if not date_range:
                    continue
                print(f"\n🎯 Fetching events for: {date_range}")
                
            elif choice == "7":
                print("\n👋 Goodbye!")
                break
                
            else:
                print("❌ Invalid choice. Please enter a number between 1 and 7.")
                continue
            
            # Get email preference
            send_email = get_email_preference()
            
            # Fetch events
            print("\n⏳ Fetching calendar events...")
            events = get_events_for_custom_range(calendar_name, date_range)
            
            if events:
                if send_email:
                    print("\n📧 Sending email...")
                    email_sent = send_calendar_email(events)
                    if email_sent:
                        print("🎉 Calendar data has been sent via email!")
                    else:
                        print("⚠️  Email sending failed, but calendar data was saved to JSON file.")
                else:
                    print("\n✅ Calendar data saved to JSON file only.")
                
                # Show summary
                total_events = sum(len(day['one_time_events']) + len(day['ongoing_events']) 
                                 for day in events.values())
                print(f"📊 Summary: {total_events} events across {len(events)} days")
                
            else:
                print("📭 No events found for the specified date range.")
            
            # Ask if user wants to continue
            print("\n" + "-" * 40)
            continue_choice = input("Would you like to fetch another date range? (y/n): ").strip().lower()
            if continue_choice not in ['y', 'yes']:
                print("\n👋 Goodbye!")
                break
                
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ An error occurred: {e}")
            print("Please try again.")

if __name__ == "__main__":
    main() 