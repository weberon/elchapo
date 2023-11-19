import logging

import requests
from os import getenv
from flask import Flask, redirect, jsonify
from flask import request, jsonify

from constants import WEBHOOK, NOT_FOUND_URL, SECRET_KEY
from models import ShortURL, RequestLogger
from zappa.asynchronous import task
from utils import fetch_request_metadata

logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

MAIN = False

app = Flask(__name__, static_url_path='/no_static')


@app.after_request
def after_request(response):
		response.headers.add('Access-Control-Allow-Origin', '*')
		response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
		return response


@app.route('/c', methods=['POST'])
def create_url():
		path = request.json['path']
		secret_key = request.json.get("secret_key")
		redirect_url = request.json['redirect_url']
		webhook = request.json.get('webhook', None)
		if secret_key != getenv("SECRET_KEY"):
			return jsonify(
				message="Credentials missing in the request.", error="Unauthorized request."), 401
		try:
				ShortURL.get(path)
				return "", 409
		except ShortURL.DoesNotExist:
				ShortURL(url=path, redirection_url=redirect_url, webhook=webhook).save()
				return jsonify(success=True), 200
		return "", 400


@task
def call_url(url):
		if url:
				retry = 3
				while retry > 0:
						x = requests.get(url)
						if x.status_code >= 400:
								retry = retry - 1
						else:
								return x.text


def get_hook(webhook, path):
		if webhook:
				if webhook.__contains__('?'):
						webhook += '&path=%s' % path
				else:
						webhook += '?path=%s' % path
		return webhook


@app.route('/<path:path>', methods=['GET'])
def redirect_url(path):
		try:
				short_url = ShortURL.get(path)
				webhook = WEBHOOK
				if short_url.webhook:
						webhook = short_url.webhook
				webhook = get_hook(webhook, path)
				if webhook:
						call_url(webhook)
				# Fetch the metadata from the request
				metadata = fetch_request_metadata(request)
				# Create a document in the RequestLogger table in DynamoDB for further inspection
				document = RequestLogger(short_url=path, request=metadata)
				document.save()
				return redirect(short_url.redirection_url, code=302)
		except ShortURL.DoesNotExist:
				return jsonify(error="Not found"), 404


# We only need this for local development.
if __name__ == '__main__':
		MAIN = True
		app.run(host='0.0.0.0', port=5601)
