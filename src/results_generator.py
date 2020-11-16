"""Determines and saves results."""

import csv
from sentiment_analyzer import *
from search_scraper import *

from csv_handler import *
import bs4
import requests
from bs4 import BeautifulSoup

def temp_cml_interface():
    print("** Need to ask user for date range & if they have an existing CSV File.")
    websites = ["www.fool.com"]
    print("** Websites being used: ")
    stocks = input("** Enter your stocks, separated by commas: ")
    stock_abbrvs = input("** Enter your stock abbreviations, separated by commas, in the same order you entered the names above: ")

    start_date = input ("** Enter the START of the date range you want to use for article scraping: ")
    end_date = input ("** Enter the END of the date range you want to use for article scraping: ")

    generate_results(stocks, websites, start_date, end_date, stock_abbrvs)

def generate_results(stocks, websites, start_date, end_date, stock_abbrvs):
    stocks_list = []
    stocks_list = stocks.split(", ")
    abbrv_list = []
    abbrv_list = stock_abbrvs.split(", ")

    articles = analyze_all_articles(stocks, websites, start_date, end_date)

    scored_articles = calc_article_sent_scores(articles)
    #print("\n\nScored Articles:", scored_articles)

    scored_stocks = calc_stock_sentiment(scored_articles, stocks_list)
    # save run date to overall dict for csv purposes
    scored_stocks = calc_recent_stock_sentiment(scored_articles, scored_stocks)

    scored_stocks = calc_stock_trifold_rating(scored_articles, scored_stocks)

    scored_stocks = calc_ovr_stock_article_feelings(scored_articles, scored_stocks)
    print("\n\nScored Stocks", scored_stocks)
    write_data(scored_articles)

    scored_stocks = calc_ovr_media_rating(scored_articles, scored_stocks)
    print(scored_stocks)

    i = 0

    while i < len(scored_stocks):
        price, previous_close, open_price, avg_volume, volume = get_stock_attributes(abbrv_list[i])

        print('Current Stock Price is : $' + str(price))
        print('Previous Close was : $' + str(previous_close))
        print('Open Price of the Day was : $' + str(open_price))
        print('Current stock volume is : ' + str(volume))
        print('Average stock volume is : ' + str(avg_volume))

        print(scored_stocks[i])
        scored_stocks[i]['current_price'] = price
        scored_stocks[i]['volume'] = volume
        scored_stocks[i]['avg_volume'] = avg_volume
        print(scored_stocks[i])

        i += 1

def calc_article_sent_scores(articles):
    """Averages all sentence scores together, if multiple, and produces one averaged score for a body of text."""
    print("Calcuting text score....")
    for article in articles:
        #ovr_text_sent_score
        ovr_text_sent_score = 0
        sent_count = 0
        print("LEN", len(article['text_sent']))
        for txsent in article['text_sent']:
            sent_count += 1
            print("COMPOUND", txsent['compound'])
            ovr_text_sent_score += txsent['compound']
        ovr_text_sent_score = ovr_text_sent_score / sent_count

        #ovr_title_sent_score
        ovr_title_sent_score = 0
        sent_count = 0
        for tisent in article['title_sent']:
            sent_count += 1
            print("COMPOUND", tisent['compound'])
            ovr_title_sent_score += tisent['compound']
        ovr_title_sent_score = ovr_title_sent_score / sent_count

        #ovr_desc_sent_score
        ovr_desc_sent_score = 0
        sent_count = 0
        for dsent in article['desc_sent']:
            sent_count += 1
            print("COMPOUND", dsent['compound'])
            ovr_desc_sent_score += dsent['compound']
        ovr_desc_sent_score = ovr_desc_sent_score / sent_count

        article['ovr_text_sent_score'] = ovr_text_sent_score
        article['ovr_title_sent_score'] = ovr_title_sent_score
        article['ovr_desc_sent_score'] = ovr_desc_sent_score

        trifold_score, trifold_rating = calc_article_trifold_rating(ovr_text_sent_score, ovr_title_sent_score, ovr_desc_sent_score)
        article['trifold_score'] = trifold_score
        article['trifold_rating'] = trifold_rating



        # call calc_sent_rating():
        #text_sent_rating
        text_sent_rating = calc_sent_rating(ovr_text_sent_score)
        article['text_sent_rating'] = text_sent_rating
        #title_sent_rating
        title_sent_rating = calc_sent_rating(ovr_title_sent_score)
        article['title_sent_rating'] = title_sent_rating
        #desc_sent_rating
        desc_sent_rating = calc_sent_rating(ovr_desc_sent_score)
        article['desc_sent_rating'] = desc_sent_rating

        # add all these scores back to articles dictionary and return it so others can ues the scores

    return articles

def calc_sent_rating(sent_score):
    """Calculates the sentiment rating for a given title, description, or text sentiment rating for an article."""
    if sent_score >= -0.05554 and sent_score <= 0.05554:
        rating = "Neutral"
    elif sent_score <= -.05555 and sent_score >= -.30554:
        rating = "Somewhat Negative"
    elif sent_score <= -.30555 and sent_score >= -.70554:
        rating = "Negative"
    elif sent_score <= -.70555 and sent_score >= 1.0:
        rating = "Very Negative"
    elif sent_score >= .05555 and sent_score <= .30554:
        rating = "Somewhat Positive"
    elif sent_score >= .30555 and sent_score <= .70554:
        rating = "Positive"
    elif sent_score >= .70555 and sent_score <= 1.0:
        rating = "Very Positive"

    return rating

def calc_article_trifold_rating(ovr_text_sent_score, ovr_title_sent_score, ovr_desc_sent_score):
    """Calculates a overall 'trifold' score for an article based on the title, description, and text sentiment scores."""

    trifold_score = (ovr_text_sent_score + ovr_title_sent_score + ovr_desc_sent_score) / 3

    trifold_rating = calc_sent_rating(trifold_score)

    return trifold_score, trifold_rating


def calc_stock_sentiment(scored_articles, stocks_list):
    # pass articles and stocks_list
    """Calculates average sentiment score for a stock based on all articles (text) for given stock."""
    scored_stocks = []

    for stock in stocks_list:
        article_count = 0
        stock_sent_score = 0
        for article in scored_articles:
            print("ARTICLE", article)
            if article['stock'] == stock:
                article_count += 1
                stock_sent_score += article['ovr_text_sent_score']

        avg_stock_sent_score = stock_sent_score / article_count
        stock_sent_dict = {'stock': stock, 'avg_stock_sent_score': avg_stock_sent_score, 'article_count': article_count}
        scored_stocks.append(stock_sent_dict)

    return scored_stocks

def calc_recent_stock_sentiment(scored_articles, scored_stocks):
    # pass articles, stocks, and stock_sentiments{}
    """Calculates average sentiment score for a stock based the most recent articles (within last 7 days)."""
    # must go by date
    # if article[date] == '1 week ago'
    # average score

    for stock in scored_stocks:
        recent_article_count = 0
        day_article_count = 0
        day_stock_sent_score = 0
        stock_sent_score = 0
        for article in scored_articles:
            if article['stock'] == stock['stock']:
                if 'day' in article['date']: # see if day is in it because then we know it is less than a week old/recent
                    print("ARTICLE", article)
                    recent_article_count += 1
                    stock_sent_score += article['ovr_text_sent_score']
                elif 'hour' in article['date']:
                    #day
                    day_article_count += 1
                    day_stock_sent_score += article['ovr_text_sent_score']
                    #recent
                    recent_article_count += 1
                    stock_sent_score += article['ovr_text_sent_score']

        try:
            rcnt_text_sent_score = stock_sent_score / recent_article_count
        except:
            rcnt_text_sent_score = 0
        stock['recent_article_count'] = recent_article_count
        stock['rcnt_text_sent_score'] = rcnt_text_sent_score

        try:
            day_text_sent_score = day_stock_sent_score / day_article_count
        except:
            day_text_sent_score = 0
        stock['day_article_count'] = day_article_count
        stock['day_stock_sent_score'] = day_stock_sent_score

    return scored_stocks


def calc_ovr_stock_article_feelings(scored_articles, scored_stocks):
    """Sees if the articles for a stock are generally positive, neutral, or negative."""
    # parses all of the article['text_sent_rating']
    # if neutral,
    # if somewhat positive, positiive, extremely positive,
    # if somewhat negative, negative, very negative
    for stock in scored_stocks:
        positive_article_count = 0
        neutral_article_count = 0
        negative_article_count = 0

        for article in scored_articles:
            sent_score = article['ovr_text_sent_score']
            if article['stock'] == stock['stock']:
                if sent_score > .05:
                    positive_article_count += 1
                elif sent_score >= -0.05 and sent_score <= 0.05:
                    neutral_article_count += 1
                elif sent_score < -.05:
                    negative_article_count += 1
                else:
                    pass

        count_list = []
        count_list.append(positive_article_count)
        count_list.append(neutral_article_count)
        count_list.append(negative_article_count)
        largest = max(count_list)
        if largest == positive_article_count:
            stock['overall_stock_articles_feelings'] = 'Positive'
        elif largest == neutral_article_count:
            stock['overall_stock_articles_feelings'] = 'Neutral'
        elif largest == negative_article_count:
            stock['overall_stock_articles_feelings'] = 'Negative'
        else:
            stock['overall_stock_articles_feelings'] = 'Undetermined'


        stock['positive_article_count'] = positive_article_count
        stock['neutral_article_count'] = neutral_article_count
        stock['negative_article_count'] = negative_article_count
        return scored_stocks

def calc_stock_trifold_rating(scored_articles, scored_stocks):
    """Takes the trifold ratings for each article for a given stock and gets the average trifold rating."""
    for stock in scored_stocks:
        stock_trifold_rating = 0
        stock_article_count = 0
        for article in scored_articles:
            if article['stock'] == stock['stock']:
                stock_article_count += 1
                stock_trifold_rating += article['trifold_score']

    try:
        ovr_stock_trifold_rating = stock_trifold_rating / stock_article_count
    except:
        ovr_stock_trifold_rating = 0
    stock['ovr_stock_trifold_rating'] = ovr_stock_trifold_rating

    return scored_stocks

def calc_ovr_media_rating(scored_articles, scored_stocks):
    """Calculates a given websites rating for a given stock based on it's overall articles."""

    media_list = []
    for article in scored_articles:
        media = article['media']
        if media in media_list:
            pass
        else:
            media_list.append(media)
    print("MEDIA", media_list)

    for stock in scored_stocks:
        stock_media_list = []
        for media in media_list:
            article_count = 0
            media_sent_score = 0
            for article in scored_articles:
                if article['media'] == media and article['stock'] == stock['stock']:
                    article_count += 1
                    media_sent_score += article['ovr_text_sent_score']

            try:
                stock_media_avg_sent_score = media_sent_score / article_count
            except:
                stock_media_avg_sent_score = 0
            media_sent_rating = calc_sent_rating(stock_media_avg_sent_score)
            media_dict = {'media': media, 'media_avg_sent_score': stock_media_avg_sent_score, 'article_count': article_count, 'media_sent_rating': media_sent_rating}
            stock_media_list.append(media_dict)
        stock['media_results'] = stock_media_list

    return scored_stocks

def gather_stock_price_info():
    """Gathers new realtime stock price info."""

def gather_previous_results_info():
    """Will be used to gather previous results from imported CSVs for added analysis."""

def predict_stock_swing():
    """Predicts the overall view of a stock and whether it will continue to rise or fall."""
    # takes stock_trifold_rating, ovr_stock_text_sent, calc_recent_stock_sentiment, ovr_stock_feelings as inputs

temp_cml_interface()
