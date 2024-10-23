from flask import Flask, render_template, request, redirect, url_for, jsonify
from PIL import Image
import matplotlib.pyplot
matplotlib.use('Agg')
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
    if not verify_recaptcha(recaptcha_response):
        return 'Captcha verification failed, please try again.', 400

    # Получаем данные формы
    scale = float(request.form.get('scale', 1.0))  # Получаем масштаб
    image_file = request.files['image']

    if image_file:
        # Сохранение оригинального изображения
        image_path = save_image(image_file)
        
        # Изменение масштаба изображения
        resized_image_path = resize_image(image_path, scale, image_file.filename)

        # Построение графиков распределения цветов
        plot_color_distribution(image_path, 'original')
        plot_color_distribution(resized_image_path, 'resized')

        return render_template('result.html', 
                               original_image=image_file.filename, 
                               resized_image=f'resized_{image_file.filename}')
    return redirect(url_for('index'))

# Проверка капчи через Google reCAPTCHA API
def verify_recaptcha(recaptcha_response):
   
    secret_key = '6LfD_2cqAAAAAMLqRsP-wGcIELbHKX0Tt10QJUme'
    verify_url = 'https://www.google.com/recaptcha/api/siteverify'
    data = {
        'secret': secret_key,
        'response': recaptcha_response
    }
    r = requests.post(verify_url, data=data)
    result = r.json()
    return result.get('success', False)

# Сохранение изображения на сервере
def save_image(image_file):
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

# Построение графиков распределения цветов
def plot_color_distribution(image_path, name):
    img = Image.open(image_path)
    arr = np.array(img)
    colors = ('r', 'g', 'b')

    plt.figure(figsize=(10, 5))
    for i, color in enumerate(colors):
        plt.hist(arr[:, :, i].ravel(), bins=256, color=color, alpha=0.5)

    plt.title(f'Color distribution - {name}')
    plt.xlabel('Pixel Value')
    plt.ylabel('Frequency')
    plt.savefig(f'./static/{name}_color_distribution.png')
    plt.close()

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(debug=True)
