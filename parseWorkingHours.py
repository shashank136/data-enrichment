import re
import phpserialize

def parseDate(unparsed_schedule):
    results = {}

    sunday = "sunday"
    monday = "monday"
    tuesday = "tuesday"
    wednesday = "wednesday"
    thursday = "thursday"
    friday = "friday"
    saturday = "saturday"
    daysInWeek = [sunday,monday,tuesday,wednesday,thursday,friday,saturday];

    dayPattern = "?:";
    for dayInWeek in daysInWeek:
        dayPattern+= dayInWeek + "|";
        results[dayInWeek] = DayOfWeek(dayInWeek,dayInWeek+"starttime",dayInWeek+"endtime",None,None);

    dayPattern = dayPattern[:-1];

    timePattern = "?:\d{1,2}(?:[:|\.]\d{1,2})?)\s*(?:[ap][\.]?m\.?";

    dict = {'weekdayPattern': dayPattern,
            'timeHoursPattern': timePattern}

    # Day Pattern
    pattern = """
    ({weekdayPattern}) #Start day
    \s*[-|to]*\s* # Seperator
    ({weekdayPattern})?  #End day
    \s*[from|:]*\s* # Seperator
    ({timeHoursPattern}) # Start hour
    \s*[-|to]+\s* # Seperator
    ({timeHoursPattern}) # Close hour
    """.format(**dict)

    regEx = re.compile(pattern, re.IGNORECASE | re.VERBOSE)

    regExResults = re.findall(regEx, unparsed_schedule);

    #print(regExResults);

    for result in regExResults:
        myPattern = """
    (({weekdayPattern})) #Start day
    \s*([-|to])*\s* # Seperator
    (({weekdayPattern}))?  #End day
    \s*([from|:])*\s* # Seperator
    (({timeHoursPattern})) # Start hour
    \s*([-|to])+\s* # Seperator
    (({timeHoursPattern})) # Close hour
    """.format(**dict)
        m = re.match(myPattern, result, re.IGNORECASE | re.VERBOSE);
        if m:
            daySeperator = m.group(2);
            if (daySeperator and (daySeperator.find("-")!=-1)):
                startDay = m.group(1).lower();
                startDayIndex = index_of(daysInWeek,startDay);
                endDay = m.group(3).lower();
                enddayIndex = index_of(daysInWeek,endDay);
                startTime = m.group(5);
                endTime = m.group(7);
                if(enddayIndex<startDayIndex):
                    enddayIndex = enddayIndex + 7;
                for i in range(startDayIndex,enddayIndex+1):
                    if i>=7 :
                        currentDayIndex = i-7;
                    else:
                        currentDayIndex = i;
                    currentDayName = daysInWeek[currentDayIndex];
                    results[currentDayName].startingtime = startTime;
                    results[currentDayName].closingtime = endTime;
            else:
                currentDayName = m.group(1).lower();
                startTime = m.group(5);
                endTime = m.group(7);
                results[currentDayName].startingtime = startTime;
                results[currentDayName].closingtime = endTime;

    # If no valid results will return empty list
    #print(';'.join(str(v) for k,v in results.items()));
    return results

def index_of(stringArray, currentStr):
    for idx,str in enumerate(stringArray):
        m = re.match(str, currentStr, re.IGNORECASE | re.VERBOSE);
        if m:
            return idx;

def parseWorkingHours(workinghoursString):
    parsedObjects = parseDate(workinghoursString);
    resultString = serializeParseDate(parsedObjects);
    #print(resultString);
    return resultString;

def interactive_test():
    """Sets up an interactive loop for testing date strings."""
    parseWorkingHours("Monday - Saturday: 10 AM - 7 PM");
    parseWorkingHours("Sunday: 10 AM - 3 PM");
    parseWorkingHours("Monday - Saturday: 8 AM - 7 PM, Sunday: 9 AM - 3 PM");
    parseWorkingHours("Monday - Sunday: 9.30 AM - 6 PM");

    print("----")
    # print res.dump()


class DayOfWeek(object):
    def __init__(self, dayName, startTimeString, endTimeString, startTime, closeTime):
        self.dayName = dayName;
        self.startingtime = startTime;
        self.closingtime = closeTime;
        self.startTimeString = startTimeString;
        self.endTimeString = endTimeString;

    def __str__(self):
        if self.startingtime:
            return self.dayName+": From "+self.startingtime+" to "+self.closingtime+".";
        else:
            return self.dayName;

def serializeParseDate(dayObjects):
    openingHoursArray = [];
    for (key, value) in dayObjects.items():
        openingHours = {};
        openingHours["listing_day"] = value.dayName.upper();
        if value.startingtime != None:
            openingHours["listing_time_from"] = value.startingtime;
        if value.closingtime != None:
            openingHours["listing_time_to"] = value.closingtime;
        if value.startingtime == None or value.closingtime == None:
            openingHours["listing_custom"] = "closed";
        openingHoursArray.append(openingHours);
    serializedOpeningHours = phpserialize.serialize(openingHoursArray);
    print(serializedOpeningHours);

def formatParseDate(dayObjects):
    output = """
    a:7:{i: 0;
    a:4:{s: 11:"listing_day";
    s:6:"MONDAY";
    s:17:"listing_time_from";
    s:8:"mondaystarttime";
    s:15:"listing_time_to";
    s:8:"mondayendtime";
    s:14:"listing_custom";
    s:0:"";}i:1;
    a:4:{s: 11:"listing_day";
    s:7:"TUESDAY";
    s:17:"listing_time_from";
    s:8:"tuesdaystarttime";
    s:15:"listing_time_to";
    s:8:"tuesdayendtime";
    s:14:"listing_custom";
    s:0:"";}i:2;
    a:4:{s: 11:"listing_day";
    s:9:"WEDNESDAY";
    s:17:"listing_time_from";
    s:8:"wednesdaystarttime";
    s:15:"listing_time_to";
    s:8:"wednesdayendtime";
    s:14:"listing_custom";
    s:0:"";}i:3;
    a:4:{s: 11:"listing_day";
    s:8:"THURSDAY";
    s:17:"listing_time_from";
    s:8:"thursdaystarttime";
    s:15:"listing_time_to";
    s:8:"thursdayendtime";
    s:14:"listing_custom";
    s:0:"";}i:4;
    a:4:{s: 11:"listing_day";
    s:6:"FRIDAY";
    s:17:"listing_time_from";
    s:8:"fridaystarttime";
    s:15:"listing_time_to";
    s:8:"fridayendtime";
    s:14:"listing_custom";
    s:0:"";}i:5;
    a:4:{s: 11:"listing_day";
    s:8:"SATURDAY";
    s:17:"listing_time_from";
    s:8:"saturdaystarttime";
    s:15:"listing_time_to";
    s:8:"sarturdayendtime";
    s:14:"listing_custom";
    s:0:"";}i:6;
    a:2:{s: 11:"listing_day";
    s:6:"SUNDAY";
    s:17:"listing_time_from";
    s:8:"sundaystarttime";
    s:15:"listing_time_to";
    s:8:"sundayendtime";
    s:14:"listing_custom";
    s:6:"closed";}}
    """
    for (key,value) in dayObjects.items():
        if(value.startingtime):
            output = output.replace(value.startTimeString, value.startingtime);
        if(value.closingtime):
            output = output.replace(value.endTimeString, value.closingtime);

    #print(output);
    return re.sub('[\s+]', '', output);

if __name__ == '__main__':
    interactive_test();
