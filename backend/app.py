from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from os.path import join, exists
from shutil import rmtree

import os
from my_script import analizar_documento_pdf

app = Flask(__name__)
CORS(app, methods=["DELETE"])

@app.route('/api/delete/<path:filename>', methods=['DELETE'])
def delete_file(filename):
    filepath = join(filename.replace('/', os.sep))
    print(f'Ruta completa del archivo a eliminar: {filepath}')

    print(f'Contenido de filename: {filename}')

    if exists(filepath):

        try:
            os.remove(filepath)

            vista_previa_filepath = join('vistas_previas', f'{filename}.png')
            if exists(vista_previa_filepath):
                os.remove(vista_previa_filepath)

            return jsonify({'message': 'Archivo eliminado correctamente'})
        except Exception as e:
            return jsonify({'error': f'Error al eliminar el archivo: {str(e)}'}), 500
    else:
        return jsonify({'error': f'Archivo no encontrado: {filename}'}), 404

@app.route('/api/analyze', methods=['POST'])
def analyze_document():
    if 'document' not in request.files:
        return jsonify({'error': 'No se proporcionó un archivo'}), 400

    document = request.files['document']

    try:
        resultados = analizar_documento_pdf(document)
        print(f'Nombre del archivo resultante desde backend: {resultados}')
        return jsonify({'message': 'Análisis ortográfico completado', 'result_filename': resultados})

    except FileNotFoundError as e:
        print(f'Error en el servidor: Archivo no encontrado: {str(e)}')
        return jsonify({'error': f'Archivo no encontrado: {str(e)}'}), 404
    
    except Exception as e:
        print(f'Error interno del servidor: {str(e)}')
        return jsonify({'error': f'Error interno del servidor: {str(e)}'}), 500

@app.route('/api/download/<path:filename>', methods=['GET'])
def download_file(filename):

    filepath = join(filename.replace('/', os.sep))
    print(f'Ruta completa del archivo: {filepath}')

    if os.path.exists(filepath):
        return send_from_directory('.', filename, as_attachment=True)
    else:
        return jsonify({'error': f'Archivo no encontrado: {filename}', 'ruta_completa': filepath}), 404
    
@app.route('/api/preview/<path:filename>', methods=['GET'])
def get_preview_image(filename):
        
    filepath = join(filename.replace('/', os.sep))
    print(f'Ruta completa del archivo: {filepath}')

    if os.path.exists(filepath):
        return send_from_directory('.', filename)
    else:
        return jsonify({'error': f'Imagen previa no encontrada: {filename}', 'ruta_completa': filepath}), 404

if __name__ == '__main__':
    app.run(debug=True)