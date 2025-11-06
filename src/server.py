import uuid
import os
import json
import logging

from dotenv import load_dotenv

from flask import Flask, redirect, request, render_template, session

import helpers
from shopify_client import ShopifyStoreClient

app = Flask(__name__)
load_dotenv()

# The secret key is required to use Flask's session.
# In a production app, this should be a long, random, and secret string.
# You can generate one using `os.urandom(24)`.
app.secret_key = os.environ.get('FLASK_SECRET_KEY')

# Configure session cookie settings for cross-domain compatibility
app.config.update(
    SESSION_COOKIE_SAMESITE='None',
    SESSION_COOKIE_SECURE=True
)
# This is a simple in-memory store for access tokens.
# In a production app, you should use a persistent database (e.g., Redis, PostgreSQL).
SHOP_ACCESS_TOKENS = {}

ACCESS_MODE = []  # Defaults to offline access mode if left blank or omitted. https://shopify.dev/concepts/about-apis/authentication#api-access-modes
SCOPES = ['write_script_tags']  # https://shopify.dev/docs/admin-api/access-scopes


@app.route('/app_launched', methods=['GET'])
@helpers.verify_web_call
def app_launched() -> 'redirect | str':
    shop = request.args.get('shop')

    if shop in SHOP_ACCESS_TOKENS:
        return render_template('welcome.html', shop=shop)

    # The NONCE is a single-use random value we send to Shopify so we know the next call from Shopify is valid (see #app_installed)
    #   https://en.wikipedia.org/wiki/Cryptographic_nonce
    # We store it in the session to associate it with the current user's installation process.
    session['nonce'] = uuid.uuid4().hex
    redirect_url = helpers.generate_install_redirect_url(shop=shop, scopes=SCOPES, nonce=session['nonce'], access_mode=ACCESS_MODE)
    return redirect(redirect_url, code=302)


@app.route('/app_installed', methods=['GET'])
@helpers.verify_web_call
def app_installed() -> 'redirect | tuple[str, int]':
    state = request.args.get('state')
    nonce = session.pop('nonce', None)

    # Shopify passes our NONCE, created in #app_launched, as the `state` parameter, we need to ensure it matches!
    if state is None or state != nonce:
        return "Invalid `state` received", 400

    # Ok, NONCE matches, we can get rid of it now (a nonce, by definition, should only be used once)
    # Using the `code` received from Shopify we can now generate an access token that is specific to the specified `shop` with the
    #   ACCESS_MODE and SCOPES we asked for in #app_installed
    shop = request.args.get('shop')
    code = request.args.get('code')
    access_token = ShopifyStoreClient.authenticate(shop=shop, code=code)
    SHOP_ACCESS_TOKENS[shop] = access_token

    # We have an access token! Now let's register a webhook so Shopify will notify us if/when the app gets uninstalled
    # NOTE This webhook will call the #app_uninstalled function defined below
    shopify_client = ShopifyStoreClient(shop=shop, access_token=access_token)
    webhook_creation_result = shopify_client.create_webhook(address=os.environ.get('WEBHOOK_APP_UNINSTALL_URL'), topic="APP_UNINSTALLED")
    if not webhook_creation_result:
        logging.error(f"Failed to create app/uninstalled webhook for shop {shop}")
        # You might want to handle this failure more gracefully

    redirect_url = helpers.generate_post_install_redirect_url(shop=shop)
    return redirect(redirect_url, code=302)


@app.route('/app_uninstalled', methods=['POST'])
@helpers.verify_webhook_call
def app_uninstalled() -> tuple[str, int]:
    # https://shopify.dev/docs/admin-api/rest/reference/events/webhook?api[version]=2020-04
    # Someone uninstalled your app, clean up anything you need to
    # NOTE the shop ACCESS_TOKEN is now void!

    webhook_topic = request.headers.get('X-Shopify-Topic')
    webhook_payload = request.get_json(silent=True) or {}
    logging.error(f"webhook call received {webhook_topic}:\n{json.dumps(webhook_payload, indent=4)}")

    shop_domain = webhook_payload.get('myshopify_domain')
    if shop_domain in SHOP_ACCESS_TOKENS:
        del SHOP_ACCESS_TOKENS[shop_domain]
        logging.info(f"Removed access token for {shop_domain}")

    return "OK", 200


@app.route('/data_removal_request', methods=['POST'])
@helpers.verify_webhook_call
def data_removal_request() -> tuple[str, int]:
    # https://shopify.dev/tutorials/add-gdpr-webhooks-to-your-app
    # Clear all personal information you may have stored about the specified shop
    webhook_topic = request.headers.get('X-Shopify-Topic')
    webhook_payload = request.get_json(silent=True) or {}
    logging.warning(f"Data removal request received for {webhook_topic}:\n{json.dumps(webhook_payload, indent=4)}")

    # Here you would add logic to remove customer/shop data from your database.
    # For example:
    # shop_domain = webhook_payload.get('shop_domain')
    # if shop_domain:
    #     # remove_data_for_shop(shop_domain)

    return "OK", 200


if __name__ == '__main__':
    # Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
