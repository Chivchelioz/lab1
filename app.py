from flask import Flask, render_template, request, redirect, url_for
from PIL import Image, ImageDraw
import numpy as np
import os
import requests

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = './static/uploads/'

# Главная страница
@app.route('/')
def index():
    return render_template('index.html')

# Обработка загрузки изображения и проверки капчи
@app.route('/upload', methods=['POST'])
def upload_image():
    # Проверка капчи
    recaptcha_response = request.form.get('g-recaptcha-response')
    if not recaptcha_response or not verify_recaptcha(recaptcha_response):
        return 'Captcha verification failed, please try again.', 400

    # Получаем данные формы
    scale = request.form.get('scale')
    try:
        scale = float(scale) if scale else 1.0  # Получаем масштаб
    except ValueError:
        return 'Invalid scale value.', 400

    image_file = request.files.get('image')
    
    if image_file and image_file.filename != '':
        # Сохранение оригинального изображения
        image_path = save_image(image_file)
        
        # Изменение масштаба изображения
        resized_image_path = resize_image(image_path, scale, image_file.filename)

        # Построение графиков распределения цветов
        plot_color_distribution(image_path, 'original')
        plot_color_distribution(resized_image_path, 'resized')

        return render_template(
            'result.html', 
            original_image=image_file.filename, 
            resized_image=f'resized_{image_file.filename}'
        )
    return redirect(url_for('index'))

# Проверка капчи через Google reCAPTCHA API
def verify_recaptcha(recaptcha_response):
    secret_key = '6LfD_2cqAAAAAMLqRsP-wGcIELbHKX0Tt10QJUme'
    verify_url = 'https://www.google.com/recaptcha/api/siteverify'
    data = {
        'secret': secret_key,
        'response': recaptcha_response
    }
    try:
        r = requests.post(verify_url, data=data)
        result = r.json()
        return result.get('success', False)
    except requests.RequestException:
        return False

# Сохранение изображения на сервере
def save_image(image_file):
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
        
    image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_file.filename)
    image_file.save(image_path)
    return image_path

# Изменение масштаба изображения
def resize_image(image_path, scale, filename):
    img = Image.open(image_path)
    new_size = (int(img.size[0] * scale), int(img.size[1] * scale))
    resized_img = img.resize(new_size)

    resized_path = os.path.join(app.config['UPLOAD_FOLDER'], f'resized_{filename}')
    resized_img.save(resized_path)
    return resized_path

# Построение графиков распределения цветов (новая версия без matplotlib)
def plot_color_distribution(image_path, name):
    img = Image.open(image_path)
    arr = np.array(img)

    # Создание пустого изображения для гистограммы
    histogram_img = Image.new('RGB', (800, 400), (255, 255, 255))
    draw = ImageDraw.Draw(histogram_img)

    # Цветовая карта для отображения цветов гистограммы
    color_map = {'r': (255, 0, 0), 'g': (0, 255, 0), 'b': (0, 0, 255)}

    # Нормализация и создание гистограммы
    colors = ('r', 'g', 'b')
    for i, color in enumerate(colors):
        histogram = np.histogram(arr[:, :, i].ravel(), bins=256, range=(0, 256))[0]
        max_count = max(histogram)
        normalized_histogram = (histogram / max_count) * 300  # Нормализуем до высоты 300 пикселей

        # Рисуем гистограмму
        for x, count in enumerate(normalized_histogram):
            draw.line([(x * 3 + i * 3, 400), (x * 3 + i * 3, 400 - count)], fill=color_map[color])

    # Сохранение изображения гистограммы
    histogram_img.save(f'./static/{name}_color_distribution.png')


if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(debug=True)
