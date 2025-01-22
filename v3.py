import os
import zipfile
from PIL import Image
import tempfile
from concurrent.futures import ThreadPoolExecutor
import flet as ft

def resize_image(img, output_size=(1000, 1000)):
    aspect_ratio = img.width / img.height
    if aspect_ratio > 1:
        new_width = output_size[0]
        new_height = int(new_width / aspect_ratio)
    else:
        new_height = output_size[1]
        new_width = int(new_height * aspect_ratio)

    img_resized = img.resize((new_width, new_height), Image.LANCZOS)
    background = Image.new("RGB", output_size, (255, 255, 255))
    offset = ((output_size[0] - new_width) // 2, (output_size[1] - new_height) // 2)
    background.paste(img_resized, offset)
    return background

def process_image(image_path, output_folder, output_format, original_name, output_size=(1000, 1000)):
    try:
        with Image.open(image_path) as img:
            img_resized = resize_image(img, output_size)
            output_path = os.path.join(output_folder, os.path.basename(original_name))
            if output_format.lower() == "jpg":
                img_resized.save(output_path, "JPEG")
            elif output_format.lower() == "png":
                img_resized.save(output_path, "PNG")
            elif output_format.lower() == "webp":
                img_resized.save(output_path, "WEBP")
            else:
                raise ValueError(f"Formato no soportado: {output_format}")
        return output_path
    except Exception as e:
        print(f"Error procesando {image_path}: {str(e)}")
        return None

def extract_and_process_images(zip_file, output_folder, output_format, image_codes):
    processed_images = []
    with tempfile.TemporaryDirectory() as temp_dir:
        zip_file.extractall(temp_dir)
        for root, _, files in os.walk(temp_dir):
            image_files = [os.path.join(root, f) for f in files if any(f.startswith(code) for code in image_codes)]
            with ThreadPoolExecutor() as executor:
                futures = [executor.submit(process_image, img, output_folder, output_format, img) for img in image_files]
                for future in futures:
                    result = future.result()
                    if result:
                        processed_images.append(result)
    return processed_images

def process_images(input_path, output_folder, output_format, image_codes):
    os.makedirs(output_folder, exist_ok=True)
    processed_images = []
    if os.path.isfile(input_path) and input_path.lower().endswith('.zip'):
        with zipfile.ZipFile(input_path, 'r') as zip_file:
            processed_images = extract_and_process_images(zip_file, output_folder, output_format, image_codes)
    elif os.path.isdir(input_path):
        for root, _, files in os.walk(input_path):
            image_files = [os.path.join(root, f) for f in files if any(f.startswith(code) for code in image_codes)]
            with ThreadPoolExecutor() as executor:
                futures = [executor.submit(process_image, img, output_folder, output_format, img) for img in image_files]
                for future in futures:
                    result = future.result()
                    if result:
                        processed_images.append(result)
    else:
        raise ValueError("La entrada debe ser un archivo ZIP o una carpeta")
    return processed_images

def main(page: ft.Page):
    page.title = "Procesador de Imágenes"
    page.scroll = ft.ScrollMode.AUTO

    input_path = ft.TextField(label="Ruta de entrada", width=600)
    codes_field = ft.TextField(label="Códigos de imágenes (uno por línea)", multiline=True, height=150)
    format_dropdown = ft.Dropdown(label="Formato de salida", options=[ft.dropdown.Option("jpg"), ft.dropdown.Option("png"), ft.dropdown.Option("webp")])
    output_label = ft.Text(value="", color=ft.colors.GREEN)

    def select_input(e):
        path = ft.FilePicker(on_result=lambda f: input_path.value := f.path)
        page.overlay.append(path)
        path.pick_files(allow_folders=True, dialog_title="Seleccionar entrada")

    def process_images_event(e):
        if not input_path.value:
            output_label.value = "Por favor, selecciona una entrada."
            page.update()
            return

        if not codes_field.value.strip():
            output_label.value = "Por favor, ingresa los códigos de imágenes."
            page.update()
            return

        output_folder = os.path.join(os.getcwd(), "processed_images")
        image_codes = [code.strip() for code in codes_field.value.split('\n') if code.strip()]
        output_format = format_dropdown.value

        try:
            processed_images = process_images(input_path.value, output_folder, output_format, image_codes)
            output_label.value = f"Se procesaron {len(processed_images)} imágenes."
            page.update()
        except Exception as e:
            output_label.value = f"Error: {str(e)}"
            page.update()

    select_button = ft.ElevatedButton("Seleccionar entrada", on_click=select_input)
    process_button = ft.ElevatedButton("Procesar Imágenes", on_click=process_images_event)

    page.add(
        ft.Row([input_path, select_button]),
        codes_field,
        format_dropdown,
        process_button,
        output_label
    )

ft.app(target=main)
