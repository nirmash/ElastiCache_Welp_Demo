# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0  

from collections import OrderedDict
from flask import Flask, Markup, request, render_template
import json
import redis

from welp import app, get_redis_client, current_location
from welp.restaurants import get_restaurant_data

@app.route('/cuisine_ratings', methods=['GET'])
def cuisine_ratings():
    """
    Return JSON mapping each rating value (1-5) to the number of restaurants that
    have been rated with this rating.
    """
    cuisine = request.args.get('cuisine') # Required
    
    response = {}
    r = get_redis_client()

    pipe = r.pipeline(transaction=False) # Batch together multiple requests

    ################################## TODO ####################################
    # https://redis.io/commands/zcount
    #  ZCOUNT key min max
    
    # Set up the pipeline
    
    for i in range(1,6):
        pipe.zcount('ratings:'+cuisine, i, i)
    
    results = pipe.execute()

    # Store the results into the response dictionary

    i = 1
    for item in results:
        response[i] = item
        i += 1

    ############################### END TODO ###################################

    return json.dumps(response, sort_keys=True)
    
def get_rating(r, cuisine, id):
    """
    Return the rating for a particular restaurant ID within a given cuisine.
    
    Arguments:
    r - Redis client.  See https://redis-py.readthedocs.io/en/latest/.
    cuisine - A string representing the given restaurant type, e.g. 'pizza'.
    id - The identifier of a restaurant.
    """

    ################################## TODO ####################################
    # https://redis.io/commands/zscore
    #  ZSCORE key member
    
    return r.zscore('ratings:'+cuisine, id)

    ############################### END TODO ###################################

    
def set_rating(r, cuisine, id, rating):
    """
    Set the rating for a particular restaurant ID within a given cuisine.
    
    Arguments:
    r - Redis client.  See https://redis-py.readthedocs.io/en/latest/.
    cuisine - A string representing the given restaurant type, e.g. 'pizza'.
    id - The identifier of a restaurant.
    rating - The new score of the restaurant.
    """

    ################################## TODO ####################################
    # https://redis.io/commands/zadd
    #  ZADD key [NX|XX] [CH] [INCR] score member [score member ...] 
    
    r.zadd('ratings:'+cuisine, {id: rating})

    ############################### END TODO ###################################

@app.route('/rating', methods=['GET'])
def rating():
    """
    Get or set the restaurant's rating.  If a rating is provided in input, set
    the rating for each cuisine sorted set and return it.  Otherwise, look up
    the rating and return it as a string.
    """
    id = request.args.get('id') # Required
    rating = request.args.get('rating') # Optional

    r = get_redis_client()

    # Fetch the cuisine for the restaurant
    data = get_restaurant_data(r, id, 'tag:cuisine')
    if 'tag:cuisine' not in data:
        return "0"
    cuisine = data['tag:cuisine']
    
    # Set the rating if provided
    if rating:
        set_rating(r, cuisine, id, rating)

    # Always look up rating at the end to make sure it's set
    rating = get_rating(r, cuisine, id)
    if rating:
        return str(rating)
    else:
        return "0"

@app.route('/clear_ratings')
def clear_ratings():
    """
    Clear all ratings, leaving other data intact.
    """

    r = get_redis_client()

    ################################## TODO ####################################
    # https://redis.io/commands/scan
    #  SCAN cursor [MATCH pattern] [COUNT count]
    # https://redis.io/commands/del
    #  DEL key [key ...] 
    
    for key in r.scan_iter('ratings:*'):
        r.delete(key)

    ############################### END TODO ###################################

    return json.dumps({
        "result": "ok",
    })