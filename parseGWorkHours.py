# -*- coding: utf-8 -*-
import phpserialize

dayofweek=['SUNDAY','MONDAY','TUESDAY','WEDNESDAY','THURSDAY','FRIDAY','SATURDAY']
def getTime(n):
	ret_time=""
	time=int(n);
	hours=time/100;
	minutes=time%100;
	if hours>=12:
		if minutes==0:
			ret_time=str(hours%12)+" PM"
		else:
			ret_time=str(hours%12)+"."+str(minutes)+" PM"
	else:
		if minutes==0:
			ret_time=str(hours)+" AM"
		else:
			ret_time=str(hours)+"."+str(minutes)+" AM"
	return ret_time
'''
        kept for quick reference/debugging
lisdays= [
            {
               "close" : {
                  "day" : 1,
                  "time" : "1930"
               },
               "open" : {
                  "day" : 1,
                  "time" : "1500"
               }
            },
            {
               "close" : {
                  "day" : 2,
                  "time" : "1930"
               },
               "open" : {
                  "day" : 2,
                  "time" : "1500"
               }
            },
            {
               "close" : {
                  "day" : 3,
                  "time" : "1930"
               },
               "open" : {
                  "day" : 3,
                  "time" : "1500"
               }
            },
            {
               "close" : {
                  "day" : 4,
                  "time" : "1930"
               },
               "open" : {
                  "day" : 4,
                  "time" : "1500"
               }
            },
            {
               "close" : {
                  "day" : 5,
                  "time" : "1930"
               },
               "open" : {
                  "day" : 5,
                  "time" : "1500"
               }
            },
            {
               "close" : {
                  "day" : 6,
                  "time" : "1930"
               },
               "open" : {
                  "day" : 6,
                  "time" : "1500"
               }
            }
         ]
'''
def parse(workingHours):
	newl=[0]*7
	for i in range(len(workingHours)):
		newl[i]={'listing_time_from':getTime(workingHours[i]["open"]["time"]),'listing_day':dayofweek[workingHours[i]['close']['day']],'listing_time_to':getTime(workingHours[i]["close"]["time"])}
	zeroes=newl.count(0)
	return finalparse(newl,zeroes)
def finalparse(newl,zeroes):
	for i in dayofweek:
		flag=0
		for j in range(len(newl)):
			if newl[j]!=0:
				if i==newl[j]['listing_day']:
					flag=1;
					break;
		if flag==0:
			newl[len(newl)-zeroes]={'listing_day':i,'listing_custom':'closed'}
			zeroes=zeroes-1
	return phpserialize.serialize(newl);
