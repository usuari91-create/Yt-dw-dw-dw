from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from yt_dlp import YoutubeDL
import tempfile
import os
import uuid
import shutil

app = Flask(__name__)
CORS(app) # ¡CRUCIAL! Permite que tu web de Netlify se conecte a este servidor

@app.route('/api/download', methods=['POST'])
def download():
    data = request.json
    url = data.get('url')
    format_type = data.get('format') # 'video' o 'audio'

    if not url:
        return jsonify({'error': 'URL requerida'}), 400

    # Creamos una carpeta temporal única para esta descarga
    temp_dir = tempfile.mkdtemp()
    safe_id = str(uuid.uuid4())
    output_template = os.path.join(temp_dir, f"{safe_id}.%(ext)s")

    ydl_opts = {
        'outtmpl': output_template,
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
    }

    if format_type == 'audio':
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
    else:
        ydl_opts['format'] = 'bestvideo+bestaudio/best'
        ydl_opts['merge_output_format'] = 'mp4'

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            # Si es audio, la extensión final será .mp3
            if format_type == 'audio':
                filename = filename.rsplit('.', 1)[0] + '.mp3'

            title = info.get('title', 'descarga').replace('/', '-').replace('\\', '-')
            ext = filename.split('.')[-1]
            
            # Enviamos el archivo al navegador del usuario
            return send_file(
                filename, 
                as_attachment=True, 
                download_name=f"{title}.{ext}"
            )
    except Exception as e:
        return jsonify({'error': f"Error al procesar: {str(e)}"}), 500
    finally:
        # Limpiamos la carpeta temporal para no llenar el servidor
        shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))