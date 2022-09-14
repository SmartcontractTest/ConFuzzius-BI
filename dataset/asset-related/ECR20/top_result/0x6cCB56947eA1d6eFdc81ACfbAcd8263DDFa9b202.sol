import pandas as pd
from selenium import webdriver
import pyperclip
import time
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import  WebDriverWait

data = pd.read_csv('bad_tokens.top.csv')
data = data['addr'].values.tolist()
options = Options()
options.add_experimental_option('excludeSwitches', ['enable-automation'])
options.add_argument("--disable-blink-features=AutomationControlled")