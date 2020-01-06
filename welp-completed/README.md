# Overview
This repo contains a demo for using Redis (in a Docker container or on ElastiCache) as a backend for a restaurant rating site. The demo goes through some advanced Redis capabilities such as geosaptial data types, sorted sets and hash maps.

**Warning:** The application and instructions were developed and tested on a Mac client and an EC2 Amazon Linux server.

# How it works
The demo is a single page web application ([SPA](https://en.wikipedia.org/wiki/Single-page_application)). It contains a dataset of Las Vegas restaurants, their locations, cuisines and allows users to score the quality of a restaurant. 

The demo is implemented in [Python Flask](https://www.fullstackpython.com/flask.html) (backend) and Javascript on a client HTML page. The demo runs in a Docker container to make dependencies easier to manage.

**Note:** The application leverages [mapbox](https://www.mapbox.com/) to generate a map view of the restaurants.

# How to use it
Once installed, click the **Import Data** button, a bar graph will appear listing the number of restaurants per cuisine. Pick a cuisine type from the drop-down box under the **Import Data** button to see a map with all the restaurants under the selected cuisine. 
![Screenshot](https://github.com/nirmash/ElastiCache_DbCache_Demo/blob/master/images/welp-screen1.jpg?raw=true)
Click on one of the restaurant names and provide a rating to see a pie-chart with the counts of restaurants by rating.
![Screenshot](https://github.com/nirmash/ElastiCache_DbCache_Demo/blob/master/images/welp-screen2.jpg?raw=true)

# Install
This demo can run on a local environment that uses Docker or on EC2 with ElastiCache for Redis. 
## Prerequisites 
The application dependencies are valid for both local environments or on EC2:
* [Docker](https://docs.docker.com/v17.09/engine/installation/)
* [docker-compose](https://docs.docker.com/compose/install/)
* [git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)

**Note:** `yum` is the package manager used on EC2 Amazon Linux instances.
Obtain an API token from [mapbox](https://www.mapbox.com/), a free token is available.
## Application files
Clone the demo repository:
```
$ git clone https://github.com/nirmash/ElastiCache_Welp_Demo
```
## Environment variables
Set the environment variables required to run the demo.

**Note:** The demo uses environment variables to store application secrets.
### AWS
```
export REDIS_MASTER_HOST=your_redis_master_node_endpoint
export REDIS_MASTER_PORT=your_redis_master_port (typically 6379)
export MAP_TOKEN=your_map_box_api_token
export FLASK_ENV=development
export PYTHONPATH=/code
```
### Locally 
```
export REDIS_MASTER_HOST=welp-completed_redis_1
export REDIS_MASTER_PORT=6379
export MAP_TOKEN=your_map_box_api_token
export FLASK_ENV=development
export PYTHONPATH=/code
```

# Build
Browse to the `docker-compose.yaml` file location and load the application Docker container:
```
$ cd ElastiCache_DbCache_Demo/dbcache
$ ./init_service.sh
```
After the build process is done, the Docker containers status will appear (see below):

```
          Name                        Command               State                 Ports               
------------------------------------------------------------------------------------------------------
welp-completed_redis_1     docker-entrypoint.sh redis ...   Up      0.0.0.0:63791->6379/tcp, 63791/tcp
welp-completed_service_1   /bin/sh -c /code/run-server.sh   Up      10000/tcp, 0.0.0.0:80->80/tcp 
```
Note that the application will load 2 containers, the welp-completed_service_1 contains the application code while the welp-completed_redis_1 container can be used instead of ElastiCache to run the demo locally.

# Run the demo
**Locally:** Browse to http://localhost.

**On AWS:** Browse to the endpoint of the EC2 server you created earlier.