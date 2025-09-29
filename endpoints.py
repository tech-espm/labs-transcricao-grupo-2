from flask import Flask, render_template, json, request, Response, session, redirect, url_for, jsonify
from datetime import datetime, timedelta
import config
from werkzeug.exceptions import HTTPException
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY') or os.urandom(24)

if __name__ == '__main__':
    app.run(host=config.host, port=config.port, debug=True)