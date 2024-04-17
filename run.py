import xlsxwriter
import csv
import posixpath
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager, ChromeType
from urllib.parse import urlparse

from bs4 import BeautifulSoup

def init_driver():
  caps = DesiredCapabilities().CHROME
  caps["pageLoadStrategy"] = 'normal' #'normal'|'eager'

  options = webdriver.ChromeOptions()
  options.headless = True
  options.add_argument("--disable-blink-features")
  options.add_argument("--disable-blink-features=AutomationControlled")
  options.add_experimental_option("excludeSwitches", ["enable-automation"])
  options.add_experimental_option('useAutomationExtension', False)
  options.add_argument('--blink-settings=imagesEnabled=false')

  driver = webdriver.Chrome(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install(), options=options, desired_capabilities=caps)
  driver.set_window_size(3840, 2160)
  return driver

def init_data():
  info = {}
  with open('input/data_1704.csv', 'r', encoding='utf-8') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    next(csv_reader, None)
    for row in csv_reader:
      info[row[2]] = row[3]
  return info

def test_data():
  info = []
  with open('input/test.csv', 'r', encoding='utf-8') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    # next(csv_reader, None)
    # for i in range(0, 580 + 611 + 953 + 82 + 349 + 1258 + 348 + 687 + 70 + 223 + 91 + 50 + 27 + 17 + 865 + 413 + 142):
    #   next(csv_reader, None)
    for row in csv_reader:
      if len(row) > 0:
        info.append(row[0])
  return info

def crawling(url):
  driver = init_driver()
  driver.get(url)
  driver.save_screenshot('a.png')

  soup = BeautifulSoup(driver.page_source, 'html.parser')
  channel_info_DOM = soup.find('div', class_='channel-info-content')
  if channel_info_DOM is None:
    print('Channel info not found')
    return None

  # go to about section -> Get social DOM
  res = {}
  about_DOM = channel_info_DOM.find('div', class_='about-section')
  social_DOM_s = about_DOM.find_all('div', class_='social-media-link')
  for about_DOM in social_DOM_s:
    social_a_DOM = about_DOM.find('a', href=True, role='link')
    social_url = social_a_DOM.get('href')
    social_name = social_a_DOM.find('p').text
    res[f'{social_name}_{urlparse(social_url).netloc}'] = social_url

  # other link
  urls = []
  channel_panel_DOM = channel_info_DOM.find('div', class_='channel-panels-container')
  if channel_panel_DOM is None:
    res['other'] = []
  else:
    panel_url_DOM_s = channel_panel_DOM.find_all('a', href=True)
    for panel_url_DOM in panel_url_DOM_s:
      urls.append(panel_url_DOM.get('href'))
    res['other'] = urls

  driver.close()

  return res

def write_file(worksheet, data: dict, count: int):
  for key, item in data.items():
    if key == 'name':
      worksheet.write(f'A{count}', item)
    elif 'twitch' in item or 'twitch' in key.lower():
      worksheet.write(f'B{count}', item)
    # elif 'youtube' in item or 'youtube' in key.lower():
    #   worksheet.write(f'C{count}', item)
    elif 'twitter' in item or 'twitter' in key.lower():
      worksheet.write(f'D{count}', item)
    # elif 'discord' in item or 'discord' in key.lower():
    #   worksheet.write(f'E{count}', item)
    # elif 'facebook' in item or 'facebook' in key.lower():
    #   worksheet.write(f'F{count}', item)
    # elif 'instagram' in item or 'instagram' in key.lower():
    #   worksheet.write(f'G{count}', item)
    # elif 'tiktok' in item or 'tiktok' in key.lower():
    #   worksheet.write(f'H{count}', item)
    # elif 'reddit' in item or 'reddit' in key.lower():
    #   worksheet.write(f'I{count}', item)
    # elif 'streamelements' in item or 'streamelements' in key.lower():
    #   worksheet.write(f'J{count}', item)
    # elif 'streamlabs' in item or 'streamlabs' in key.lower():
    #   worksheet.write(f'K{count}', item)
    elif key == 'other':
      if not any([key for key in data.keys() if 'twitter' in key.lower()]):
        twitch_urls = [url for url in item if 'twitter' in url.lower()]
        print(twitch_urls)
        if len(twitch_urls) > 0:
          print(f'---FROM OTHER---> {twitch_urls}')
          worksheet.write(f'D{count}', ','.join(twitch_urls))
    # else:
      # data['other'].append(item)
      # print(key, item)
      # worksheet.write(f'L{count}', ','.join(data['other']))


if __name__ == '__main__':
  channel_info_s = init_data()
  name_info_s = test_data()

  # for name, url in channel_info_s.items():
  #   if name not in name_info_s:
  #     print(name, url)

  workbook   = xlsxwriter.Workbook('twitch_social_urls.xlsx')
  worksheet = workbook.add_worksheet()

  try:
    count = 0
    for id, (name, url) in enumerate(channel_info_s.items()):
      if name not in name_info_s:
        about_url = posixpath.join(url, 'about')
        # count = id + 1
        count += 1
        print(f'----> Crawling {count} ...: {about_url}')
        res = crawling(about_url)
        print(res)
        if res is None:
          continue
        res['name'] = name
        res['twitch'] = url
        write_file(worksheet, res, count)
        time.sleep(0.5)
  except Exception as error:
    print(error)

  workbook.close()
