from PIL import Image,ImageDraw,ImageFont
import random
import re
import os
def fetch(s):
	li=""
	x=re.compile(r'[A-Z]')
	x=x.findall(s)
	for i in range(len(x)):
		li+=x[i]
	W,H=(250,250)
	base=Image.new("RGBA",(250,250),(random.randrange(170,255),random.randrange(70,255),random.randrange(70,255)))
	fnt=ImageFont.truetype('Pillow/Tests/fonts/FreeMonoBold.ttf',50)
	w,h=fnt.getsize(li)
	d=ImageDraw.Draw(base)
	d.text(((W-w)/2,(H-h)/2),li,font=fnt,fill="white",spacing=1)
	try:
		os.makedirs("./output/images")
	except Exception:
		pass
	base.save("./output/images/"+s+".png")
	return "./output/images/"+s+".png"
fetch("IIT Delhi")



