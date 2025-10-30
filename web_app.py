import concurrent.futures
import csv
import json
import os
import time
import logging
import secrets
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
import telnyx
import openai

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(32))
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload

# Setup logging
logging.basicConfig(level=logging.INFO)

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Global variables to keep track of active calls and their recordings
active_calls = {}
call_results = []
app_config = {
    'telnyx_api_key': '',
    'openai_api_key': '',
    'connection_id': '',
    'from_number': '',
    'audio_url': ''
}

# Function to save configuration
def save_config():
    with open('config.json', 'w') as f:
        json.dump(app_config, f)

# Function to load configuration
def load_config():
    global app_config
    if os.path.exists('config.json'):
        with open('config.json', 'r') as f:
            app_config = json.load(f)
            if app_config.get('telnyx_api_key'):
                telnyx.api_key = app_config['telnyx_api_key']
            if app_config.get('openai_api_key'):
                openai.api_key = app_config['openai_api_key']

# Load config on startup
load_config()

# Function to make a call and play a sound
def call_and_play_sound(number):
    logging.info(f"Calling {number}...")
    try:
        call = telnyx.Call.create(
            connection_id=app_config['connection_id'],
            to=number,
            from_=app_config['from_number']
        )
        active_calls[call.call_control_id] = {
            'call': call,
            'number': number,
            'status': 'initiated',
            'start_time': datetime.now().isoformat()
        }
        return {'success': True, 'call_id': call.call_control_id}
    except Exception as e:
        logging.error(f"Error calling {number}: {str(e)}")
        return {'success': False, 'error': str(e), 'number': number}

# Function to transcribe audio file
def transcribe_audio_file(file_path, filename):
    retries = 0
    while retries < 3:
        try:
            with open(file_path, 'rb') as audio_file:
                transcript = openai.Audio.transcribe("whisper-1", audio_file)
                return {'filename': filename, 'transcription': transcript["text"], 'success': True}
        except Exception as e:
            logging.error(f"Error transcribing {filename}: {str(e)}")
            retries += 1
            time.sleep(2 ** retries)
    return {'filename': filename, 'error': 'Failed after 3 retries', 'success': False}

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/config')
def config_page():
    return render_template('config.html')

@app.route('/api/config', methods=['GET', 'POST'])
def api_config():
    global app_config
    if request.method == 'POST':
        data = request.json
        app_config['telnyx_api_key'] = data.get('telnyx_api_key', '')
        app_config['openai_api_key'] = data.get('openai_api_key', '')
        app_config['connection_id'] = data.get('connection_id', '')
        app_config['from_number'] = data.get('from_number', '')
        app_config['audio_url'] = data.get('audio_url', '')
        
        # Update API keys
        if app_config['telnyx_api_key']:
            telnyx.api_key = app_config['telnyx_api_key']
        if app_config['openai_api_key']:
            openai.api_key = app_config['openai_api_key']
        
        save_config()
        return jsonify({'success': True, 'message': 'Configuration saved'})
    else:
        # Return config with masked API keys
        masked_config = app_config.copy()
        if masked_config['telnyx_api_key']:
            masked_config['telnyx_api_key'] = masked_config['telnyx_api_key'][:10] + '...'
        if masked_config['openai_api_key']:
            masked_config['openai_api_key'] = masked_config['openai_api_key'][:10] + '...'
        return jsonify(masked_config)

@app.route('/caller')
def caller_page():
    return render_template('caller.html')

@app.route('/api/start-calls', methods=['POST'])
def start_calls():
    if 'numbers_file' not in request.files:
        return jsonify({'success': False, 'error': 'No file uploaded'})
    
    file = request.files['numbers_file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'})
    
    # Read numbers from file
    numbers = []
    try:
        content = file.read().decode('utf-8')
        numbers = [line.strip() for line in content.split('\n') if line.strip()]
    except Exception as e:
        return jsonify({'success': False, 'error': f'Error reading file: {str(e)}'})
    
    if not numbers:
        return jsonify({'success': False, 'error': 'No phone numbers found in file'})
    
    # Start calling in background
    results = []
    for number in numbers:
        result = call_and_play_sound(number)
        results.append(result)
        time.sleep(0.5)  # Small delay between calls
    
    return jsonify({
        'success': True,
        'message': f'Started calling {len(numbers)} numbers',
        'results': results
    })

@app.route('/api/call-status')
def call_status():
    status_list = []
    for call_id, call_data in active_calls.items():
        status_list.append({
            'call_id': call_id,
            'number': call_data['number'],
            'status': call_data['status'],
            'start_time': call_data['start_time']
        })
    return jsonify({'calls': status_list, 'total': len(status_list)})

@app.route('/results')
def results_page():
    return render_template('results.html')

@app.route('/api/results')
def api_results():
    results = []
    if os.path.exists('results.tsv'):
        with open('results.tsv', 'r', newline='') as f:
            reader = csv.reader(f, delimiter='\t')
            for row in reader:
                if len(row) >= 4:
                    results.append({
                        'from_number': row[0],
                        'to_number': row[1],
                        'transcription': row[2],
                        'duration': row[3]
                    })
    return jsonify({'results': results})

@app.route('/api/download-results')
def download_results():
    if os.path.exists('results.tsv'):
        return send_file('results.tsv', as_attachment=True, download_name='results.tsv')
    return jsonify({'error': 'No results file found'}), 404

@app.route('/transcriber')
def transcriber_page():
    return render_template('transcriber.html')

@app.route('/api/transcribe', methods=['POST'])
def api_transcribe():
    if 'audio_files' not in request.files:
        return jsonify({'success': False, 'error': 'No files uploaded'})
    
    files = request.files.getlist('audio_files')
    if not files:
        return jsonify({'success': False, 'error': 'No files selected'})
    
    results = []
    for file in files:
        if file.filename:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Transcribe the file
            result = transcribe_audio_file(filepath, filename)
            results.append(result)
            
            # Clean up uploaded file
            try:
                os.remove(filepath)
            except (OSError, FileNotFoundError) as e:
                logging.warning(f"Could not remove temporary file {filepath}: {e}")
    
    # Save results to TSV
    if results:
        with open('transcriptions.tsv', 'a', newline='') as f:
            writer = csv.writer(f, delimiter='\t')
            for result in results:
                if result['success']:
                    writer.writerow([result['filename'], result['transcription']])
    
    return jsonify({'success': True, 'results': results})

@app.route('/api/transcriptions')
def api_transcriptions():
    results = []
    if os.path.exists('transcriptions.tsv'):
        with open('transcriptions.tsv', 'r', newline='') as f:
            reader = csv.reader(f, delimiter='\t')
            for row in reader:
                if len(row) >= 2:
                    results.append({
                        'filename': row[0],
                        'transcription': row[1]
                    })
    return jsonify({'results': results})

@app.route('/api/download-transcriptions')
def download_transcriptions():
    if os.path.exists('transcriptions.tsv'):
        return send_file('transcriptions.tsv', as_attachment=True, download_name='transcriptions.tsv')
    return jsonify({'error': 'No transcriptions file found'}), 404

# Webhook routes (from original run.py)
@app.route("/webhook", methods=["POST"])
def webhook_received():
    data = request.json
    event_type = data.get('data', {}).get('event_type')
    
    logging.info(f"Received {event_type} event")
    
    if event_type == "call.initiated":
        pass
    elif event_type == "call.answered":
        call_control_id = data.get('data', {}).get('payload', {}).get('call_control_id')
        if call_control_id in active_calls:
            active_calls[call_control_id]['status'] = 'answered'
            try:
                call = active_calls[call_control_id]['call']
                if app_config.get('audio_url'):
                    call.playback_start(audio_url=app_config['audio_url'])
                call.record_start(format="mp3", channels="single")
            except Exception as e:
                logging.error(f"Error handling answered call: {str(e)}")
    elif event_type == "call.hangup":
        call_control_id = data.get('data', {}).get('payload', {}).get('call_control_id')
        if call_control_id in active_calls:
            active_calls[call_control_id]['status'] = 'completed'
    
    return '', 200

@app.route("/webhook/call-recording-saved", methods=["POST"])
def call_recording_saved():
    data = request.json
    call_control_id = data.get('data', {}).get('payload', {}).get('call_control_id')
    recording_url = data.get('data', {}).get('payload', {}).get('public_recording_urls', {}).get('mp3')
    
    if call_control_id in active_calls:
        try:
            call_data = active_calls[call_control_id]
            call = call_data['call']
            
            logging.info(f"Transcribing call {call_control_id}...")
            
            # Download and transcribe audio file
            import requests
            audio_file = requests.get(recording_url, stream=True).raw
            transcript = openai.Audio.transcribe("whisper-1", audio_file)
            
            # Write result to TSV file
            with open('results.tsv', 'a', newline='') as f_output:
                tsv_output = csv.writer(f_output, delimiter='\t')
                tsv_output.writerow([
                    call.from_,
                    call.to,
                    transcript['text'],
                    getattr(call, 'call_duration', 'N/A')
                ])
            
            del active_calls[call_control_id]
        except Exception as e:
            logging.error(f"Error processing recording: {str(e)}")
    
    return '', 200

if __name__ == "__main__":
    # Get debug mode from environment, default to False for production safety
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() in ('true', '1', 'yes')
    app.run(host='0.0.0.0', port=5000, debug=debug_mode)
