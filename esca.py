import requests
from bs4 import BeautifulSoup
import sqlite3
from urllib.parse import urljoin
import time

base_url = 'https://www.awafim.tv/browse?q=&type=series&genre%5B%5D=Crime&genre%5B%5D=Drama&country%5B%5D=GBR&country%5B%5D=USA&page='

def init_database():
    connection = sqlite3.connect('movies.db')
    cursor = connection.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS action_and_drama(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        movie_title TEXT,
        date TEXT,
        season TEXT,              
        link TEXT,
        country TEXT,
        image TEXT,
        rating TEXT
    )""")
    connection.commit()
    connection.close()

def add_data(title, date, season, link, country, image, rating):
    connection = sqlite3.connect('movies.db')
    cursor = connection.cursor()
    cursor.execute("""INSERT INTO action_and_drama (
                   movie_title,
                   date,
                   season,
                   link,
                   country,
                   image,
                   rating) VALUES (?, ?, ?, ?, ?, ?, ?)""",
                   (title, date, season, link, country, image, rating))
    connection.commit()
    connection.close()

def scrape_page(page_number):
    url = base_url + str(page_number)
    response = requests.get(url)
    if response.status_code != 200:
        return False  # Stop if there's an issue with the request
    
    soup = BeautifulSoup(response.text, 'html.parser')

    # Extract data and insert into the database
    articles = soup.find_all('article', {'class': 'titles-one'})
    if not articles:
        return False  # No more articles, end of pagination

    for data in articles:
        try:
            head = data.find('h3', {'class': 'to-h3'})
            f_head = head.text.strip() if head else 'N/A'
            
            date = data.find('div', {'class': 'toi-year'})
            f_date = date.text.strip() if date else 'N/A'
            
            season = data.find('div', {'class': 'toi-run'})
            f_season = season.text.strip() if season else 'N/A'
            
            link_tag = data.find('a')
            link = urljoin(base_url, link_tag['href']) if link_tag else 'N/A'
            
            country = data.find('div', {'class': 'toi-countries'})
            f_country = country.find('i')['class'][0] if country and country.find('i') else 'N/A'
            
            image = data.find('img', {'class': 'to-thumb'})
            f_image = image.get('src') if image else 'N/A'
            
            rating = data.find('span', {'class': 'stars-list'})
            f_rating = rating.get('title') if rating else 'N/A'
            
            add_data(f_head, f_date, f_season, link, f_country, f_image, f_rating)
        except Exception as e:
            print(f"An error occurred while processing an article: {e}")

    return True  # Continue to next page

# Initialize the database once
init_database()

# Start scraping from the first page
page_number = 1
while scrape_page(page_number):
    print(f"Scraped page {page_number}")
    page_number += 1
    time.sleep(1)  # Be polite to the server by adding a delay
