'''
    "mon_1_open": "10:00",
    "mon_1_close": "20:00",
    "tue_1_open": "10:00",
    "tue_1_close": "20:00",
    "wed_1_open": "10:00",
    "wed_1_close": "20:00",
    "thu_1_open": "10:00",
    "thu_1_close": "20:00",
    "fri_1_open": "10:00",
    "fri_1_close": "20:00",
    "sat_1_open": "10:00",
    "sat_1_close": "20:00",
    "sun_1_open": "10:00",
    "sun_1_close": "20:00"
    '''
from phpserialize import serialize
from parseGWorkHours import getTime

dayofweek=['SUNDAY','MONDAY','TUESDAY','WEDNESDAY','THURSDAY','FRIDAY','SATURDAY']
final_list=[]
def parse(diction):
    for i in dayofweek:
        tOpen,tClose = diction.get(i.lower()[:3]+'_1_open'), diction.get(i.lower()[:3]+'_1_close')
        
        if tOpen and tClose:
            try:
                tOpen,tClose = getTime(tOpen.replace(':','')), getTime(tClose.replace(':',''))
            except:
                print "Possible bad format: %s, %s"%(tOpen,tClose)
            final_list.append({'listing_time_from': tOpen, 'listing_day': i, 'listing_time_to': tClose})
        else:
            final_list.append({'listing_custom': 'closed', 'listing_day': i})
            
    return serialize(final_list)
            
        
