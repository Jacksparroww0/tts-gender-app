from flask import Flask, render_template, request, jsonify, send_file
import os
import re
import uuid
import json
import gender_guesser.detector as gender
import asyncio
import edge_tts
import io
import tempfile
import wave
import time
from pydub import AudioSegment
import shutil  # Dosya işlemleri için gerekli
import datetime

app = Flask(__name__)

# uploads klasörünü oluştur
os.makedirs('uploads', exist_ok=True)

# Cinsiyet dedektörünü başlat
gender_detector = gender.Detector(case_sensitive=False)

# Bilinen isimler için cinsiyet belirlemeleri - Sorunlu isimler için manuel cinsiyet atama
KNOWN_GENDERS = {
    "markus": "male",
    "lisa": "female",
    "julia": "female",
    "thomas": "male",
    "anna": "female",
    "michael": "male",
    "sabine": "female",
    "stefan": "male",
    "hannah": "female",
    "peter": "male",
    "maria": "female",
    "klaus": "male",
    "monika": "female",
    "andreas": "male",
    "sandra": "female",
    "martin": "male",
    "christin": "female",
    "christian": "male",
    "brigitte": "female",
    "frank": "male",
    "susanne": "female",
    "oliver": "male",
    "nicole": "female"
}

# Cinsiyete göre sesler (Almanca sesleri kullan)
VOICES = {
    "male": "de-DE-ConradNeural", # Almanca erkek sesi
    "female": "de-DE-KatjaNeural", # Almanca kadın sesi
    "unknown": "de-DE-KatjaNeural"  # Varsayılan
}

def get_gender(name):
    """
    İsme göre cinsiyet tahmini yapar.
    Önce bilinen isimler listesinde kontrol eder, bulamazsa gender-guesser kullanır.
    """
    # İlk adı al (birden fazla isim varsa)
    first_name = name.split()[0].lower()
    
    # Önce bilinen isimler listesinde ara
    if first_name in KNOWN_GENDERS:
        return KNOWN_GENDERS[first_name]
    
    # Bilinen isimler listesinde yoksa gender-guesser ile tahmin et
    gender_guess = gender_detector.get_gender(first_name)
    
    # Sonuçları basitleştir
    if gender_guess in ['male', 'mostly_male']:
        return 'male'
    elif gender_guess in ['female', 'mostly_female']:
        return 'female'
    else:
        # Belirsizse cinsiyetine güvenilen bir karakter varsayılan değer olarak kullan
        return 'unknown'

def parse_dialogue(text):
    """
    Diyalog metnini analiz ederek konuşmacıları ve mesajlarını ayırır.
    """
    dialogues = []
    lines = text.strip().split('\n')
    
    for line in lines:
        # "İsim: Mesaj" formatında mı kontrol et
        match = re.match(r'^([^:]+):\s*(.+)$', line.strip())
        if match:
            speaker = match.group(1).strip()
            message = match.group(2).strip()
            
            # Cinsiyet tahmin et
            gender = get_gender(speaker)
            
            dialogues.append({
                "speaker": speaker,
                "text": message,
                "gender": gender
            })
    
    return dialogues

async def text_to_speech_edge(text, gender, output_file):
    """
    Edge TTS kullanarak metni sese çevirir ve belirtilen dosyaya kaydeder.
    """
    try:
        # Cinsiyete göre ses belirle (Almanca)
        voice = VOICES.get(gender, VOICES["unknown"])
        
        # Edge TTS ile seslendirme yap
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_file)
        return True
    except Exception as e:
        print(f"Edge TTS hatası: {e}")
        return False

async def generate_audio_for_dialogues(dialogues, session_id):
    """
    Her diyalog için cinsiyete uygun sesle ses dosyası oluşturur.
    Ayrıca tüm diyalogları tek bir ses dosyasında birleştirir.
    """
    try:
        # Her diyalog için ayrı ses dosyası oluştur
        audio_files = []
        individual_files = []
        
        # Önce tüm diyaloglar için ses dosyalarını oluştur
        for i, dialogue in enumerate(dialogues):
            try:
                # Sadece diyalog metnini kullan (konuşmacı ismi olmadan)
                text_to_speak = dialogue['text']
                output_file = os.path.join('uploads', f'{session_id}_{i}.mp3')
                
                # Edge TTS ile cinsiyete uygun sesle seslendirme yap
                await text_to_speech_edge(text_to_speak, dialogue['gender'], output_file)
                
                # Dosya başarıyla oluşturulduysa ve boyutu sıfırdan büyükse listeye ekle
                if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                    audio_files.append(output_file)
                    individual_file_name = f'{session_id}_{i}.mp3'
                    individual_files.append(individual_file_name)
                    print(f"Ses dosyası oluşturuldu: {output_file} - Boyut: {os.path.getsize(output_file)} bytes")
                else:
                    print(f"Uyarı: Ses dosyası oluşturulamadı veya dosya boş: {output_file}")
            except Exception as e:
                print(f"Ses oluşturma hatası (diyalog {i}): {e}")
        
        # Oluşturulan ses dosyalarının bir listesini dosyaya kaydet
        audio_list_file = os.path.join('uploads', f'{session_id}_audio_list.json')
        with open(audio_list_file, 'w', encoding='utf-8') as f:
            json.dump({
                "audio_files": individual_files,
                "session_id": session_id,
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }, f, ensure_ascii=False, indent=4)
        
        # Tüm diyalogları tek bir dosyada birleştir (AudioSegment ile)
        combined_output = os.path.join('uploads', f'{session_id}_combined.mp3')
        try:
            # AudioSegment ile birleştir
            combined = AudioSegment.empty()
            silence = AudioSegment.silent(duration=500)  # 500ms sessizlik
            
            if len(audio_files) > 0:
                for audio_file in audio_files:
                    try:
                        if os.path.exists(audio_file) and os.path.getsize(audio_file) > 0:
                            segment = AudioSegment.from_file(audio_file)
                            combined += segment + silence
                        else:
                            print(f"Ses dosyası birleştirilemedi (dosya yok veya boş): {audio_file}")
                    except Exception as e:
                        print(f"Ses dosyası birleştirme hatası ({audio_file}): {e}")
                        continue
                
                # Boş değilse kaydet
                if len(combined) > 0:
                    # MP3 olarak dışa aktar
                    combined.export(combined_output, format="mp3")
                    
                    # Birleştirilmiş dosyayı dosya listesinin başına ekle
                    combined_filename = f'{session_id}_combined.mp3'
                    if os.path.exists(combined_output) and os.path.getsize(combined_output) > 0:
                        individual_files.insert(0, combined_filename)
                        print(f"Birleştirilmiş ses dosyası oluşturuldu: {combined_output} - Boyut: {os.path.getsize(combined_output)} bytes")
                    else:
                        print(f"Uyarı: Birleştirilmiş ses dosyası oluşturulamadı veya dosya boş: {combined_output}")
                else:
                    print("Uyarı: Birleştirilecek ses verisi bulunamadı")
            else:
                print("Uyarı: Birleştirilecek ses dosyası bulunamadı")
                
            # Diyalog bilgilerini kaydet
            recording_info = {
                "session_id": session_id,
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "filename": combined_filename,
                "dialogues": dialogues,
                "audio_files": individual_files
            }
            
            # JSON bilgilerini kaydet
            info_file = os.path.join('uploads', f'{session_id}_info.json')
            with open(info_file, 'w', encoding='utf-8') as f:
                json.dump(recording_info, f, ensure_ascii=False, indent=4)
                
        except Exception as e:
            print(f"Diyalog birleştirme hatası: {e}")
        
        # Oluşturulan ses dosyalarını döndür
        return individual_files if individual_files else None
        
    except Exception as e:
        print(f"Genel ses oluşturma hatası: {e}")
        return None

def run_async(coro):
    """
    Asenkron fonksiyonu senkron çağırır
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/recordings')
def list_recordings():
    """
    Tüm ses kayıtlarını listeleyen sayfa
    """
    recordings = []
    
    # uploads dizinindeki tüm dosyaları tara
    try:
        for filename in os.listdir('uploads'):
            # Sadece _combined.mp3 ile biten dosyaları al
            if filename.endswith('_combined.mp3'):
                session_id = filename.split('_combined.mp3')[0]
                info_path = os.path.join('uploads', f'{session_id}_info.json')
                
                # Dosya bilgilerinin alınması
                file_path = os.path.join('uploads', filename)
                file_exists = os.path.exists(file_path)
                file_size = os.path.getsize(file_path) if file_exists else 0
                
                # Dosya çok küçükse muhtemelen boştur, atla
                if file_size < 1000:  # 1 KB'dan küçük dosyaları atla
                    continue
                
                recording_data = {
                    "session_id": session_id,
                    "filename": filename,
                    "audio_url": f'/audio/{filename}',
                    "timestamp": "",
                    "dialogues": [],
                    "audio_files": []
                }
                
                # Eğer bilgi dosyası varsa, detayları ekle
                if os.path.exists(info_path):
                    try:
                        with open(info_path, 'r', encoding='utf-8') as f:
                            info = json.load(f)
                            recording_data["timestamp"] = info.get("timestamp", "")
                            recording_data["dialogues"] = info.get("dialogues", [])
                            recording_data["audio_files"] = info.get("audio_files", [])
                    except Exception as e:
                        print(f"Bilgi dosyası okuma hatası: {e}")
                
                # Timestamp yoksa dosya değiştirilme tarihini kullan
                if not recording_data["timestamp"]:
                    try:
                        file_mtime = os.path.getmtime(os.path.join('uploads', filename))
                        recording_data["timestamp"] = datetime.datetime.fromtimestamp(file_mtime).strftime("%Y-%m-%d %H:%M:%S")
                    except Exception as e:
                        print(f"Dosya tarihi hatası: {e}")
                        recording_data["timestamp"] = "Bilinmiyor"
                
                recordings.append(recording_data)
        
        # Tarihe göre sırala, en yeni başta
        recordings.sort(key=lambda x: x["timestamp"], reverse=True)
        
        print(f"Bulunan kayıt sayısı: {len(recordings)}")
    except Exception as e:
        print(f"Kayıtları listeleme hatası: {e}")
    
    # Debug için, hangi kayıtlar bulundu
    for i, rec in enumerate(recordings):
        print(f"Kayıt {i+1}: {rec['filename']} - {rec['timestamp']} - {len(rec['dialogues'])} diyalog, {len(rec['audio_files'])} ses dosyası")
    
    return render_template('recordings.html', recordings=recordings)

@app.route('/process', methods=['POST'])
def process_text():
    if 'text' not in request.form:
        return jsonify({"error": "No text provided"}), 400
    
    text = request.form['text']
    dialogues = parse_dialogue(text)
    
    # Diyalog yoksa hata mesajı ver
    if not dialogues:
        return jsonify({"error": "No valid dialogues found"}), 400
    
    # Benzersiz bir dosya adı oluştur
    session_id = str(uuid.uuid4())
    
    # Diyalogları dosyaya kaydet
    dialogue_file = os.path.join('uploads', f'dialogue_{session_id}.json')
    with open(dialogue_file, 'w', encoding='utf-8') as f:
        json.dump(dialogues, f, ensure_ascii=False)
    
    # Sesli anlatım oluştur (asenkron işlemi senkron olarak çağır)
    try:
        audio_files = run_async(generate_audio_for_dialogues(dialogues, session_id))
        
        return jsonify({
            "dialogues": dialogues,
            "session_id": session_id,
            "audio_files": audio_files
        })
        
    except Exception as e:
        print(f"Ses oluşturma hatası: {e}")
        return jsonify({
            "dialogues": dialogues,
            "session_id": session_id,
            "error": str(e)
        }), 500

@app.route('/audio/<filename>')
def serve_audio(filename):
    """
    Oluşturulan ses dosyalarını servis et
    """
    return send_file(os.path.join('uploads', filename))

if __name__ == '__main__':
    # Farklı bir port numarası (8080) ve host (0.0.0.0) kullanarak dış bağlantılara açık hale getir
    app.run(debug=True, host='0.0.0.0', port=8080) 