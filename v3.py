import os
import zipfile
from PIL import Image
import tkinter as tk
from tkinter import filedialog, ttk, scrolledtext, messagebox
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
import tempfile
import subprocess

def resize_image(img, output_size=(1000, 1000)):
    aspect_ratio = img.width / img.height
    if aspect_ratio > 1:
        new_width = output_size[0]
        new_height = int(new_width / aspect_ratio)
    else:
        new_height = output_size[1]
        new_width = int(new_height * aspect_ratio)
    
    img_resized = img.resize((new_width, new_height), Image.LANCZOS)
    background = Image.new('RGB', output_size, (255, 255, 255))
    offset = ((output_size[0] - new_width) // 2, (output_size[1] - new_height) // 2)
    background.paste(img_resized, offset)
    return background

def process_image(image_path, output_folder, output_format, original_name, output_size=(1000, 1000)):
    try:
        with Image.open(image_path) as img:
            img_resized = resize_image(img, output_size)
            output_path = os.path.join(output_folder, os.path.basename(original_name))
            if output_format.lower() == 'jpg':
                img_resized.save(output_path, "JPEG")
            elif output_format.lower() == 'png':
                img_resized.save(output_path, "PNG")
            elif output_format.lower() == 'webp':
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
                for future in tqdm(futures, desc="Procesando imágenes"):
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
                for future in tqdm(futures, desc="Procesando imágenes"):
                    result = future.result()
                    if result:
                        processed_images.append(result)
    else:
        raise ValueError("La entrada debe ser un archivo ZIP o una carpeta")
    return processed_images

def open_output_folder(folder_path):
    if os.name == 'nt':  # Windows
        os.startfile(folder_path)
    elif os.name == 'posix':  # macOS y Linux
        subprocess.call(['open', folder_path]) if sys.platform == 'darwin' else subprocess.call(['xdg-open', folder_path])

class ImageProcessorApp:
    def __init__(self, master):
        self.master = master
        master.title("Procesador de Imágenes")

        self.input_label = tk.Label(master, text="Entrada:")
        self.input_label.grid(row=0, column=0, sticky="e")
        self.input_entry = tk.Entry(master, width=50)
        self.input_entry.grid(row=0, column=1)
        self.input_button = tk.Button(master, text="Seleccionar", command=self.select_input)
        self.input_button.grid(row=0, column=2)

        self.codes_label = tk.Label(master, text="Códigos:")
        self.codes_label.grid(row=1, column=0, sticky="ne")
        self.codes_text = scrolledtext.ScrolledText(master, width=50, height=10)
        self.codes_text.grid(row=1, column=1, columnspan=2)

        self.format_label = tk.Label(master, text="Formato de salida:")
        self.format_label.grid(row=2, column=0, sticky="e")
        self.format_var = tk.StringVar(value="jpg")
        self.format_dropdown = ttk.Combobox(master, textvariable=self.format_var, values=["jpg", "png", "webp"])
        self.format_dropdown.grid(row=2, column=1)

        self.process_button = tk.Button(master, text="Procesar Imágenes", command=self.process_images)
        self.process_button.grid(row=3, column=1)

    def select_input(self):
        path = filedialog.askopenfilename(filetypes=[("ZIP files", "*.zip")]) or filedialog.askdirectory()
        if path:
            self.input_entry.delete(0, tk.END)
            self.input_entry.insert(0, path)

    def process_images(self):
        input_path = self.input_entry.get()
        output_format = self.format_var.get()
        image_codes = [code.strip() for code in self.codes_text.get("1.0", tk.END).split('\n') if code.strip()]
        if not input_path:
            messagebox.showerror("Error", "Por favor, seleccione la entrada.")
            return
        if not image_codes:
            messagebox.showerror("Error", "Por favor, ingrese los códigos de las imágenes.")
            return
        output_folder = os.path.join(os.getcwd(), "processed_images")
        try:
            processed_images = process_images(input_path, output_folder, output_format, image_codes)
            messagebox.showinfo("Éxito", f"Se procesaron {len(processed_images)} imágenes.")
            open_output_folder(output_folder)
        except Exception as e:
            messagebox.showerror("Error", str(e))

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageProcessorApp(root)
    root.mainloop()
