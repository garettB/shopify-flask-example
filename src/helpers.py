from functools import wraps
from typing import List, Callable, Any
from urllib.parse import urlencode
import logging

import os
import re
import hmac
import base64
import hashlib
from flask import request, abort
from dotenv import load_dotenv
import os

load_dotenv()

def generate_install_redirect_url(shop: str, scopes: List[str], nonce: str, access_mode: List[str]) -> str:
    """Generates the installation redirect URL for the Shopify OAuth flow."""
    query_params = {
        "client_id": os.environ.get('SHOPIFY_API_KEY'),
        "scope": ",".join(scopes),
        "redirect_uri": os.environ.get('INSTALL_REDIRECT_URL'),
        "state": nonce,
        "grant_options[]": ",".join(access_mode)
    }
    print(f"https://{shop}/admin/oauth/authorize?{urlencode(query_params)}")
    return f"https://{shop}/admin/oauth/authorize?{urlencode(query_params)}"

load_dotenv()
SHOPIFY_SECRET = os.environ.get('SHOPIFY_SECRET')
SHOPIFY_API_KEY = os.environ.get('SHOPIFY_API_KEY')
INSTALL_REDIRECT_URL = os.environ.get('INSTALL_REDIRECT_URL')
APP_NAME = os.environ.get('APP_NAME')

def generate_post_install_redirect_url(shop: str) -> str:
    """Generates the post-install redirect URL to the app's page in the Shopify admin."""
    return f"https://{shop}/admin/apps/{os.environ.get('APP_NAME')}"


def verify_web_call(f: Callable) -> Callable:
    @wraps(f)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        query_params = request.args.to_dict()
        sent_hmac = query_params.pop('hmac', None)

        # Parameters must be sorted alphabetically before being used to generate the HMAC
        sorted_params = sorted(query_params.items())
        message = urlencode(sorted_params).encode('utf-8')

        if not sent_hmac or not verify_hmac(message, sent_hmac):
            logging.error(f"HMAC could not be verified for web call.")
            abort(400)

        shop = query_params.get('shop')
        if shop and not is_valid_shop(shop):
            logging.error(f"Shop name received is invalid: \n\tshop {shop}")
            abort(401)
        return f(*args, **kwargs)
    return wrapper


def verify_webhook_call(f: Callable) -> Callable:
    @wraps(f)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        encoded_hmac = request.headers.get('X-Shopify-Hmac-Sha256')
        data = request.get_data()

        if not encoded_hmac or not verify_hmac(data, encoded_hmac, is_webhook=True):
            logging.error(f"HMAC could not be verified for webhook.")
            abort(401)
        return f(*args, **kwargs)
    return wrapper


def verify_hmac(data: bytes, received_hmac: str, is_webhook: bool = False) -> bool:
    """Verifies the HMAC signature of a request."""
    calculated_hmac = hmac.new(os.environ.get('SHOPIFY_SECRET').encode('utf-8'), data, hashlib.sha256)
    if is_webhook:
        return hmac.compare_digest(base64.b64encode(calculated_hmac.digest()), received_hmac.encode('utf-8'))
    return hmac.compare_digest(calculated_hmac.hexdigest(), received_hmac)


def is_valid_shop(shop: str) -> bool:
    # Shopify docs give regex with protocol required, but shop never includes protocol
    shopname_regex = r'[a-zA-Z0-9][a-zA-Z0-9\-]*\.myshopify\.com[\/]?'
    return True if re.match(shopname_regex, shop) else False
