import urllib
import os

def DownloadImages(rows):
	not_responding_urls = []
	for row in rows:
		print "row=\n\n",row,"\n\n"
		inp = input()
		newpath = r'downloaded_images/'+row['City']
		if not os.path.exists(newpath):
			os.makedirs(newpath)
		image_list = row['Images URL'].split(',')
		for image in image_list:
			image = image.strip()
			filename = image.split('/')[-1]
			try:
				urllib.urlretrieve(image,"downloaded_images/"+row['City']+"/"+row['EduID']+"__"+filename)
			except:
				not_responding_urls.append(image)
	#the following line shows list of urls failed to fetch			
	print "images could not fetch=\n\n",not_responding_urls