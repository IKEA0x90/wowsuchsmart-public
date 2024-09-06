import openai
import os
import requests
from random import randint
import ftplib

clientopenai = openai.OpenAI(api_key="")
img_path = "img/generated"

async def make_image(description, quality="standard"):
    if description:
        response = clientopenai.images.generate(
            model="dall-e-3",
            prompt=description,
            size="1024x1024",
            quality=quality,
            n=1,
        )
        
        image_url = response.data[0].url
        return image_url
    return "Something went wrong"

async def save_image(image_url, save_path = img_path):
    try:
        if not os.path.exists(img_path):
            os.makedirs(img_path)

        response = requests.get(image_url, stream=True)
        
        if response.status_code == 200:
            file_path = f'{img_path}/{randint(1,1000000000)}.png'
            while os.path.exists(file_path):
                file_path = f'{img_path}/{randint(1,1000000000)}.png'

            with open(f'{file_path}', 'wb') as file:
                for chunk in response.iter_content(1024):
                    file.write(chunk)
                
            print(f"Image saved as {file_path}")
            return file_path
        else:
            print(f"Failed to retrieve image. HTTP Status code: {response.status_code}")

    except Exception as e:
        print(f"An error occurred: {e}")

async def upload_image(server, username, password, file_path):
    try:
        ftp = ftplib.FTP(server)
        ftp.login(user=username, passwd=password)
        
        filename = file_path.split('/')[-1]
        
        with open(file_path, 'rb') as file:
            ftp.storbinary(f'STOR {filename}', file)
        
        return f""
        
    except ftplib.all_errors as e:
        print(f"FTP error: {e}")
        
    finally:
        ftp.quit()