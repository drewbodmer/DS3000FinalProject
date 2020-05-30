import requests
import bs4.element
from bs4 import BeautifulSoup
import time
r = requests.get('https://store.steampowered.com/search/?filter=globaltopsellers&os=win')

soup = BeautifulSoup(r.text, 'html.parser')

resultsRow = soup.find_all('a', {'class': 'search_result_row'})
results = []

for resultRow in resultsRow:
    gameURL = resultRow.get('href')
    title = resultRow.find('span', {'class': 'title'}).text
    releaseDate = resultRow.find('div', {'class': 'search_released'}).text
    price = None
    r = resultRow.find('span', {'class': 'search_review_summary'})
    if r is not None:
        review = r.get('data-tooltip-html')
    discountedPrice = None
    time.sleep(.1)
    gr = requests.get(gameURL)
    gsoup = BeautifulSoup(gr.text, 'html.parser')
    gamedetails = gsoup.find_all('div', {'class': 'details_block'})
    if len(gamedetails) > 0:
        details = {}
        btags = gamedetails[0].find_all('b')
        for item in btags:
            og = item
            children = []
            while str(item) != '<br/>' and item.next_sibling is not None:
                if type(item.next_sibling) == bs4.element.NavigableString:
                    sibling = ''.join(c for c in str(item.next_sibling) if c.isalnum())
                    if sibling != '':
                        children.append(sibling)
                elif type(item.next_sibling) == bs4.element.Tag:
                    if str(item.next_sibling.text) != '':
                        children.append(item.next_sibling.text)
                item = item.next_sibling

                details[og.text] = children
                
        # finding the number of reviews and percentage that are positive
        ratings = gsoup.find_all("span", class_ = "nonresponsive_hidden responsive_reviewdesc")
        if len(ratings) > 0:
            rating_percentage = ratings[-1].get_text().strip().split(" ")[1]
        else:
            rating_percentage = "No Rating"
        
        num_ratings = gsoup.find("meta", {"itemprop": "reviewCount"})
        if num_ratings != None:
            num_ratings = int(num_ratings.get("content"))
        else:
            num_ratings = 0
            
        details["Number of Ratings"] = num_ratings
        details["Percentage of Positive Reviews"] = rating_percentage
        
        print(details)
    break
