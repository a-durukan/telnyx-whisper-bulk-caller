# Telnyx Whisper Bulk Caller - Web GUI

A modern web-based interface for the Telnyx Whisper Bulk Caller application. This application allows you to make bulk phone calls, record them, and transcribe the recordings using AI.

![Web GUI Dashboard](https://img.shields.io/badge/status-active-success.svg)
![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/flask-3.0.0-green.svg)

## Features

- 🎯 **Modern Web Interface**: Clean, intuitive UI for easy navigation
- 📞 **Bulk Calling**: Make multiple calls simultaneously with Telnyx API
- 🎙️ **Auto Recording**: Automatically record all calls
- 🤖 **AI Transcription**: Transcribe recordings using OpenAI Whisper
- 🎵 **Audio Transcriber**: Batch transcribe audio files
- 📊 **Results Viewer**: View and download results as TSV files
- ⚙️ **Configuration Management**: Secure API key storage
- 📈 **Real-time Monitoring**: Track active calls and progress

## Prerequisites

- Python 3.8 or higher
- Telnyx account with API key and phone number
- OpenAI account with API key
- Flask-compatible web server (included)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/a-durukan/telnyx-whisper-bulk-caller.git
cd telnyx-whisper-bulk-caller
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Starting the Web Application

Run the web application:
```bash
python web_app.py
```

The application will start on `http://localhost:5000`

### Web Interface Pages

#### 1. Home (`/`)
- Overview of features
- Quick links to all sections
- Getting started guide

#### 2. Configuration (`/config`)
- Set up Telnyx API key
- Set up OpenAI API key
- Configure connection ID
- Set from number
- Set audio file URL

#### 3. Bulk Caller (`/caller`)
- Upload phone numbers file (one number per line)
- Start bulk calling process
- Monitor active calls in real-time
- View call status

#### 4. Call Results (`/results`)
- View transcription results
- See call statistics
- Download results as TSV

#### 5. Audio Transcriber (`/transcriber`)
- Upload audio files for transcription
- Batch transcribe multiple files
- View and download transcriptions

## Configuration

On first run, navigate to the Configuration page and enter:

- **Telnyx API Key**: Your Telnyx API key
- **OpenAI API Key**: Your OpenAI API key
- **Connection ID**: Your Telnyx connection ID
- **From Number**: The phone number to call from (E.164 format, e.g., +1234567890)
- **Audio URL**: URL of the audio file to play during calls

Configuration is saved to `config.json` in the application directory.

## Phone Numbers Format

Create a text file with phone numbers in E.164 format (one per line):

```
+12025551234
+12025555678
+12025559012
```

## Webhook Configuration

For the calling functionality to work properly, you need to configure webhooks in your Telnyx account:

1. Go to your Telnyx Dashboard
2. Navigate to your Connection settings
3. Set the webhook URL to: `http://your-server:5000/webhook`
4. Set the recording webhook to: `http://your-server:5000/webhook/call-recording-saved`

## File Structure

```
telnyx-whisper-bulk-caller/
├── web_app.py              # Main Flask application
├── run.py                  # Original CLI application
├── transcriber.py          # Original transcriber script
├── requirements.txt        # Python dependencies
├── README_WEB.md          # This file
├── README.md              # Original README
├── templates/             # HTML templates
│   ├── base.html         # Base template
│   ├── index.html        # Home page
│   ├── config.html       # Configuration page
│   ├── caller.html       # Bulk caller page
│   ├── results.html      # Results page
│   └── transcriber.html  # Transcriber page
└── uploads/              # Temporary upload directory
```

## API Endpoints

The web application exposes several API endpoints:

- `GET/POST /api/config` - Get/update configuration
- `POST /api/start-calls` - Start bulk calling
- `GET /api/call-status` - Get active calls status
- `GET /api/results` - Get call results
- `GET /api/download-results` - Download results TSV
- `POST /api/transcribe` - Transcribe audio files
- `GET /api/transcriptions` - Get transcriptions
- `GET /api/download-transcriptions` - Download transcriptions TSV
- `POST /webhook` - Telnyx webhook endpoint
- `POST /webhook/call-recording-saved` - Recording webhook endpoint

## Security Notes

- API keys are stored locally in `config.json`
- Keep your API keys secure and never commit them to version control
- The application uses HTTPS in production (recommended)
- Configure proper firewall rules for webhook endpoints

## Original CLI Application

The original command-line applications are still available:

- `run.py` - Original Flask app with CLI
- `transcriber.py` - Standalone transcription script

See the main [README.md](README.md) for documentation on the original applications.

## Troubleshooting

### Calls not being made
- Check your Telnyx API key and connection ID in Configuration
- Verify your from number is properly configured
- Check webhook configuration in Telnyx dashboard

### Transcriptions failing
- Verify OpenAI API key in Configuration
- Check API rate limits
- Ensure audio files are in supported formats

### Webhook not receiving events
- Ensure your server is publicly accessible
- Check firewall rules
- Verify webhook URL in Telnyx dashboard

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is open source and available under the MIT License.

## Credits

Original application by [@yigitkonur](https://twitter.com/yigitkonur)

Backstory: https://twitter.com/yigitkonur/status/1654827917845860353

## Support

For issues and questions, please use the GitHub issue tracker.
