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
	base=Image.new("RGBA",(W,H),(random.randrange(170,255),random.randrange(70,255),random.randrange(70,255)))
	font_path=os.environ.get("font_path","./fonts/DroidSans-Bold.ttf")
	fnt=ImageFont.truetype(font_path,100)
	w,h=fnt.getsize(li)
	if w>W:
		base=base.resize((W+(w-W)+20,H),Image.ANTIALIAS)
		W=W+(w-W)+20
	d=ImageDraw.Draw(base)
	d.text(((W-w)/2,(H-h)/2),li,font=fnt,fill="white")
	try:
		os.mkdir("./output/images")
	except Exception:
		pass
	base.save("./output/images/"+s+".png")
	return "static.careerbreeder.com/output/images/"+s+".png"
