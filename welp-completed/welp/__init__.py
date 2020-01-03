# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0  

import redis, os 
from flask import Flask, Markup, request, render_template

app = Flask(__name__)

hostname = os.getenv('REDIS_MASTER_HOST') # Change this value
port = os.getenv('REDIS_MASTER_PORT') # Default Redis port

current_location = [36.1212, -115.1697] # Las Vegas
data_file = '/code/nevada-restaurants.osm'

# To obtain your own token, visit mapbox.com and sign up for a free account.
map_access_token = os.getenv('MAP_TOKEN')   # MapBox token

def get_redis_client():
    return redis.Redis(host=hostname, port=port, db=0, decode_responses=True)

import welp.restaurants
import welp.ratings
import welp.map
import welp.data_import

@app.route('/')
def index():
    return render_template('index.html', current_location=current_location, map_access_token=map_access_token)