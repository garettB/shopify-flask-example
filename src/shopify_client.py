import json
from typing import List, Dict, Optional
import logging
import os

import requests
from requests.exceptions import HTTPError
from dotenv import load_dotenv

load_dotenv()

# Use a recent, supported API version. It's good practice to keep this in your config.
# See: https://shopify.dev/docs/api/usage/versioning
SHOPIFY_API_VERSION = "2025-10"


class ShopifyStoreClient():

    def __init__(self, shop: str, access_token: str):
        self.shop = shop
        self.access_token = access_token
        self.base_url = f"https://{shop}/admin/api/{SHOPIFY_API_VERSION}/graphql.json"

    @staticmethod
    def authenticate(shop: str, code: str) -> Optional[str]:
        url = f"https://{shop}/admin/oauth/access_token"
        payload = {
            "client_id": os.environ.get('SHOPIFY_API_KEY'),
            "client_secret": os.environ.get('SHOPIFY_SECRET'),
            "code": code
        }
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            return response.json()['access_token']
        except HTTPError as ex:
            logging.error(f"Failed to authenticate with shop {shop}: {ex}")
            logging.error(f"Response: {ex.response.text}")
            return None

    def execute_query(self, query: str, variables: Optional[Dict] = None) -> Optional[Dict]:
        """Executes a GraphQL query or mutation."""
        headers = {
            'X-Shopify-Access-Token': self.access_token,
            'Content-Type': 'application/json'
        }
        payload = {'query': query}
        if variables:
            payload['variables'] = variables

        try:
            response = requests.post(self.base_url, json=payload, headers=headers)
            response.raise_for_status()
            response_json = response.json()

            if 'errors' in response_json:
                logging.error(f"GraphQL query failed: {response_json['errors']}")
                return None

            logging.debug(f"GraphQL response:\n{json.dumps(response_json, indent=4)}")
            return response_json
        except HTTPError as ex:
            logging.error(f"API call failed for query: {ex}")
            logging.error(f"Response: {ex.response.text}")
            return None

    def get_shop(self) -> Optional[Dict]:
        query = """
        {
          shop {
            id
            name
            myshopifyDomain
          }
        }
        """
        response = self.execute_query(query)
        return response['data']['shop'] if response and response.get('data') else None

    def get_script_tags(self) -> Optional[List]:
        query = """
        {
          scriptTags(first: 5) {
            edges {
              node {
                id
                src
                displayScope
              }
            }
          }
        }
        """
        response = self.execute_query(query)
        if not response or not response.get('data') or not response['data'].get('scriptTags'):
            return None
        return [edge['node'] for edge in response['data']['scriptTags']['edges']]

    def get_script_tag(self, id: str) -> Optional[Dict]:
        query = """
        query($id: ID!) {
          scriptTag(id: $id) {
            id
            src
            displayScope
          }
        }
        """
        variables = {"id": id}
        response = self.execute_query(query, variables)
        return response['data']['scriptTag'] if response and response.get('data') else None

    def update_script_tag(self, id: str, src: str, display_scope: Optional[str] = None) -> Optional[Dict]:
        mutation = """
        mutation ScriptTagUpdate($id: ID!, $input: ScriptTagInput!) {
          scriptTagUpdate(id: $id, input: $input) {
            scriptTag {
              id
              src
            }
            userErrors {
              field
              message
            }
          }
        }
        """
        input_data = {"src": src}
        if display_scope:
            input_data['displayScope'] = display_scope.upper()

        variables = {"id": id, "input": input_data}
        response = self.execute_query(mutation, variables)
        return response['data']['scriptTagUpdate'] if response and response.get('data') else None

    def create_script_tag(self, src: str, display_scope: str = 'ALL') -> Optional[Dict]:
        mutation = """
        mutation scriptTagCreate($input: ScriptTagInput!) {
          scriptTagCreate(input: $input) {
            scriptTag {
              id
              src
            }
            userErrors {
              field
              message
            }
          }
        }
        """
        variables = {"input": {"src": src, "displayScope": display_scope.upper()}}
        response = self.execute_query(mutation, variables)
        return response['data']['scriptTagCreate'] if response and response.get('data') else None

    def delete_script_tag(self, script_tag_id: str) -> Optional[str]:
        mutation = """
        mutation scriptTagDelete($id: ID!) {
          scriptTagDelete(id: $id) {
            deletedScriptTagId
            userErrors {
              field
              message
            }
          }
        }
        """
        variables = {"id": script_tag_id}
        response = self.execute_query(mutation, variables)
        return response['data']['scriptTagDelete']['deletedScriptTagId'] if response and response.get('data') and response['data'].get('scriptTagDelete') else None

    def create_webhook(self, address: str, topic: str) -> Optional[Dict]:
        mutation = """
        mutation webhookSubscriptionCreate($topic: WebhookSubscriptionTopic!, $webhookSubscription: WebhookSubscriptionInput!) {
          webhookSubscriptionCreate(topic: $topic, webhookSubscription: $webhookSubscription) {
            webhookSubscription {
              id
              topic
              filter
              uri
            }
            userErrors {
              field
              message
            }
          }
        }
        """
        variables = {
            "topic": topic,
            "webhookSubscription": {
                "uri": address,
                "format": "JSON"
            }
        }
        response = self.execute_query(mutation, variables)
        return response['data']['webhookSubscriptionCreate'] if response and response.get('data') else None

    def get_webhooks_count(self, topic: Optional[str] = None) -> Optional[int]:
        query = """
        query WebhookSubscriptionsCount($query: String!) { 
            webhookSubscriptionsCount(query: $query) { 
                count
                precision
            } 
        }
        """
        variables = {"topic": topic} if topic else None
        response = self.execute_query(query, variables)
        return response['data']['webhookSubscriptionsCount']['count'] if response and response.get('data').get('webhookSubscriptionsCount') else None
