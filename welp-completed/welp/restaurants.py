# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0  

from collections import OrderedDict
from flask import Flask, Markup, request, render_template
from string import Template
import json
import redis

from welp import app, get_redis_client, current_location

@app.route('/restaurant_frequencies')
def restaurant_frequencies():
    """
    Return JSON mapping cuisine to the number of restaurants serving that
    cuisine.  The dictionary should contain the top cuisines in order by
    frequency.
    """
    response = OrderedDict() # Dictionary that maintains order added

    r = get_redis_client()

    ################################## TODO ####################################
    # https://redis.io/commands/zcount
    #  ZREVRANGEBYSCORE key max min [WITHSCORES] [LIMIT offset count]

    response.update(r.zrevrangebyscore('cuisine_rankings', '+inf', '-inf', withscores=True))

    ############################### END TODO ###################################

    return json.dumps(response)
    
def get_restaurant_data(r, id, field):
    """
    Return a dictionary containing detail fields associated with a given
    restaurant.
    
    Arguments:
    r - Redis client.  See https://redis-py.readthedocs.io/en/latest/.
    id - The identifier of a restaurant.
    field - An optional field to request a single property.
    """
    response = {}
    
    ################################## TODO ####################################
    # https://redis.io/commands/hget
    #  HGET key field
    # https://redis.io/commands/hgetall
    #  HGETALL key
    
    if field:
        response[field] = r.hget(id, field)
    else:
        response = r.hgetall(id)

    ############################### END TODO ###################################

    return response

@app.route('/restaurant_detail')
def restaurant_detail():
    id = request.args.get('id') # Required
    field = request.args.get('field') # Optional

    r = get_redis_client()

    response = get_restaurant_data(r, id, field)

    return json.dumps(response, sort_keys=True)
    
@app.route('/restaurant_list', methods=['GET'])
def restaurant_list():
    """
    Return JSON mapping restaurant identifiers to their public-facing names.
    To filter the set of restaurants, a cuisine type is provided, as well as
    the map's diagonal distance.
    
    Arguments:
    cuisine - A string representing the given restaurant type, e.g. 'pizza'.
    latitude - A float representing the latitude of the center of the map.
    longitude - A float representing the longitude of the center of the map.
    diag - The distance, in meters, from the northwest corner of the map to the
           southeast corner of the map.
    """
    cuisine = request.args.get('cuisine') # Required
    longitude = request.args.get('lng') # Required
    latitude = request.args.get('lat') # Required
    diag = request.args.get('diag') # Required

    response = {}

    r = get_redis_client()

    # Use this LUA template and fill in the function calls to return id, name
    # pairs for entries that are geographically close.
    lua_script_template = Template('''
local results = {}
for i, id in ipairs($redis_function_call1) do
  local name = $redis_function_call2
  table.insert(results, id)
  table.insert(results, name)
end
return results''')

    ################################## TODO ####################################
    # https://redis.io/commands/eval
    #  EVAL script numkeys key [key ...] arg [arg ...]
    #
    # The restaurant's name is stored in the property 'tag:name'
    
    lua_script = lua_script_template.substitute(
        redis_function_call1="redis.call('GEORADIUS', KEYS[1], ARGV[1], ARGV[2], ARGV[3], 'm')",
        redis_function_call2="redis.call('HGET', id, 'tag:name')"
        )

    # EVAL call to Redis goes here and returns a list
    members = r.eval(lua_script, 1, 'geo:'+cuisine, longitude, latitude, float(diag)/2)

    ############################### END TODO ###################################

    it = iter(members)
    for item in it:
        name = next(it)
        # Some restaurants may not have a name - handle this gracefully
        if name is None:
            name = "Unknown "+cuisine
        response[item] = name
        
    return json.dumps(response, sort_keys=True)