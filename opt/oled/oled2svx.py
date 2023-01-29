#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SP2ONG 2022 oled2svx

import time
from datetime import datetime
import math
import os

import subprocess

from board import SCL, SDA
import busio
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306

# Create the I2C interface.
i2c = busio.I2C(SCL, SDA)
# Create the SSD1306 OLED class.
# The first two parameters are the pixel width and pixel height.  Change these
# to the right size for your display!
disp = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c)

# Contrast OLED values 1 -255
disp.contrast(5)
#
# time out for screen saver
screen_saver=10


# Clear display.
disp.fill(0)
disp.show()

# Create blank image for drawing.
# Make sure to create image with mode '1' for 1-bit color.
width = disp.width
height = disp.height
image = Image.new("1", (width, height))

# Get drawing object to draw on image.
draw = ImageDraw.Draw(image)

# Draw a black filled box to clear the image.
draw.rectangle((0, 0, width, height), outline=0, fill=0)

# Draw some shapes.
# First define some constants to allow easy resizing of shapes.
padding = -2
top = padding
bottom = height - padding
# Move left to right keeping track of the current x position for drawing shapes.
x = 0

# Load default font.
#font = ImageFont.load_default()
# use custom font
font_path = str('/opt/oled/fonts/Roboto-Light.ttf')
font12 = ImageFont.truetype(font_path, 11)
font14 = ImageFont.truetype(font_path, 14)
font20 = ImageFont.truetype(font_path, 20)
font = ImageFont.truetype(font_path, 18)


def get_svxlog():
    f = os.popen('egrep -a -h "Talker start on|Talker stop on" /var/log/svxlink | tail -1')
    logsvx = str(f.read()).split(" ")
    if len(logsvx)>=2 and logsvx[4]=="start":
       CALL=logsvx[8].rstrip("\r\n")
       TalkG="TG "+logsvx[7].lstrip("#").rstrip(":")
    else:
       CALL=""
       TalkG=""
    return CALL,TalkG

def get_ip():
    cmd = "hostname -I | awk '{print $1}'"
    IP = subprocess.check_output(cmd, shell = True ).decode("utf-8")
    return "IP:  " + str(IP).rstrip("\r\n")+" "

def get_temp():
    # get cpu temperature
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as temp:
            tmpCel = int(temp.read()[:2])
    except:
        tmpCel = 0
    finally:
        return "T "+str(tmpCel)+" C"
#        return "T "+str(tmpCel)+"°C"

def get_cpuL():
    cmd = "top -bn1 | grep load | awk '{printf \"CPU : L %.2f,\", $(NF-2)}'"
    CPUL = subprocess.check_output(cmd, shell = True ).decode("utf-8")
    return CPUL


# Define text and get total width.
text = (
    "SVXRelector PL"
)
maxwidth, unused = draw.textsize(text, font=font)

# Set animation and sine wave parameters.
amplitude = height / 4
offset = height / 2 - 2
velocity = -2
startpos = width
pos = startpos

# width in pixel screen
W=128

time_show="0"
count=0

while True:
    count =count+1

    # Draw a black filled box to clear the image.
    draw.rectangle((0,0,width,height), outline=0, fill=0)
    check_svx=get_svxlog()
    if check_svx[0]!="":
      time_show="0"
      count=0
      msg = str(check_svx[1])
      w,h = draw.textsize(msg,font=font14)
      draw.text(((W-w)/2, top+32),    msg,  font=font14, fill=255)
      msg = str(check_svx[0])
      w,h = draw.textsize(msg,font=font14)
      draw.text(((W-w)/2, top+50),    msg,  font=font14, fill=255)
    elif check_svx[0]=="" and count<screen_saver:
      now = datetime.now()
      current_time = now.strftime("Time: "+"%H:%M")
      msg = str(current_time)
      w,h = draw.textsize(msg,font=font20)
      draw.text(((W-w)/2, top+38),    msg,  font=font20, fill=255)
      time_show="1"
    if count<screen_saver:
      Temp = get_temp()
      CPUL = get_cpuL()
      msg = str(CPUL) + " "+str(Temp)
      draw.text((x, top), msg, font=font14, fill=255)

      msg = get_ip()
      w,h = draw.textsize(msg,font=font12)
      draw.text(((W-w)/2, top+16),  msg, font=font12, fill=255)

    # Screen saver
    if time_show=="1" and check_svx[0]=="" and count>screen_saver and flase :
      draw.rectangle((0, 0, width, height), outline=0, fill=0)
      xx = pos
      for i, c in enumerate(text):
        # Stop drawing if off the right side of screen.
        if xx > width:
            break
        # Calculate width but skip drawing if off the left side of screen.
        if xx < -10:
            char_width, char_height = draw.textsize(c, font=font)
            xx += char_width
            continue
        # Calculate offset from sine wave.
        y = offset + math.floor(amplitude * math.sin(xx / float(width) * 2.0 * math.pi))
        # Draw text.
        draw.text((xx, y), c, font=font, fill=255)
        # Increment x position based on chacacter width.
        char_width, char_height = draw.textsize(c, font=font)
        xx += char_width

    # Display image.
    disp.image(image)
    disp.show()

    # Move position for next frame.
    pos += velocity
    # Start over if text has scrolled completely off left side of screen.
    if pos < -maxwidth:
        pos = startpos
    if time_show=="1" and count>screen_saver:
      time.sleep(0.05)
    else:
      time.sleep(0.25)
