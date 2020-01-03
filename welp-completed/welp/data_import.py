# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0  

from concurrent.futures import ThreadPoolExecutor

import os
import redis
import sys
import xml.etree.cElementTree as ET
import json

from welp import app, get_redis_client, data_file

executor = ThreadPoolExecutor(1) # for async file loading
progress = 0 # global progress
stop = False # async loading has been requested to stop
future = None # current async task

def process_restaurant(r, data):
    """
    Process a given restaurant node during an XML scan of the input file and 
    store its data into Redis.
    
    Arguments:
    r - Redis client.  See https://redis-py.readthedocs.io/en/latest/.
    data - Dictionary containing key/value data pairs for the location. Node
           properties (e.g. latitude/longitude) will be prefixed with 'property:'
           and tags (e.g. cuisine type) will be prefixed with 'tag:'.
    """
    
    id = data['property:id'] # Unique numerical identifier for the node
    cuisines = data['tag:cuisine'].split(';') # Cuisines are semicolon-separated
    latitude = data['property:lat'] # Latitude of location
    longitude = data['property:lon'] # Longitude of location
    
    ################################## TODO ####################################
    # https://redis.io/commands/zincrby
    #   ZINCRBY key increment member
    # https://redis.io/commands/geoadd
    #   GEOADD key longitude latitude member [longitude latitude member ...]
    # https://redis.io/commands/hmset
    #   HMSET key field value [field value ...]
    
    r.hmset(id, data)

    for cuisine in cuisines:
        r.zincrby('cuisine_rankings', float(1.0), cuisine)
        r.geoadd('geo:'+cuisine, longitude, latitude, id)
        
    ############################### END TODO ###################################

def process_node(r, item):
    """Process a given cuisine node"""
    properties = dict(item.items()) # Node properties ('loc', 'lat', 'timestamp', 'version')

    # Find all tags (they look like <tag k="key" v="value"/>)
    tags = {}
    for child in item:
        if not child.tag == 'tag':
            continue
        tags[child.attrib['k']] = child.attrib['v']

    data = dict({'property:'+key: value for key, value in properties.items()})
    data.update({'tag:'+key: value for key, value in tags.items()})

    process_restaurant(r, data)

def import_data(filename):
    """Parse the restaurant information from the given OSM XML data file and store in Redis"""
    print (filename)
    global progress
    global stop
    
    r = get_redis_client()
    r.flushall()

    total_size = os.path.getsize(filename)
    print (total_size)
    with open(filename, 'r') as f:
        context = ET.iterparse(f, events=('start', 'end'))
        context = iter(context)
    
        event, root = next(context)
    
        cuisine_item = False # Whether the current item has a tag with key 'cuisine'
        node_item = False # Whether the current item has a 'node' tag
        for event, item in context:
            if stop:
                break
            
            # Process all nodes and their children
            progress = float(f.tell())/total_size
    
            if event == 'start':
                if item.tag == 'node':
                    node_item = True # Currently parsing a node
                continue
            elif not node_item:
                root.clear() # GC
                continue
    
            if item.tag == 'tag' and item.attrib['k'] == 'cuisine':
                cuisine_item = True
            if item.tag == 'node':
                if cuisine_item:
                    cuisine_item = False
                    process_node(r, item)
                root.clear()
                node_item = False
                
    if not stop:
        progress = 1

    stop = False

def import_running():
    global future

    if future is not None:
        if future.done() or future.cancelled():
            error = future.exception()
            if error:
                raise error
            future = None

    return future is not None

@app.route('/start_import')
def start_import():
    global future
    global progress

    if not import_running():
        progress = 0
        future = executor.submit(import_data, data_file)
    return import_progress()

@app.route('/stop_import')
def stop_import():
    global future
    global stop
    
    if import_running():
        stop = True
    return import_progress()
    
@app.route('/import_progress')
def import_progress():
    result =  {
        'running': import_running(),
        'progress': progress*100
    }
    return json.dumps(result)