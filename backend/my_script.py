import os
import fitz 
import tempfile
import Lenguaje
from pdf2image import convert_from_path
from reportlab.lib.pagesizes import letter
from werkzeug.datastructures import FileStorage
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer


def get_error_type(rule_id):
    if rule_id.startswith('MORFOLOGIK_RULE_ES'):
        return 'Ortografía'
    elif rule_id == 'ES_SIMPLE_REPLACE_SIMPLE_TAMBIEN':
        return 'Error gramatical'
    else:
        return 'Desconocido'

def analizar_documento_pdf(archivo, output_folder='resultados', preview_folder='vistas_previas'):
    try:        
        if isinstance(archivo, FileStorage):
            archivo_temp_path = os.path.join('uploads', archivo.filename)
            archivo.save(archivo_temp_path)
        elif isinstance(archivo, str):
            archivo_temp_path = archivo
        else:
            raise ValueError('Tipo de archivo no admitido')

        pdf_filepath, vista_previa_filepath = process_document_from_server(archivo_temp_path, output_folder, preview_folder)

        return pdf_filepath, vista_previa_filepath

    except fitz.FileNotFoundError as e:
        print(f'Error en el servidor: Archivo no encontrado: {str(e)}')
        return {'error': f'Archivo no encontrado: {str(e)}'}, 404

    except Exception as e:
        print(f'Error interno del servidor: {str(e)}')
        return {'error': f'Error interno del servidor: {str(e)}'}, 500

def process_document_from_server(input_pdf_filepath, output_pdf_folder='resultados', preview_folder='vistas_previas'):
    try:
        tool = Lenguaje.LanguageToolPublicAPI('es')

        document_text = extract_text_from_pdf(input_pdf_filepath)

        matches = tool.check(document_text)

        output_pdf_filepath = highlight_errors_pdf(document_text, matches, pdf_folder=output_pdf_folder)

        preview_image_filepath = generate_preview_image(output_pdf_filepath, preview_folder)
        
        os.remove(input_pdf_filepath)

        return output_pdf_filepath, preview_image_filepath

    except Exception as e:
        print(f'Error al procesar el documento: {str(e)}')

        os.remove(input_pdf_filepath)
        
        return None, None


def extract_text_from_pdf(pdf_filepath):
    pdf_document = fitz.open(pdf_filepath)
    text = ""
    for page_num in range(pdf_document.page_count):
        page = pdf_document[page_num]
        text += page.get_text()
    pdf_document.close()
    return text    

def highlight_errors_pdf(text, matches, pdf_folder='resultados', pdf_filename='output.pdf'):
    try:
        os.makedirs(pdf_folder, exist_ok=True)

        pdf_filepath = os.path.join(pdf_folder, pdf_filename.replace('\\', '/'))
        doc = SimpleDocTemplate(pdf_filepath, pagesize=letter)
        elements = []

        texto_formateado = ''

        i = 0
        while i < len(text):
            palabra_actual = ''
            tipo_error = None
            mensaje = None

            for match in matches:
                start, end = match.offset, match.offset + match.errorLength
                if start <= i < end:
                    palabra_actual = text[start:end]
                    tipo_error = get_error_type(match.ruleId)
                    mensaje = match.message

            if tipo_error == 'Ortografía':
                texto_formateado += f'<font color="blue">{palabra_actual}</font>'
            elif tipo_error == 'Error gramatical':
                texto_formateado += f'<font color="green">{palabra_actual}</font>'
            else:
                texto_formateado += text[i]

            i += len(palabra_actual) or 1

        elements.append(Paragraph(texto_formateado, style=getSampleStyleSheet()["BodyText"]))

        for match in matches:
            tipo_error = get_error_type(match.ruleId)
            palabra_incorrecta = text[match.offset:match.offset + match.errorLength]

            elements.append(Paragraph(f'\nPalabra Incorrecta: <font color="red">{palabra_incorrecta}</font>', style=getSampleStyleSheet()["BodyText"]))
            elements.append(Paragraph(f'Tipo de Error: <font color="purple">{tipo_error}</font>', style=getSampleStyleSheet()["BodyText"]))
            elements.append(Paragraph(f'Mensaje: <font color="brown">{match.message}</font>', style=getSampleStyleSheet()["BodyText"]))
            elements.append(Paragraph(f'Reemplazos sugeridos: {match.replacements}', style=getSampleStyleSheet()["BodyText"]))
            elements.append(Paragraph(f'Posición del error: {match.offset}-{match.offset + match.errorLength}', style=getSampleStyleSheet()["BodyText"]))
            elements.append(Spacer(1, 12))

        doc.build(elements)

        print(f'Ruta del archivo resultante: {pdf_filepath}')
        return pdf_filepath

    except Exception as e:
        print(f'Error al resaltar errores en el PDF: {str(e)}')
        return None


def generate_preview_image(pdf_filepath, output_folder='vistas_previas'):
    try:
        os.makedirs(output_folder, exist_ok=True)

        images = convert_from_path(pdf_filepath, first_page=1, last_page=1)

        with tempfile.NamedTemporaryFile(dir=output_folder, delete=False, suffix=".png") as temp_image:
            images[0].save(temp_image.name, format="PNG")
            preview_image_filename = os.path.basename(temp_image.name)

        preview_image_filepath = os.path.join(output_folder, preview_image_filename)

        return preview_image_filepath
    
    except Exception as e:
        print(f'Error al generar la vista previa después del análisis: {str(e)}')
        return None