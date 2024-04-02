from PIL import Image
from PIL import GifImagePlugin
from colorthief import ColorThief
import os
import sys
import subprocess
import shutil
import glob
import random

class Converter:
	def __init__(self,screen_width,screen_height,orientation=1):
		self.__screen_width = screen_width
		self.__screen_height = screen_height
		self.__orientation = orientation
		
	def get_rand_name(self):
		random.seed()
		name = ''
		for i in range(5):
			name += random.choice(list('0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'))
		return name
			
		
	def rgb888_to_rgb565(self,red8, green8, blue8):
	    # Convert 8-bit red to 5-bit red.
		red5 = round(red8 / 255 * 31)
	    # Convert 8-bit green to 6-bit green.
		green6 = round(green8 / 255 * 63)
	    # Convert 8-bit blue to 5-bit blue.
		blue5 = round(blue8 / 255 * 31)
	
	    # Shift the red value to the left by 12 bits.
		red5_shifted = red5 << 11
	    # Shift the green value to the left by 56 bits.
		green6_shifted = green6 << 5
	
		# Combine the red, green, and blue values.
		rgb565 = "0x%0.4X" % (red5_shifted | green6_shifted | blue5)
	
		return rgb565
		
	def rgb_to_rgb888(self,rgb):
	    # Shift the red value to the left by 12 bits.
		red8_shifted = rgb[0] << 16
	    # Shift the green value to the left by 56 bits.
		green8_shifted = rgb[1] << 8
	
		# Combine the red, green, and blue values.
		rgb888 = "0x%0.6X" % (red8_shifted | green8_shifted | rgb[2])
		return rgb888
		
	def rgb888_to_rgb(self,color):
		if color.startswith('#'):
			color = color[1:]
		if color.startswith('0x'):
			color = color[2:]
		return tuple(int(color[i:i+2],16) for i in (0, 2, 4))
		
	def convert(self,imagePath,custom_color=None):
		if self.__orientation > 0:
			print('converter: rotating image')
		tmp_name = self.get_rand_name()
		if self.__orientation == 0:#standard portrait orientation
			shutil.copy(imagePath,tmp_name+'.gif')
		elif self.__orientation == 1:#standard landscape orientation
			subprocess.call([".\gifsicle.exe","-w","--rotate-90",imagePath,"-o", tmp_name+'.gif'])
		elif self.__orientation == 2:#swapped portrait orientation
			subprocess.call([".\gifsicle.exe","-w","--rotate-180",imagePath,"-o", tmp_name+'.gif'])
		elif self.__orientation == 3:#swapped landscape orientation
			subprocess.call([".\gifsicle.exe","-w","--rotate-270",imagePath,"-o", tmp_name+'.gif'])
		print('converter: processing image')
		subprocess.call([".\gifsicle.exe","-w","--resize-colors","256","--resize-method","lanczos3","--resize-fit",str(self.__screen_width)+'x'+str(self.__screen_height),tmp_name+'.gif',"-o", tmp_name+'.gif'])
		img = Image.open(tmp_name+'.gif')
		tmp2_name = self.get_rand_name()
		shutil.copy(tmp_name+'.gif', tmp2_name+'.gif')
		
		
		#Find a fitting background color to complement the gif
		if custom_color is None:
			print("converter: finding background color")
			color_thief = ColorThief(imagePath)
			color = color_thief.get_color(quality=1)
		
			if((img.width/self.__screen_width) < 0.5 or (img.height/self.__screen_height) < 0.5):
				color = (255-color[0],255-color[1],255-color[2])
			bgColor = self.rgb_to_rgb888(color)
		else:
			color = self.rgb888_to_rgb(custom_color)
			bgColor = custom_color
			
		print("converter: removing transparency")
		
		with Image.open(tmp_name+'.gif') as img:
			for i in range(0,img.n_frames):
				img.seek(i)
				im = img.copy().convert('RGBA')
				for y in range(0,im.height):
					for x in range(0,im.width):
						pixel = im.getpixel((x,y))
						if pixel[3] == 0:
							im.putpixel((x,y),color)
				im.save(tmp_name+"{}.gif".format(i))
			
				subprocess.call([".\gifsicle.exe","-w",tmp2_name+'.gif',"--replace","#{}".format(i),tmp_name+"{}.gif".format(i),"-o",tmp2_name+'.gif'])
		
		name = bgColor+'_'+str(self.__orientation)+os.path.basename(imagePath)
		print("converter: formating outputfile")
		try:
			os.replace(tmp2_name+'.gif', bgColor+'_'+str(self.__orientation)+os.path.basename(imagePath))
		except:
			name = bgColor+'_'+str(4)+os.path.basename(imagePath)
			#file already exist and is currently being uploaded or used so save a copy
			os.replace(tmp2_name+'.gif', bgColor+'_'+str(4)+os.path.basename(imagePath))
		
		
		print("converter: cleaning up.")
		for i in range(0,img.n_frames):
			os.remove((tmp_name+'{}.gif'.format(i)))
		img.close()
		if os.path.exists(tmp_name+'.gif'):
			os.remove(tmp_name+'.gif')
			print("converter: done.")
			
		return os.getcwd()+'\\'+name

