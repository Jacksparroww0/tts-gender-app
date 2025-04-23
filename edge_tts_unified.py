"""
Edge-TTS ile SSML kullanarak birleştirilmiş diyalog oluşturan test script.
Ses dosyası uploads klasörüne kaydedilir.
"""

import asyncio
import edge_tts
import os
import uuid

# Uploads klasörünü kontrol et ve oluştur
os.makedirs('uploads', exist_ok=True)

# Ses ayarları
VOICES = {
    "male": "de-DE-ConradNeural",  # Almanca erkek sesi
    "female": "de-DE-KatjaNeural",  # Almanca kadın sesi
}

# Test diyalogları
TEST_DIALOGUES = [
    {"speaker": "Thomas", "text": "Hallo, wie geht es dir?", "gender": "male"},
    {"speaker": "Anna", "text": "Mir geht es gut, danke! Und dir?", "gender": "female"},
    {"speaker": "Thomas", "text": "Auch gut, danke. Was machst du heute?", "gender": "male"},
    {"speaker": "Anna", "text": "Ich gehe ins Kino. Willst du mitkommen?", "gender": "female"},
    {"speaker": "Thomas", "text": "Ja, sehr gerne! Welchen Film schauen wir an?", "gender": "male"},
]

async def create_unified_audio():
    """
    Tüm diyalogları SSML kullanarak tek bir ses dosyasında birleştirir.
    """
    # Benzersiz dosya adı oluştur
    session_id = str(uuid.uuid4())
    output_file = os.path.join('uploads', f'{session_id}_unified.mp3')
    
    try:
        # SSML metnini oluştur
        ssml = "<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='de-DE'>"
        
        for i, dialogue in enumerate(TEST_DIALOGUES):
            voice = VOICES.get(dialogue["gender"], VOICES["female"])
            speaker = dialogue["speaker"]
            text = dialogue["text"]
            
            # Her diyalog için ayrı ses kullan
            ssml += f'<voice name="{voice}">{speaker}: {text}</voice>'
            
            # Son diyalog değilse durak ekle
            if i < len(TEST_DIALOGUES) - 1:
                ssml += '<break time="500ms"/>'
        
        ssml += "</speak>"
        
        print(f"SSML Metni: {ssml}")
        
        # Edge-TTS ile ses oluştur
        communicator = edge_tts.Communicate(text=ssml, voice=VOICES["male"])
        await communicator.save(output_file)
        
        print(f"Birleştirilmiş ses dosyası oluşturuldu: {output_file}")
        return output_file
    except Exception as e:
        print(f"Hata: {str(e)}")
        return None

# Ana işlev
async def main():
    file_path = await create_unified_audio()
    if file_path:
        print(f"Dosya oluşturuldu: {file_path}")
        print("Doğrulama: MP3 oynatıcı ile dosyayı çalarak farklı sesleri duyabilirsiniz.")
    else:
        print("Birleştirilmiş ses dosyası oluşturulamadı!")

# Çalıştır
if __name__ == "__main__":
    asyncio.run(main()) 