from PIL import Image,ImageDraw,ImageFont
import random
import re
import os
import glob
def fetch(s):
	li=""
	x=re.compile(r'[A-Z]')
	x=x.findall(s)
	for i in range(len(x)):
		li+=x[i]
	W,H=(850,450)
	print 
	base=Image.new("RGBA",(W,H),(random.randrange(170,255),random.randrange(70,255),random.randrange(70,255)))
	font_path=os.environ.get("font_path","./fonts/DroidSans-Bold.ttf")
	fnt=ImageFont.truetype(font_path,100)
	w,h=fnt.getsize(li)
	if w>W:
		base=base.resize((W+(w-W)+20,H),Image.ANTIALIAS)
		W=W+(w-W)+20
	d=ImageDraw.Draw(base)
	d.text(((W-w)/2,(H-h)/2),li,font=fnt,fill="white")
	return "static.careerbreeder.com/output/images/"+s+".png"

def correctImage(photos):
	'''
	correcting thumbnails
	'''
	new_imgs=''
	photos_li=list(map(str,list(photos.strip().split("#"))))
	#print "photos_li",photos_li
	match_str=re.compile(r'-t',re.I)
	for i in range(len(photos_li)):
		if match_str.search(photos_li[i].strip()):
			photos_li[i]=''
	for i in range(len(photos_li)):
		if photos_li[i]!='' and i!=(len(photos_li)-1):
			new_imgs+=photos_li[i]+","
		elif photos_li[i]!='' and i==(len(photos_li)-1):
			new_imgs+=photos_li[i]
	return new_imgs

