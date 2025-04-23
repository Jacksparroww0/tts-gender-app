# Text-to-Speech Dialogue Application

This is a web application that converts dialogues to speech using gender-specific voices. The application detects the gender of each speaker in a dialogue and uses the appropriate voice to generate audio.

## Features

- Gender detection for speakers in dialogues
- Text-to-speech conversion with Edge TTS
- Male and female voice differentiation
- Audio generation for individual dialogue lines
- Combined audio file for the complete dialogue
- Automatic playback of dialogues
- Download options for generated audio
- Responsive web interface with dark mode support

## Technical Stack

- **Backend**: Flask (Python)
- **Text-to-Speech**: Edge TTS
- **Gender Detection**: gender-guesser
- **Audio Processing**: pydub, ffmpeg
- **Frontend**: HTML, CSS, JavaScript, Bootstrap 5

## Installation

1. Clone the repository:

   ```
   git clone https://github.com/your-username/tts-gender-app.git
   cd tts-gender-app
   ```

2. Create a virtual environment and activate it:

   ```
   python -m venv .venv
   # Windows
   .venv\Scripts\activate
   # Linux/Mac
   source .venv/bin/activate
   ```

3. Install dependencies:

   ```
   pip install -r requirements.txt
   ```

4. Install FFmpeg (required for audio processing):

   - Windows: Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH
   - Linux: `sudo apt-get install ffmpeg`
   - Mac: `brew install ffmpeg`

5. Run the application:

   ```
   python app.py
   ```

6. Open your browser and navigate to:
   ```
   http://127.0.0.1:8080
   ```

## Usage

1. Enter your dialogue text in the format:

   ```
   Name: Dialogue text
   Another Name: Response text
   ```

2. Click "Start Speech" button
3. The application will automatically:
   - Detect gender for each speaker
   - Generate audio files with appropriate voices
   - Merge them into a single audio file
   - Play the audio automatically

## Example Dialogue Format

```
Markus: Hallo, hier ist Markus aus dem Vertrieb.
Lisa: Ja, hallo Markus! Hier ist Lisa vom IT-Support.
```

## License

MIT

## Credits

- German voices provided by Microsoft Edge TTS
- Gender detection powered by gender-guesser

## GitHub Repository

To push your local repository to GitHub, use the following commands:

```
git remote add origin https://github.com/Jacksparroww0/tts-gender-app.git
git branch -M main
git push -u origin main
```
