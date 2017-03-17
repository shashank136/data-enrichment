import time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import File_3

from pyvirtualdisplay import Display

display = Display(visible=0, size=(800, 600))
display.start()


# Loops through all the pages and prints the data

def search_key(top):
    tip = top
    browser = webdriver.Firefox()
    my_url = 'http://cbseaff.nic.in/cbse_aff/schdir_Report/userview.aspx'
    browser.get(my_url)

    radio_key_word = browser.find_element_by_id("optlist_0")
    radio_key_word.click()

    time.sleep(6)

    search = browser.find_element_by_id('keytext')
    search.send_keys(tip)
    search.send_keys(Keys.RETURN)

    search.clear()
    time.sleep(6)

    # initial_url = 'http://cbseaff.nic.in/cbse_aff/schdir_Report/'

    while True:

        links = browser.find_elements_by_xpath("//tr/td/a")
        cheat = len(links)

        if cheat > 0:
            print len(links)
            size = len(links) + 1

            text = 'rep1_ctl'
            check1 = '_hyp'
            check2 = '_Hyperlink1'

            for no in range(1, size):
                # champ1 = 0
                if no < 10:
                    test1 = text + str(0) + str(no) + check1
                    test2 = text + str(0) + str(no) + check2
                else:
                    test1 = text + str(no) + check1
                    test2 = text + str(no) + check2
                try:
                    link = browser.find_element_by_id(test1).get_attribute("href")
                    # print link.get_attribute("href")
                    File_3.school_details(link)
                    print no
                    champ1 = 1


                except:
                    pass
                    champ1 = 0

                if champ1 == 0:
                    try:
                        link = browser.find_element_by_id(test2).get_attribute("href")
                        File_3.school_details(link)
                        print no
                        # print link.get_attribute("href")

                    except:
                        pass

            next_button = browser.find_element_by_id("Button1")
            next_button.click()

            time.sleep(6)

        else:
            break

    browser.quit()

    display.stop()
