#
# '''
#
# import time
# import random
# import json
# import pandas as pd
# from bs4 import BeautifulSoup
# from selenium import webdriver
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.chrome.service import Service
# from webdriver_manager.chrome import ChromeDriverManager
# from fake_useragent import UserAgent
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.webdriver.common.by import By
# from selenium.common.exceptions import TimeoutException
# import re
#
#
# class PinnacleParser:
#     def __init__(self, base_url, stats_matching, output_dir='data'):
#         self.base_url = base_url
#         self.stats_matching = stats_matching
#         self.output_dir = output_dir
#         self.driver = None
#
#     def init_driver(self):
#         """Инициализация Selenium WebDriver."""
#         ua = UserAgent()
#         chrome_options = Options()
#         chrome_options.add_argument('--ignore-certificate-errors')
#         chrome_options.add_argument('--allow-insecure-localhost')
#         chrome_options.add_argument(f'user-agent={ua.random}')
#         self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
#
#     def quit_driver(self):
#         """Закрытие драйвера."""
#         if self.driver:
#             self.driver.quit()
#
#     def get_match_links(self):
#         """Получение списка ссылок на матчи."""
#         self.init_driver()
#         try:
#             self.driver.get(self.base_url)
#             time.sleep(random.uniform(10, 20))
#             html_content = self.driver.page_source
#             soup = BeautifulSoup(html_content, 'html.parser')
#
#             match_links = set()
#             pattern = r'/en/hockey/nhl/[^/]+-vs-[^/]+/\d+/'
#
#             for a in soup.find_all('a', href=True):
#                 match = re.search(pattern, a['href'])
#                 if match:
#                     match_links.add(match.group())
#
#             return list(match_links)
#         finally:
#             self.quit_driver()
#
#     def parse_match_data(self, link, max_retries=3):
#         """Парсинг данных одного матча."""
#         self.init_driver()
#         try:
#             full_url = f"https://52.51.47.88:16869{link}#player-props"
#             for attempt in range(max_retries):
#                 try:
#                     self.driver.get(full_url)
#                     WebDriverWait(self.driver, 30).until(
#                         EC.presence_of_element_located((By.CLASS_NAME, 'marketGroup-wMlWprW2iC'))
#                     )
#                     break
#                 except TimeoutException:
#                     if attempt < max_retries - 1:
#                         time.sleep(random.uniform(5, 10))
#                     else:
#                         print(f"Не удалось загрузить страницу: {full_url}")
#                         return []
#
#             match_html = self.driver.page_source
#             soup = BeautifulSoup(match_html, 'html.parser')
#             players_data = []
#
#             for group in soup.find_all('div', class_='marketGroup-wMlWprW2iC'):
#                 try:
#                     player_info = group.find('span', class_='titleText-BgvECQYfHf').text.strip()
#                     buttons = group.find_all('button', class_='market-btn')
#
#                     base_value, over_price, under_price = None, None, None
#                     for button in buttons:
#                         label = button.find('span', class_='label-GT4CkXEOFj').text.strip()
#                         price = button.find('span', class_='price-r5BU0ynJha').text.strip()
#
#                         if 'Over' in label:
#                             base_value = label.split(' ')[1]
#                             over_price = price
#                         elif 'Under' in label:
#                             under_price = price
#
#                     stats_key = player_info.split(' (')[-1].replace(')', '')
#
#                     try:
#                         base_value = float(base_value)
#                         over_price = float(over_price)
#                         under_price = float(under_price)
#
#                         if base_value > 0 and over_price > 1 and under_price > 1:
#                             players_data.append({
#                                 "Player": player_info.split(' (')[0],
#                                 "Stats": self.stats_matching.get(stats_key, stats_key),
#                                 "Base": base_value,
#                                 "Over": over_price,
#                                 "Under": under_price
#                             })
#                         else:
#                             print(f"Пропущены некорректные данные для игрока {player_info}")
#                     except (ValueError, TypeError):
#                         print(f"Ошибка при обработке данных для игрока {player_info}")
#                         continue
#
#                 except AttributeError:
#                     continue
#
#             return players_data
#         finally:
#             self.quit_driver()
#
#     def parse_all_matches(self, sleep_range=(5, 15), output_csv=None):
#         """
#         Парсинг всех матчей с главной страницы.
#         :param sleep_range: Кортеж (min, max) для случайной задержки между запросами.
#         :param output_csv: Если задано, сохраняет результат в указанный CSV файл.
#         :return: Список всех данных об игроках.
#         """
#         print("Получение ссылок на матчи...")
#         links = self.get_match_links()
#         print(f"Найдено ссылок на матчи: {len(links)}")
#
#         all_players_data = []
#         for link in links:
#             time.sleep(random.uniform(*sleep_range))
#             data = self.parse_match_data(link)
#             if data:
#                 all_players_data.extend(data)
#                 print(f"Данные для матча {link} успешно обработаны.")
#
#         if output_csv:
#             self.save_to_csv(all_players_data, output_csv)
#
#         return all_players_data
#
#     @staticmethod
#     def save_to_json(data, filename):
#         """Сохранение данных в JSON."""
#         with open(filename, 'w') as f:
#             json.dump(data, f)
#         print(f"Сохранено {len(data)} записей в {filename}")
#
#     @staticmethod
#     def save_to_csv(data, filename):
#         """Сохранение данных в CSV."""
#         df = pd.DataFrame(data)
#         df.to_csv(filename, index=False)
#         print(f"Сохранено данные в CSV: {filename}")
#
# '''
#
