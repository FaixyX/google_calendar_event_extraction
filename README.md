# Google Calendar Email Sender

This project fetches events from your Google Calendar and sends them via email in a beautifully formatted HTML email.

## Features

- 📅 Fetches calendar events for the current week (Monday to Sunday)
- 📧 Sends beautifully formatted HTML emails with calendar data
- 🔄 Handles both one-time and ongoing events
- 📍 Includes event locations and descriptions
- 🎨 Responsive email design with proper styling
- 📱 Plain text fallback for email clients that don't support HTML

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

Run the main script:

```bash
python script.py
```

The script will:
1. Authenticate with Google Calendar
2. Fetch events for the current week
3. Save data to JSON file
4. Send a formatted email with the calendar data

## Email Features

- **HTML Formatting**: Beautiful, responsive design with proper styling
- **Event Categorization**: Separates ongoing and one-time events
- **Time Formatting**: Converts ISO timestamps to readable format
- **Location Support**: Displays event locations when available
- **Description Support**: Shows event descriptions with HTML cleaning
- **Plain Text Fallback**: Ensures compatibility with all email clients

## File Structure

- `script.py` - Main calendar fetching script
- `email_sender.py` - Email functionality module
- `data.json` - Output file with calendar data
- `requirements.txt` - Python dependencies

## Troubleshooting

### Email Issues
- Ensure you're using an App Password for Gmail
- Check that SMTP settings are correct
- Verify recipient email address

### Calendar Issues
- Make sure the calendar name matches exactly
- Check that credentials.json is in the correct location
- Ensure the Google Calendar API is enabled

## Security Notes

- Never commit your `.env` file to version control
- Keep your credentials.json file secure
- Use App Passwords instead of regular passwords for email 