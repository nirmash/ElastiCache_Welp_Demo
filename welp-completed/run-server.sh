#!/bin/sh

export PYTHONPATH=/code
export FLASK_ENV=development
export FLASK_DEBUG=1
export FLASK_APP=welp
flask run -h 0.0.0.0 -p 80