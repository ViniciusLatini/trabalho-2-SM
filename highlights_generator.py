import cv2
import pytesseract
import subprocess
import os

VIDEO_PATH = 'video.mp4'

PLAYER_NAME = 'donk'

KILLFEED_REGION = (1050, 100, 220, 150) 

CLIP_DURATION = 10 


def detect_kill_events(video_path, player_name):
    print("Iniciando a análise do vídeo. Isso pode demorar...")
    cap = cv2.VideoCapture(video_path)
    
    video_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    video_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Calcula a região do canto superior direito
    x = int(video_width * 0.80)
    y = int(video_height * 0.10) 
    w = int(video_width * 0.19)  
    h = int(video_height * 0.25) 
    
    killfeed_region = (x, y, w, h)
    print(f"Vídeo de {video_width}x{video_height}. Região de análise definida para: {killfeed_region}")
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    kill_timestamps = []
    last_kill_time = -10  # Cooldown para evitar detecções duplicadas do mesmo evento

    frame_count = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        if frame_count % int(fps) == 0:
            current_time_sec = frame_count / fps
            
            # Recorta a região do feed de eliminações
            x, y, w, h = killfeed_region
            killfeed_frame = frame[y:y+h, x:x+w]
            
            # Pré-processamento da imagem para melhorar a leitura do OCR
            gray_frame = cv2.cvtColor(killfeed_frame, cv2.COLOR_BGR2GRAY)
            
            try:
                text = pytesseract.image_to_string(gray_frame)
                formatted_time = f"{int(current_time_sec // 3600):02d}:{int((current_time_sec % 3600) // 60):02d}:{int(current_time_sec % 60):02d}"
                print(f"({formatted_time}): {text.strip()}")
                # Verifica se o nome do jogador está no texto do feed
                if player_name in text:
                    print(f"Texto detectado no feed: {text.strip()}")
                    # Evita detectar o mesmo kill várias vezes seguidas
                    if current_time_sec > last_kill_time + 5:
                        print(f"Evento detectado! {player_name} em {current_time_sec:.2f} segundos.")
                        kill_timestamps.append(current_time_sec)
                        last_kill_time = current_time_sec

            except Exception as e:
                pass

        frame_count += 1
        
    cap.release()
    print(f"Análise concluída. {len(kill_timestamps)} eventos encontrados.")
    return kill_timestamps

def create_clips_from_timestamps(video_path, timestamps, duration):
    if not timestamps:
        print("Nenhum evento para criar clipes.")
        return []

    print("Criando clipes individuais...")
    clip_files = []
    for i, ts in enumerate(timestamps):
        start_time = max(0, ts - duration / 2) # Começa X segundos antes
        output_filename = f"temp_clip_{i}.mp4"
        
        # cortar o video com ffmpeg
        command = [
            'ffmpeg',
            '-y',
            '-ss', str(start_time),
            '-i', video_path,
            '-t', str(duration),
            '-c', 'copy',
            output_filename
        ]
        
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        clip_files.append(output_filename)
        
    print(f"{len(clip_files)} clipes criados.")
    return clip_files

def concatenate_clips(clip_files, output_filename):
    if not clip_files:
        return

    print("Juntando os clipes no vídeo final...")
    # Cria um arquivo de texto temporário com a lista de clipes
    with open("mylist.txt", "w") as f:
        for clip in clip_files:
            f.write(f"file '{clip}'\n")

    # concatena clips com ffmpeg
    command = [
        'ffmpeg',
        '-y',
        '-f', 'concat',
        '-safe', '0',
        '-i', 'mylist.txt',
        '-c', 'copy',
        output_filename
    ]
    
    subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"Vídeo final '{output_filename}' criado com sucesso!")

def cleanup(files):
    print("Limpando arquivos temporários...")
    for f in files:
        if os.path.exists(f):
            os.remove(f)
    if os.path.exists("mylist.txt"):
        os.remove("mylist.txt")

if __name__ == "__main__":
    # 1. Detecta os eventos no vídeo
    timestamps = detect_kill_events(VIDEO_PATH, PLAYER_NAME)
    
    if timestamps:
        # 2. Cria os clipes individuais a partir dos timestamps
        clips = create_clips_from_timestamps(VIDEO_PATH, timestamps, CLIP_DURATION)
        
        # 3. Junta os clipes em um único vídeo
        concatenate_clips(clips, "melhores_momentos.mp4")
        
        # 4. Limpa os arquivos temporários
        cleanup(clips)