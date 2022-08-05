import argparse
import os
import random
import subprocess
import time
import requests
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from faker import Faker
from faker_education import SchoolProvider
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions
import speech_recognition as sr

from fp.fp import FreeProxy


fake = Faker()
fake.add_provider(SchoolProvider)

form_url = 'https://www.localalabama.org/content-report-form'
# Adds /usr/local/bin to my path which is where my ffmpeg is stored
os.environ["PATH"] += ":/usr/local/bin"

CLOUD_DESCRIPTION = 'Puts script in a \'cloud\' mode where the Chrome GUI is invisible'
CLOUD_DISABLED = False
CLOUD_ENABLED = True
CAPTCHA_BOX = 'recapBorderAccessible'
AUDIO_ERROR_MESSAGE = 'rc-audiochallenge-error-message'
CAPTCHA_MP3_FILENAME = 'captchaAudio/1.mp3'
CAPTCHA_WAV_FILENAME = 'captchaAudio/2.wav'
RECAPTCHA_AUDIO_BUTTON = 'recaptcha-audio-button'
RECAPTCHA_ANCHOR = 'recaptcha-anchor'
AUDIO_SOURCE = 'audio-source'
AUDIO_RESPONSE = 'audio-response'

SCRIPT_DESCRIPTION = ''

parser = argparse.ArgumentParser(SCRIPT_DESCRIPTION)
parser.add_argument('--cloud', action='store_true', default=CLOUD_DISABLED,
                    required=False, help=CLOUD_DESCRIPTION, dest='cloud')
args = parser.parse_args()


def start_driver():
    #PROXY = FreeProxy(country_id=['US'],  timeout=0.3, rand=True).get()
    chrome_options = webdriver.ChromeOptions()
    if (args.cloud == CLOUD_ENABLED):

        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--allow-running-insecure-content')
        user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.50 Safari/537.36'
        chrome_options.add_argument(f'user-agent={user_agent}')
        #chrome_options.add_argument('--proxy-server=%s' % PROXY)
        driver = webdriver.Chrome('chromedriver', options=chrome_options)
    else:

        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        # chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--allow-running-insecure-content')
        user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.50 Safari/537.36'
        #chrome_options.add_argument('--proxy-server=%s' % PROXY)
        driver = webdriver.Chrome(
            ChromeDriverManager().install(), options=chrome_options)

    driver.get(form_url)
    time.sleep(2)
    return driver


r = sr.Recognizer()


def audioToText(mp3Path):
    # deletes old file
    try:
        os.remove(CAPTCHA_WAV_FILENAME)
    except FileNotFoundError:
        pass
    # convert wav to mp3
    subprocess.run(
        f"ffmpeg -i {mp3Path} {CAPTCHA_WAV_FILENAME}", shell=True, timeout=5)

    with sr.AudioFile(CAPTCHA_WAV_FILENAME) as source:
        audio_text = r.listen(source)
        try:
            text = r.recognize_google(audio_text)
            print(f'Converting audio transcripts into text ...')
            return(text)
        except Exception as e:
            print(e)
            print(f'Sorry.. run again...')


def saveFile(content, filename):
    with open(filename, "wb") as handle:
        for data in content.iter_content():
            handle.write(data)
# END TEST


def solveCaptcha(driver):
    # Logic to click through the reCaptcha to the Audio Challenge, download the challenge mp3 file, run it through the audioToText function, and send answer
    #googleClass = driver.find_elements(By.CCAPTCHA_BOX)[0]
    #googleClass = driver.find_element(By.XPATH, "//iframe[@title='reCAPTCHA']")
    # time.sleep(2)
    #outeriframe = googleClass.find_element_by_tag_name('iframe')
    WebDriverWait(driver, 10).until(
        expected_conditions.presence_of_element_located((By.XPATH, "//iframe[@title='reCAPTCHA']")))
    outeriframe = driver.find_element(By.XPATH, "//iframe[@title='reCAPTCHA']")
    time.sleep(1)
    outeriframe.click()
    time.sleep(2)
    allIframesLen = driver.find_elements(By.TAG_NAME, 'iframe')
    time.sleep(1)
    audioBtnFound = False
    audioBtnIndex = -1
    for index in range(len(allIframesLen)):
        driver.switch_to.default_content()
        iframe = driver.find_elements(By.TAG_NAME, 'iframe')[index]
        driver.switch_to.frame(iframe)
        driver.implicitly_wait(2)
        try:
            audioBtn = driver.find_element(By.ID,
                                           RECAPTCHA_AUDIO_BUTTON) or driver.find_element(By.ID, RECAPTCHA_ANCHOR)
            audioBtn.click()
            audioBtnFound = True
            audioBtnIndex = index
            break
        except Exception as e:
            pass
    if audioBtnFound:
        try:
            while True:
                """
                try:
                    time.sleep(3)
                    WebDriverWait(driver, 20).until(expected_conditions.presence_of_element_located((By.ID, AUDIO_SOURCE)))
                except Exception as e:
                    print(f"Waiting broke lmao {e}")
                """

                try:
                    time.sleep(3)
                    WebDriverWait(driver, 20).until(
                        expected_conditions.presence_of_element_located((By.ID, AUDIO_SOURCE)))
                except Exception as e:
                    print(f"Waiting broke lmao {e}")

                # driver.implicitly_wait(10)
                href = driver.find_element(By.ID,
                                           AUDIO_SOURCE).get_attribute('src')
                response = requests.get(href, stream=True)
                saveFile(response, CAPTCHA_MP3_FILENAME)
                response = audioToText(CAPTCHA_MP3_FILENAME)
                print(response)
                driver.switch_to.default_content()
                iframe = driver.find_elements(By.TAG_NAME, 'iframe')[
                    audioBtnIndex]
                driver.switch_to.frame(iframe)
                inputbtn = driver.find_element(By.ID, AUDIO_RESPONSE)
                inputbtn.send_keys(response)
                inputbtn.send_keys(Keys.ENTER)
                time.sleep(2)
                errorMsg = driver.find_elements(By.CLASS_NAME,
                                                AUDIO_ERROR_MESSAGE)[0]
                if errorMsg.text == "" or errorMsg.value_of_css_property('display') == 'none':
                    print(f"reCaptcha defeated!")
                    break
        except Exception as e:
            print(e)
            print(f'Oops, something happened. Check above this message for errors or check the chrome window to see if captcha locked you out...')
    else:
        print(f'Button not found. This should not happen.')

    time.sleep(2)
    driver.switch_to.default_content()


def pick_teacher():
    prefixs = ['Mr', 'Mrs', 'Ms', 'Dr', 'Prof']
    suffixs = ['Jr', 'Sr', 'II', 'III', 'IV', 'V']
    teacher = random.choice(prefixs) + \
        f' {fake.name()} ' + random.choice(suffixs)
    return teacher


def rand_grade():
    grades = ['K', '1', '2', '3', '4', '5',
              '6', '7', '8', '9', '10', '11', '12']
    return random.choice(grades)


def fill_form(driver):
    email = fake.email()
    driver.find_element(By.ID, 'input_comp-kyjjs2d5').send_keys(email)
    #time.sleep(random.randint(0, 2))
    driver.find_element(By.ID, 'input_comp-kyjjs2da').send_keys(email)
    #time.sleep(random.randint(0, 2))
    driver.find_element(By.ID,
                        'input_comp-kyjjs2de').send_keys(fake.school_name())
    #time.sleep(random.randint(0, 2))
    driver.find_element(By.ID, 'input_comp-kyjjs2di').send_keys(pick_teacher())
    #time.sleep(random.randint(0, 2))
    driver.find_element(By.ID, 'input_comp-kyjjs2dm1').send_keys(rand_grade())
    #time.sleep(random.randint(0, 2))

    driver.find_element(
        By.XPATH, '/html/body/div/div/div[3]/div/main/div/div/div/div[2]/div/div/div/section/div[2]/div/div[2]/div/section/div[2]/div/div[2]/div/div[2]/div/div/form/div/div/div[6]/div/div').click()

    i = 0

    while (i < 10) and (not bool(driver.find_elements(By.CLASS_NAME, '_1gCtg'))):
        time.sleep(1)
        i += 1

    # if driver.find_elements(By.CLASS_NAME, '_1gCtg') != []:

    random.choice(driver.find_elements(By.CLASS_NAME, '_1gCtg')).click()

    time.sleep(random.randint(0, 2))
    cbs = driver.find_elements(By.XPATH, "//input[@type='checkbox']")

    for cb in cbs:
        if random.randint(0, 100) > 50:
            cb.click()

    driver.find_element(
        By.XPATH, '//*[@id="textarea_comp-kyjjs2ej"]').send_keys(fake.address())

    driver.find_element(By.XPATH, '//*[@id="comp-kyjjs2f41"]/button').click()

    time.sleep(1)

    try:
        solveCaptcha(driver)
    except:
        try:
            driver.find_element(
                By.XPATH, '//*[@id="comp-kyjjs2ff"]/span/p/span')
            print("Successfully submitted form")
            count_form()
        except:
            print(driver.page_source)
            print("Captcha not found or failed to solve")
        return
    # print(driver.page_source)

    # driver.find_element(By.ID, 'input_comp-kyjjs2ej').send_keys('bad things')
    # driver.find_element(By.ID, 'input_comp-kyjjs2ev').send_keys('oilsprite.png')


def count_form():
    requests.post("http://change-is-brewing.herokuapp.com/alabamaCRT")


# send_tip()
if __name__ == '__main__':
    while True:
        driver = start_driver()
        fill_form(driver)
        time.sleep(3)
