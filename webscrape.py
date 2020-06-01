import requests
import bs4.element
from bs4 import BeautifulSoup
import time
import pandas as pd
from random import randint
import re

df = pd.DataFrame()

# loop through 10 pages of the steam website, each page storing 100 games
for start in range(0, 1000, 100):
    
    print("starting games starting at", start)
    
    # getting the url of the current page
    r = requests.get('https://store.steampowered.com/search/results/?query&start=' + str(start) + '&count=100')

    soup = BeautifulSoup(r.text, 'html.parser')

    # a list of all the rows in the table of games on this page
    resultsRow = soup.find_all('a', {'class': 'search_result_row'})
    results = []
    game_info = []

    for resultRow in resultsRow:
        # getting the url of the game
        gameURL = resultRow.get('href')
        
        title = resultRow.find('span', {'class': 'title'}).text
        releaseDate = resultRow.find('div', {'class': 'search_released'}).text
        price = None
        
        r = resultRow.find('span', {'class': 'search_review_summary'})
        if r is not None:
            review = r.get('data-tooltip-html')
        discountedPrice = None
        
        # sleeping to prevent banning and then getting the soup of the game
        time.sleep(.1)
        gr = requests.get(gameURL)
        gsoup = BeautifulSoup(gr.text, 'html.parser')
        gamedetails = gsoup.find_all('div', {'class': 'details_block'})
        if len(gamedetails) > 0:
            details = {}
            # getting all the b_tags which is where the game information is found
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

                    # adding the game detail to the dictionary
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


            # Gets the pricing info for the game

            if '%' in resultRow.find('div', {'class':'col search_discount responsive_secondrow'}).get_text():

                price = resultRow.find('strike').get_text()
                discount_chunk = resultRow.find('div', {'class':'col search_price discounted responsive_secondrow'})

                discount =''.join(discount_chunk.find('br').next_siblings)

                details['Price'] = price
                details['Discounted Price'] = discount


            elif '%' not in resultRow.find('div', {'class':'col search_discount responsive_secondrow'}).get_text():

                price = resultRow.find('div', {'class': 'col search_price responsive_secondrow'}).get_text()

                details['Price'] = price.strip()
                details['Discounted Price'] = 'N/A'



        # appending the information to the dataframe
        df = df.append(details, ignore_index = True)
        
    print("finished games starting at", start)
    
    # sleeping to prevent banning
    time.sleep(randint(2,10))
    
    
# dropping useless columns
df.drop(labels = "", axis = 1, inplace = True)
df.drop(labels = ["Languages\t\t\t\t\t\t\t\t\t\t:", "Languages:", "Manufacturer:", "Incorporates 3rd-party DRM:"], axis = 1, inplace = True)

# dropping games whose title was NaN
df = df.dropna(subset = ["Title:"]).reset_index(drop = True)

def fix_title(title):
    """
    The titles are currently stored in our dataframe in a list of size 1 with all the words mushed together.
    This method uses regex to separate the title based on capital letters
    """
    words = re.findall('[A-Z][^A-Z]*', title[0])
    final_str = ""
    for word in words:
        final_str += word + " "
    return final_str.strip()

# a dataframe of video game metacritic scores that we found online
metacritic = pd.read_csv("metacritic_game_info.csv")

def mush_title(title):
    """
    Takes in a properly formatted title and mushes all the words together by removing the spaces. It does this to
    ensure that the given title is formatted the same way it was in our original dataframe.
    """
    words = title.split(" ")
    mushed_title = ""
    for word in words:
        mushed_title += word
    return [mushed_title]

metacritic["Mushed Title"] = metacritic["Title"].apply(mush_title)

# Creating a column to merge the metacritic dataframe with the scraped dataframe
metacritic["Merge Title"] = metacritic["Mushed Title"].apply(fix_title)

df["Merge Title"] = df["Title:"].apply(fix_title)

# merging the dataframes on their "Merge Title" columns
combined = pd.merge(metacritic, df, left_on = "Merge Title", right_on = "Merge Title", how = "outer")

combined.drop(labels = ["Unnamed: 0", "Merge Title", "Mushed Title"], axis = 1, inplace = True)

# saving the dataframe to a csv
# NOTE: this dataframe is not fully cleaned up yet so there is future work to be done
combined.to_csv("fp2.csv")
