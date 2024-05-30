import aiosqlite
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import asyncio
async def init_database():
    async with aiosqlite.connect('movies.db') as db:
        await db.execute("""CREATE TABLE IF NOT EXISTS action_and_drama(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            movie_title TEXT,
            date TEXT,
            season TEXT,
            link TEXT,
            country TEXT,
            image TEXT,
            rating TEXT)""")
        await db.commit()
async def add_data(title, date, season, link, country, image, rating):
    async with aiosqlite.connect('movies.db') as connection:
        cursor = await connection.cursor()
        await cursor.execute("""INSERT INTO action_and_drama (
                   movie_title,
                   date,
                   season,
                   link,
                   country,
                   image,
                   rating) VALUES (?, ?, ?, ?, ?, ?, ?)""",
                   (title, date, season, link, country, image, rating))
        await connection.commit()
async def scrape_page(session, page_number):
    base_url = 'https://www.awafim.tv/browse?q=&type=series&genre%5B%5D=Crime&genre%5B%5D=Drama&country%5B%5D=GBR&country%5B%5D=USA&page='
    url = base_url + str(page_number)
    async with session.get(url) as response:
        if response.status != 200:
            return False  # Stop if there's an issue with the request
        text = await response.text()
        soup = BeautifulSoup(text, 'html.parser')
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
                await add_data(f_head, f_date, f_season, link, f_country, f_image, f_rating)
            except Exception as e:
                print(f"An error occurred while processing an article: {e}")
        return True  # Continue to next page
async def main():
    await init_database()
    async with aiohttp.ClientSession() as session:
        page_number = 1
        while await scrape_page(session, page_number):
            print(f"Scraped page {page_number}")
            page_number += 1
            await asyncio.sleep(1)  # Be polite to the server by adding a delay
# Start the main function
asyncio.run(main())