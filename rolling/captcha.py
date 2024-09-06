from PIL import Image, ImageDraw, ImageFont, ImageFilter
import random

async def generate_captcha(width, height, length):
    characters = "wakeupWAKEUP"
    captcha_text = ''.join(random.choice(characters) for _ in range(length))
    print(f"Generated captcha with solution {captcha_text}")
    
    image = Image.new('RGBA', (width, height), color=(255, 255, 255, 0))
    font = ImageFont.truetype('arial.ttf', size=40)

    for i, char in enumerate(captcha_text):
        char_image = Image.new('RGBA', (50, 50), (random.randint(0,255), random.randint(0,255), random.randint(0,255), 255))
        char_draw = ImageDraw.Draw(char_image)
        char_draw.text((10, 10), char, (0, 0, 0), font=font)
        char_image = char_image.rotate(random.randint(-30, 30), expand=1)
        
        distorted_image = Image.new('RGBA', char_image.size)
        for x in range(char_image.width):
            for y in range(char_image.height):
                src_x = int(x + random.choice([-2, -1, 1, 2]))
                src_y = int(y + random.choice([-2, -1, 1, 2]))
                if 0 <= src_x < char_image.width and 0 <= src_y < char_image.height:
                    distorted_image.putpixel((x, y), char_image.getpixel((src_x, src_y)))
        
        image.paste(distorted_image, (i * 40 + 10, 10), distorted_image)
    
    image = image.filter(ImageFilter.GaussianBlur(radius=1))
    image.save('./storage/captcha.png')

    image = Image.open('./storage/captcha.png')

    with open("./storage/captcha.txt", "w") as f:
        f.write(captcha_text)

    return captcha_text 