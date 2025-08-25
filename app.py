from flask import Flask, render_template, request, jsonify, send_file
import os
import threading
from highlights_generator import generate_highlights
import time # Para simular o tempo de processamento

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'

# Garante que o diretório de uploads existe
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Dicionário para rastrear o status de cada trabalho (processo de geração)
processing_status = {}

@app.route('/')
def index():
    return render_template('index.html')

def process_video_task(file_path, player_name, task_id):
    """Função que roda em segundo plano para processar o vídeo."""
    try:
        # Simula um tempo de processamento para o loading screen
        time.sleep(3) 
        
        # Chama a função do seu script para gerar os destaques
        output_video_path = generate_highlights(file_path, player_name, 10) # 10s de duração do clipe
        
        if output_video_path:
            processing_status[task_id] = {'status': 'completed', 'video_path': output_video_path}
        else:
            processing_status[task_id] = {'status': 'failed', 'message': 'Nenhum destaque encontrado.'}
    except Exception as e:
        print(f"Erro no processamento: {e}")
        processing_status[task_id] = {'status': 'failed', 'message': f'Erro: {str(e)}'}
    finally:
        # Opcional: remover o arquivo original após o processamento
        if os.path.exists(file_path):
            os.remove(file_path)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'video' not in request.files:
        return jsonify({'success': False, 'message': 'Nenhum arquivo enviado'}), 400
    
    file = request.files['video']
    player_name = request.form.get('player_name')
    
    if file.filename == '' or not player_name:
        return jsonify({'success': False, 'message': 'Nome do jogador ou arquivo de vídeo faltando'}), 400

    filename = file.filename
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)
    
    # Gera um ID único para a tarefa
    task_id = os.urandom(16).hex()
    processing_status[task_id] = {'status': 'processing'}
    
    # Inicia o processamento do vídeo em uma thread separada para não travar a interface
    thread = threading.Thread(target=process_video_task, args=(file_path, player_name, task_id))
    thread.start()
    
    return jsonify({'success': True, 'task_id': task_id})

@app.route('/status/<task_id>')
def get_status(task_id):
    """Verifica o status de uma tarefa de processamento."""
    status = processing_status.get(task_id, {'status': 'not_found'})
    return jsonify(status)

@app.route('/highlights/<path:filename>')
def serve_highlights(filename):
    """Serve o vídeo de destaques para o usuário."""
    return send_file(filename, mimetype='video/mp4', as_attachment=False)

if __name__ == '__main__':
    app.run(debug=True)