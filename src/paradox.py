from selenium.webdriver.common.keys import Keys
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
import sys, select, os
import boto3
import json
from time import sleep
import datetime
from pyvirtualdisplay import Display

def get_array_from_source(array_name, sources):
    my_array = []
    if '{} = new Array('.format(array_name) in sources:
        i = sources.find('{} = new Array('.format(array_name))
        i += len('{} = new Array('.format(array_name))
        f = sources.find(')',i)
        if (i > -1) and (f > i):
            my_array = sources[i:f].split(',')
    return my_array

def paradox_login(driver, ipaddress, usercode, password):

    print('Opening Paradox at address: {}'.format(ipaddress))
    driver.get('http://{}'.format(ipaddress))

    print('Waiting a moment..')
    sleep(5)

    if "Solo un collegam. per volta" in driver.page_source:
        print('Server in use. Exit.')
        return False

    if "Benvenuto" not in driver.page_source:
        #Login
        print('Login..')
        user_elem = driver.find_element_by_id("user")
        pass_elem = driver.find_element_by_id("pass")
        user_elem.clear()
        user_elem.send_keys(usercode)
        pass_elem.clear()
        pass_elem.send_keys(password)
        pass_elem.send_keys(Keys.RETURN)

    return True

def paradox_polling():

    options = Options()
    options.headless = True

    # Set screen resolution to 1366 x 768 like most 15" laptops
    display = Display(visible=0, size=(1366, 768))
    display.start()

    driver = webdriver.Firefox(executable_path='/usr/local/bin/geckodriver', options=options)

    ipaddress = os.environ['PARADOX_IPADDRESS']
    if not paradox_login(driver, ipaddress, os.environ['PARADOX_USERCODE'], os.environ['PARADOX_PASSWORD']):
        print('Login failed.')
        driver.quit()
        exit()

    producer = boto3.client('firehose')

    try:
       
        #Getting Info
        print('Getting info..')
        driver.get('http://{}/index.html'.format(ipaddress))
        sleep(2)
        area_name = get_array_from_source('tbl_areanam', driver.page_source)
        area_name = [x.replace('"', '') for x in area_name]
        print('Area Name: {}'.format(area_name))

        zone_name = get_array_from_source('tbl_zone', driver.page_source)
        zone_name = [x.replace('"', '') for x in zone_name]
        zone_name = [x.replace(' ', '_') for x in zone_name]
        print('Zone Name: {}'.format(zone_name))

        if len(area_name) == 0:
            print('Server in use. Exit.')
            driver.quit()
            exit()

        if 'KEYPRESS_CHECK' in os.environ:
            print('Starting loop. Press ENTER to exit.')
        stay = True

        zone_status, last_zone_status = [],[]
        area_status, last_area_status = [],[]

        while stay:
            sleep(1)

            driver.get('http://{}/statuslive.html'.format(ipaddress))
            zone_status = get_array_from_source('tbl_statuszone', driver.page_source)
            zone_status = [int(x) for x in zone_status]
            area_status = get_array_from_source('tbl_useraccess', driver.page_source)
            area_status = [int(x) for x in area_status]

            if (len(zone_status) == 0) or (len(area_status) == 0):
                stay = False
            else:
                if (zone_status != last_zone_status) or (area_status != last_area_status):
                    print('Status Zone: {}'.format(zone_status))
                    print('Status Area: {}'.format(area_status))

                    firehose_record = {
                        'time': datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
                    }
                    for i in range(len(area_status)):
                        if area_status[i] != 0:
                            firehose_record['area.{}.{}'.format(i+1, area_name[i])] = area_status[i] 

                    for i in range(len(zone_name) // 2):
                        if int(zone_name[i*2]) != 0:
                            firehose_record['area.{}.zone.{}'.format(zone_name[i*2], zone_name[i*2+1])] = zone_status[i] 

                
                    response = producer.put_record(
                        DeliveryStreamName=os.environ['KINESIS_STREAM'],
                        Record={
                        'Data': json.dumps(firehose_record) + '\n'
                        }
                    )

            last_area_status = area_status
            last_zone_status = zone_status

            if 'KEYPRESS_CHECK' in os.environ:
                if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                    line = input()
                    break

    finally:
        print('Logout..')
        driver.get('http://{}/logout.html'.format(ipaddress))
        sleep(1)
        driver.quit()
        display,stop()

if __name__ == "__main__":
    paradox_polling()

    