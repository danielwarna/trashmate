#!/bin/bash
gunicorn -b 127.0.0.1:9085 --debug webapp:app

