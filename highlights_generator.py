import cv2
import pytesseract
import subprocess
import os
import shutil

# --- ATENÇÃO: SUBSTITUA ESTE CAMINHO PELO SEU CAMINHO REAL DO TESSERACT OCR NO WINDOWS ---
# Exemplo: r'C:\Program Files\Tesseract-OCR\tesseract.exe'
# Este caminho é CRÍTICO para o funcionamento do OCR no Windows
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def detect_kill_events(video_path, player_name):
    """
    Detecta eventos de kill no vídeo usando OCR na região do killfeed.
    Retorna uma lista de timestamps (segundos) onde os eventos foram detectados.
    """
    print(f"Iniciando a análise do vídeo '{video_path}'. Isso pode demorar...")
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        print(f"Erro: Não foi possível abrir o vídeo em {video_path}")
        return []

    video_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    video_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Calcula a região do canto superior direito (killfeed)
    x = int(video_width * 0.80)
    y = int(video_height * 0.10)
    w = int(video_width * 0.19)
    h = int(video_height * 0.25)
    
    killfeed_region = (x, y, w, h)
    print(f"Vídeo de {video_width}x{video_height}. Região de análise definida para: {killfeed_region}")
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps == 0:
        print("Erro: FPS do vídeo é 0. Não é possível processar.")
        cap.release()
        return []

    kill_timestamps = []
    last_kill_time = -10  # Cooldown para evitar detecções duplicadas do mesmo evento (5 segundos)

    frame_count = 0
    frames_to_skip = max(1, int(fps / 2)) 

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        if frame_count % frames_to_skip == 0:
            current_time_sec = frame_count / fps
            
            x_kf, y_kf, w_kf, h_kf = killfeed_region
            killfeed_frame = frame[y_kf:y_kf+h_kf, x_kf:x_kf+w_kf]
            
            gray_frame = cv2.cvtColor(killfeed_frame, cv2.COLOR_BGR2GRAY)
            _, thresh_frame = cv2.threshold(gray_frame, 150, 255, cv2.THRESH_BINARY_INV) 
            
            try:
                custom_config = r'--oem 3 --psm 6' 
                text = pytesseract.image_to_string(thresh_frame, config=custom_config)
                
                formatted_time = f"{int(current_time_sec // 3600):02d}:{int((current_time_sec % 3600) // 60):02d}:{int(current_time_sec % 60):02d}"
                # print(f"({formatted_time}): {text.strip()}") # Descomente para depurar o texto lido

                if player_name.lower() in text.lower():
                    print(f"Texto detectado no feed: {text.strip()}")
                    if current_time_sec > last_kill_time + 5: 
                        print(f"Evento detectado! {player_name} em {current_time_sec:.2f} segundos.")
                        kill_timestamps.append(current_time_sec)
                        last_kill_time = current_time_sec

            except Exception as e:
                # print(f"Erro no OCR em {formatted_time}: {e}")
                pass

        frame_count += 1
        
    cap.release()
    print(f"Análise concluída. {len(kill_timestamps)} eventos encontrados.")
    return kill_timestamps

def create_clips_from_timestamps(video_path, timestamps, duration, output_temp_dir):
    """
    Cria clipes de vídeo individuais a partir de timestamps usando FFmpeg.
    Salva os clipes em um diretório temporário.
    """
    if not timestamps:
        print("Nenhum evento para criar clipes.")
        return []

    print("Criando clipes individuais...")
    os.makedirs(output_temp_dir, exist_ok=True)
    clip_files = []
    for i, ts in enumerate(timestamps):
        start_time = max(0, ts - duration / 2) 
        output_filename = os.path.join(output_temp_dir, f"temp_clip_{i}.mp4")
        
        command = [
            'ffmpeg',
            '-y', 
            '-ss', str(start_time), 
            '-i', video_path, 
            '-t', str(duration), 
            '-c', 'copy', 
            output_filename
        ]
        
        try:
            subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            clip_files.append(output_filename)
        except subprocess.CalledProcessError as e:
            print(f"Erro ao criar clipe {output_filename}: {e}")
            continue 
        
    print(f"{len(clip_files)} clipes criados.")
    return clip_files

def concatenate_clips(clip_files, output_final_path):
    """
    Concatena múltiplos clipes de vídeo em um único arquivo usando FFmpeg.
    """
    if not clip_files:
        print("Nenhum clipe para concatenar.")
        return

    print("Juntando os clipes no vídeo final...")
    
    mylist_path = os.path.join(os.path.dirname(clip_files[0]), "mylist.txt") if clip_files else "mylist.txt"
    with open(mylist_path, "w") as f:
        for clip in clip_files:
            f.write(f"file '{os.path.basename(clip)}'\n")

    command = [
        'ffmpeg',
        '-y',
        '-f', 'concat', 
        '-safe', '0', 
        '-i', mylist_path, 
        '-c', 'copy', 
        output_final_path 
    ]
    
    try:
        original_cwd = os.getcwd()
        os.chdir(os.path.dirname(mylist_path))
        
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"Vídeo final '{output_final_path}' criado com sucesso!")
    except subprocess.CalledProcessError as e:
        print(f"Erro ao concatenar clipes: {e}")
    finally:
        os.chdir(original_cwd) 
        if os.path.exists(mylist_path):
            os.remove(mylist_path) 

def convert_to_dash(input_mp4_path, output_dash_dir):
    """
    Converte um arquivo MP4 em formato DASH (fragmented MP4 segments e MPD manifest).
    Para simplicidade, gera uma única representação (qualidade).
    """
    print(f"Convertendo '{input_mp4_path}' para DASH na pasta '{output_dash_dir}'...")
    os.makedirs(output_dash_dir, exist_ok=True)
    
    # O nome do MPD será apenas 'master.mpd' quando estivermos dentro de 'output_dash_dir'
    output_mpd_filename = 'master.mpd'
    # O caminho completo para o MPD para retorno e referência
    full_output_mpd_path = os.path.join(output_dash_dir, output_mpd_filename)
    
    command = [
        'ffmpeg',
        '-i', input_mp4_path,
        '-f', 'dash',
        '-map', '0:v', '-map', '0:a?', # Adicionado '?' para tornar o áudio opcional
        '-c:v', 'libx264', '-preset', 'medium', '-crf', '23', 
        '-c:a', 'aac', '-b:a', '128k', 
        '-adaptation_sets', 'id=0,streams=v id=1,streams=a',
        '-seg_duration', '4', 
        '-dash_segment_type', 'mp4',
        '-use_template', '1',
        '-use_timeline', '1',
        '-init_seg_name', 'init-$RepresentationID$.m4s',
        '-media_seg_name', 'segment-$RepresentationID$-$Number%05d$.m4s',
        output_mpd_filename # Usamos apenas o nome do arquivo aqui
    ]

    print(f"\n--- DEBUG FFmpeg: Comando a ser executado ---\n{' '.join(command)}\n--- FIM DEBUG ---\n")
    
    original_cwd = os.getcwd()
    try:
        # Muda o diretório de trabalho para a pasta onde os arquivos DASH devem ser criados
        os.chdir(output_dash_dir)
        print(f"Diretório de trabalho atual alterado para: {os.getcwd()}")
        
        # Executa o comando FFmpeg no novo diretório de trabalho
        subprocess.run(command, check=True) 
        print(f"Conversão para DASH concluída. Manifest em: {full_output_mpd_path}")
        return full_output_mpd_path
    except subprocess.CalledProcessError as e:
        print(f"Erro ao converter para DASH: {e}")
        return None
    finally:
        # Restaura o diretório de trabalho original
        os.chdir(original_cwd)
        print(f"Diretório de trabalho restaurado para: {os.getcwd()}")


def cleanup(files_or_dirs):
    """
    Limpa arquivos e diretórios temporários.
    """
    print("Limpando arquivos temporários...")
    for item in files_or_dirs:
        if os.path.exists(item):
            if os.path.isfile(item):
                os.remove(item)
            elif os.path.isdir(item):
                shutil.rmtree(item) 
    print("Limpeza concluída.")

def generate_highlights(video_input_path, player_name, clip_duration, task_id, dash_base_output_dir):
    """
    Função principal que orquestra a detecção de highlights, criação de clipes,
    concatenação e conversão para DASH.
    Retorna o caminho relativo para o arquivo DASH master.mpd.
    """
    concatenated_mp4_filename = f"concatenated_highlights_{task_id}.mp4"
    # Usamos os.path.join para garantir o caminho completo para o arquivo MP4 concatenado
    # na pasta do projeto principal, antes de passar para a conversão DASH.
    concatenated_mp4_path = os.path.join(os.getcwd(), concatenated_mp4_filename)

    temp_clips_dir = os.path.join(os.getcwd(), f"temp_clips_{task_id}")

    # Define o diretório de saída para os arquivos DASH para esta tarefa específica
    dash_output_task_dir = os.path.join(dash_base_output_dir, task_id)

    try:
        timestamps = detect_kill_events(video_input_path, player_name)
        
        if not timestamps:
            print("Nenhum evento para criar clipes. Retornando None.")
            return None

        clips = create_clips_from_timestamps(video_input_path, timestamps, clip_duration, temp_clips_dir)
        
        if not clips:
            print("Nenhum clipe foi gerado. Retornando None.")
            return None

        concatenate_clips(clips, concatenated_mp4_path)

        if not os.path.exists(concatenated_mp4_path):
            print("Erro: Vídeo concatenado MP4 não foi criado.")
            return None
        
        # Converte para DASH; a função agora garante que os arquivos estão na pasta correta
        dash_manifest_path_abs = convert_to_dash(concatenated_mp4_path, dash_output_task_dir)

        if not dash_manifest_path_abs:
            print("Erro: Conversão para DASH falhou.")
            return None
        
        # Retorna o caminho RELATIVO ao diretório dash_base_output_dir
        # Ex: "TASK_ID/master.mpd"
        # O basename de dash_manifest_path_abs é "master.mpd"
        return os.path.join(task_id, os.path.basename(dash_manifest_path_abs))
    
    except Exception as e:
        print(f"Erro geral na geração de highlights: {e}")
        return None
    finally:
        temp_files_to_clean = [
            concatenated_mp4_path, 
            temp_clips_dir         
        ]
        cleanup(temp_files_to_clean) 

if __name__ == "__main__":
    print("Iniciando teste local do highlight_generator.py (com DASH)...")
    test_video_path = 'video.mp4' 
    test_player_name = 'donk' 
    test_clip_duration = 10
    test_task_id = 'local_test_dash' 
    test_dash_base_output = 'dash_output' 

    if os.path.exists(test_video_path):
        os.makedirs(test_dash_base_output, exist_ok=True) 
        relative_dash_manifest = generate_highlights(
            test_video_path, test_player_name, test_clip_duration, test_task_id, test_dash_base_output
        )
        if relative_dash_manifest:
            print(f"Teste local concluído. Manifest DASH em: {os.path.join(test_dash_base_output, relative_dash_manifest)}")
        else:
            print("Teste local concluído, mas nenhum destaque DASH foi gerado.")
    else:
        print(f"Erro: O arquivo de vídeo de teste '{test_video_path}' não foi encontrado.")
        print("Por favor, coloque um 'video.mp4' na raiz do projeto para o teste.")
