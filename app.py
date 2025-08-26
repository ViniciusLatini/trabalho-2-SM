from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import threading
from highlights_generator import generate_highlights
import time
import shutil

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['DASH_OUTPUT_FOLDER'] = 'dash_output/'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['DASH_OUTPUT_FOLDER'], exist_ok=True)

processing_status = {}

@app.route('/')
def index():
    return render_template('index.html')

def process_video_task(file_path, player_name, task_id):
    """
    Função que roda em segundo plano para processar o vídeo,
    gerar highlights e convertê-los para DASH.
    """
    try:
        print(f"[{task_id}] Iniciando processamento do vídeo: {file_path}")
        dash_manifest_path = generate_highlights(
            video_input_path=file_path, 
            player_name=player_name, 
            clip_duration=10, 
            task_id=task_id,
            dash_base_output_dir=app.config['DASH_OUTPUT_FOLDER']
        )
        
        if dash_manifest_path:
            print(f"[{task_id}] Processamento DASH concluído. Manifest: {dash_manifest_path}")
            processing_status[task_id] = {'status': 'completed', 'dash_manifest_path': dash_manifest_path}
        else:
            print(f"[{task_id}] Processamento DASH falhou: Nenhum destaque encontrado ou erro.")
            processing_status[task_id] = {'status': 'failed', 'message': 'Nenhum destaque DASH encontrado ou erro durante a geração.'}
    except Exception as e:
        print(f"[{task_id}] Erro no processamento da tarefa: {e}")
        processing_status[task_id] = {'status': 'failed', 'message': f'Erro interno do servidor: {str(e)}'}
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"[{task_id}] Arquivo de upload original '{file_path}' removido.")

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'video' not in request.files:
        return jsonify({'success': False, 'message': 'Nenhum arquivo de vídeo enviado'}), 400
    
    file = request.files['video']
    player_name = request.form.get('player_name')
    
    if file.filename == '' or not player_name:
        return jsonify({'success': False, 'message': 'Nome do jogador ou arquivo de vídeo faltando'}), 400

    filename = file.filename
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)
    print(f"Arquivo '{filename}' salvo em '{file_path}'")
    
    task_id = os.urandom(16).hex()
    processing_status[task_id] = {'status': 'processing', 'message': 'Iniciando análise e conversão para DASH...'}
    
    thread = threading.Thread(target=process_video_task, args=(file_path, player_name, task_id))
    thread.start()
    
    return jsonify({'success': True, 'task_id': task_id})

@app.route('/status/<task_id>')
def get_status(task_id):
    status = processing_status.get(task_id, {'status': 'not_found', 'message': 'Tarefa não encontrada.'})
    return jsonify(status)

@app.route('/dash/<task_id>/<path:filename>')
def serve_dash_files(task_id, filename):
    directory = os.path.join(app.config['DASH_OUTPUT_FOLDER'], task_id)
    print(f"Servindo DASH: {filename} do diretório {directory}")
    return send_from_directory(directory, filename)

if __name__ == '__main__':
    app.run(debug=True)
