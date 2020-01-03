# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0  

from collections import OrderedDict
from flask import Flask, Markup, request, render_template
import json
import redis

from welp import app, get_redis_client

@app.route('/map_data', methods=['GET'])
def map_data():
    """
    Given a specific cuisine and a latitude, longitude, and diagonal bound
    in meters, return a dictionary mapping the ID of the restaurant to a
    pair of (longitude, latitude).
    
    Arguments:
    cuisine - A string representing the given restaurant type, e.g. 'pizza'.
    latitude - A float representing the latitude of the center of the map.
    longitude - A float representing the longitude of the center of the map.
    diag - The distance, in meters, from the northwest corner of the map to the
           southeast corner of the map.
    """
    cuisine = request.args.get('cuisine') # Required
    latitude = request.args.get('lat') # Required
    longitude = request.args.get('lng') # Required
    diag = request.args.get('diag') # Required

    response = {}

    r = get_redis_client()

    ################################## TODO ###################################
    # https://redis.io/commands/georadius
    #   GEORADIUS key longitude latitude radius m|km|ft|mi [WITHCOORD] [WITHDIST] [WITHHASH] [COUNT count] [ASC|DESC] [STORE key] [STOREDIST key]
    
    response.update(r.georadius('geo:'+cuisine, longitude, latitude, float(diag)/2, unit='m', withcoord=True))

    ############################### END TODO ###################################

    return json.dumps(response)
