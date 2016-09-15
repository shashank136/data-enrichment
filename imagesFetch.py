from PIL import Image,ImageDraw,ImageFont
import random
import re
import os
import glob
def fetch(s):
	li=""
	add=glob.glob("./output/images")
	x=re.compile(r'[A-Z]')
	x=x.findall(s)
	for i in range(len(x)):
		li+=x[i]
	W,H=(250,250)
	base=Image.new("RGBA",(250,250),(random.randrange(170,255),random.randrange(70,255),random.randrange(70,255)))
	font_path=os.environ.get("font_path","./fonts/DroidSans-Bold.ttf")
	fnt=ImageFont.truetype(font_path,50)
	w,h=fnt.getsize(li)
	d=ImageDraw.Draw(base)
	d.text(((W-w)/2,(H-h)/2),li,font=fnt,fill="white")
	try:
		os.makedirs(add)
	except Exception:
		pass
	#add=glob.glob("./output/images/")
	base.save("./output/images/"+s+".png")
	return "./output/images/"+s+".png"


