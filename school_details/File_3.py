from urllib2 import urlopen as uReq
from bs4 import BeautifulSoup as soup
import re


def school_details(new_url):
    my_url = new_url

    # opening up the connection, grabbing the page
    newClient = uReq(my_url)
    new_page_html = newClient.read()
    newClient.close()

    # html parsing
    new_page_soup = soup(new_page_html, "html.parser")

    new_container = new_page_soup.findAll('td', {"width": "494"})

    # getting school_name, Afilliation_no, Addresss, Phone_no, email_id

    school_name = new_container[0].text.strip()
    affiliation_no = new_container[1].text.strip()
    state = new_container[2].text.strip()
    district = new_container[3].text.strip()
    postal_address = new_container[4].text.strip()
    pin_code = new_container[5].text.strip()
    phone_no = new_container[7].text.strip()
    email_id = new_container[10].text.strip()
    web_site = new_container[11].text.strip()
    year_of_foundation = new_container[12].text.strip()
    date_of_opening = new_container[13].text.strip()
    name_of_principal = new_container[14].text.strip()
    sex = new_container[15].text.strip()
    status_of_school = new_container[20].text.strip()
    type_of_affiliation = new_container[21].text.strip()
    affiliation_period_from = new_container[22].text.strip()
    affiliation_period_to = new_container[23].text.strip()
    name_of_trust_society_managing_committee = new_container[24].text.strip()

    # formatting the data
    new_school_name = '\"' + school_name + '\"'
    new_affiliation_no = '\"' + affiliation_no + '\"'
    new_state = '\"' + state + '\"'
    new_district = '\"' + district + '\"'
    new_pin_code = '\"' + pin_code + '\"'
    new_year_of_foundation = '\"' + year_of_foundation + '\"'
    new_phone_no = '\"' + phone_no + '\"'
    new_postal_address = '\"' + postal_address + '\"'
    new_email_id = '\"' + email_id + '\"'
    new_web_site = '\"' + web_site + '\"'
    new_date_of_opening = '\"' + date_of_opening + '\"'
    new_name_of_principal = '\"' + name_of_principal + '\"'
    new_status_of_school = '\"' + status_of_school + '\"'
    new_type_of_affiliation = '\"' + type_of_affiliation + '\"'
    new_affiliation_period_from = '\"' + affiliation_period_from + '\"'
    new_name_of_trust_society_managing_committee = '\"' + name_of_trust_society_managing_committee + '\"'

    updated_affiliation_period_to = re.sub(' +', ' ', affiliation_period_to)
    test_updated_affiliation_period_to = updated_affiliation_period_to.replace('\n', '')
    check_updated_affiliation_period_to = test_updated_affiliation_period_to.replace('\t', '')
    new_affiliation_period_to = '\"' + check_updated_affiliation_period_to + '\"'

    # printing the data

    print '------------------------------------------------------------------------------------------------------------'
    print 'school_name    : ' + new_school_name
    print 'affiliation_no : ' + new_affiliation_no
    print 'Address        : ' + new_postal_address + ',' + new_district + ',' + new_state
    print 'pin            : ' + new_pin_code
    print 'phone_no       : ' + new_phone_no
    print 'email_id       : ' + new_email_id
    print 'web_site       : ' + new_web_site
    print 'year_of_foundation : ' + new_year_of_foundation
    print 'date_of_opening : ' + new_date_of_opening
    print 'name_of_principal : ' + new_name_of_principal
    print 'Sex              : ' + sex
    print 'status_of_school  : ' + new_status_of_school
    print 'type_of_affiliation : ' + new_type_of_affiliation
    print 'affiliation_period_from : ' + new_affiliation_period_from
    print 'affiliation_period_to : ' + new_affiliation_period_to
    print 'name_of_trust_society_managing_committee : ' + new_name_of_trust_society_managing_committee
    print '------------------------------------------------------------------------------------------------------------'

    filename = "shashank_kumar.csv"
    f = open(filename, "a")
    f.write(
        new_school_name + "," + new_affiliation_no + "," + new_state + "," + new_district + "," + new_postal_address + "," + new_pin_code + "," + new_phone_no + "," + new_email_id + "," + new_web_site + "," + new_year_of_foundation + "," + new_date_of_opening + "," + new_name_of_principal + "," + sex + "," + new_status_of_school + "," + new_type_of_affiliation + "," + new_affiliation_period_from + "," + new_affiliation_period_to + "," + new_name_of_trust_society_managing_committee + "\n")

    f.close()
