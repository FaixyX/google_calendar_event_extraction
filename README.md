# Google Calendar Email Sender

This project fetches events from your Google Calendar and sends them via email in a beautifully formatted HTML email.

## Features

- 📅 Fetches calendar events for custom date ranges
- 📧 Sends beautifully formatted HTML emails with calendar data
- 🔄 Handles both one-time and ongoing events
- 📍 Includes event locations and descriptions
- 🎨 Responsive email design with proper styling
- 📱 Plain text fallback for email clients that don't support HTML
- 🎯 **NEW**: Interactive mode for easy date range selection
- 🎯 **NEW**: Support for custom date ranges and whole months

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Google Calendar Setup

1. Create a Google Cloud Project
2. Enable the Google Calendar API
3. Create credentials (OAuth 2.0 Client ID)
4. Download the credentials file as `credentials.json`

### 3. Email Setup

For Gmail users:
1. Enable 2-Factor Authentication
2. Generate an App Password
3. Use the App Password instead of your regular password

### 4. Environment Configuration

Create a `.env` file with the following variables:

```env
# Google Calendar Configuration
GOOGLE_CALENDAR_NAME=Your Calendar Name
GOOGLE_CREDENTIALS_FILE=credentials.json
GOOGLE_TOKEN_FILE=token.pickle
GOOGLE_CALENDAR_SCOPES=https://www.googleapis.com/auth/calendar.readonly

# Output Configuration
OUTPUT_JSON_FILE=data.json
MAX_RESULTS=100000
ENABLE_HTML_CLEANING=true

# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USER=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
RECIPIENT_EMAIL=recipient@example.com
```

## Usage

### Interactive Mode (Recommended)

Simply run the main script and it will ask you for the date range:

```bash
python script.py
```

The program will present you with a menu to choose from:

1. **Current week (Monday to Sunday)** - DEFAULT
2. **Next week** - Next Monday to Sunday from today
3. **This month** - Current month
4. **Next month** - Next month
5. **Custom date range** - Enter specific start and end dates
6. **Specific month** - Enter a month and year (e.g., "August 2024")

### Alternative Interactive Script

You can also use the dedicated interactive script:

```bash
python interactive_calendar.py
```

This provides the same functionality with additional options like choosing whether to send email or just save to JSON.

### Supported Date Formats

When entering custom dates, the system supports various formats:

#### Custom Date Ranges
- Enter start and end dates in `YYYY-MM-DD` format
- Examples: `2024-08-01` to `2024-08-04`

#### Whole Months
- `"august 2024"` - All of August 2024
- `"aug 2024"` - All of August 2024 (abbreviated)
- `"2024-08"` - All of August 2024 (YYYY-MM format)
- `"december 2024"` - All of December 2024

#### Relative Time Periods
- `"next week"` - Next Monday to Sunday from today
- `"this month"` - Current month
- `"next month"` - Next month

## Email Features

- **HTML Formatting**: Beautiful, responsive design with proper styling
- **Event Categorization**: Separates ongoing and one-time events
- **Time Formatting**: Converts ISO timestamps to readable format
- **Location Support**: Displays event locations when available
- **Description Support**: Shows event descriptions with HTML cleaning
- **Plain Text Fallback**: Ensures compatibility with all email clients

## File Structure

- `script.py` - Main calendar fetching script with interactive mode
- `interactive_calendar.py` - Alternative interactive mode with more options
- `email_sender.py` - Email functionality module
- `data.json` - Output file with calendar data
- `requirements.txt` - Python dependencies

## Examples

### Example 1: Get August 1-4 Events
1. Run: `python script.py`
2. Choose option 5 (Custom date range)
3. Enter: Start date: `2024-08-01`
4. Enter: End date: `2024-08-04`

### Example 2: Get Whole Month of August
1. Run: `python script.py`
2. Choose option 6 (Specific month)
3. Enter: `august 2024`

### Example 3: Get Next Week
1. Run: `python script.py`
2. Choose option 2 (Next week)

## Troubleshooting

### Email Issues
- Ensure you're using an App Password for Gmail
- Check that SMTP settings are correct
- Verify recipient email address

### Calendar Issues
- Make sure the calendar name matches exactly
- Check that credentials.json is in the correct location
- Ensure the Google Calendar API is enabled

### Date Range Issues
- Use the exact format shown in examples
- Dates should be in YYYY-MM-DD format
- Month names are case-insensitive

## Security Notes

- Never commit your `.env` file to version control
- Keep your credentials.json file secure
- Use App Passwords instead of regular passwords for email 