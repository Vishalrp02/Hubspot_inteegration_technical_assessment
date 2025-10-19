# hubspot.py
import json
import secrets
from fastapi import Request, HTTPException
from fastapi.responses import HTMLResponse
from urllib.parse import unquote, quote
import httpx
import asyncio

import base64
from integrations.integration_item import IntegrationItem
from redis_client import add_key_value_redis, get_value_redis, delete_key_redis

CLIENT_ID = '0b5354c9-a32b-4576-95ea-03e973632616'
CLIENT_SECRET = '7180fee3-384a-40ad-85a0-58fd3260c96b'
encoded_client_id_secret = base64.b64encode(f'{CLIENT_ID}:{CLIENT_SECRET}'.encode()).decode()
REDIRECT_URI = 'http://localhost:8000/integrations/hubspot/oauth2callback'

authorization_url = (
    f'https://app-na2.hubspot.com/oauth/authorize'
    f'?client_id={CLIENT_ID}'
    f'&redirect_uri={REDIRECT_URI}'
    f'&scope=oauth%20crm.objects.companies.read%20crm.objects.deals.read%20crm.objects.contacts.read'
)


async def authorize_hubspot(user_id, org_id):
    state_data = {
        'state': secrets.token_urlsafe(32),
        'user_id': user_id,
        'org_id': org_id
    }
    encoded_state = json.dumps(state_data)
    await add_key_value_redis(f'hubspot_state:{org_id}:{user_id}', encoded_state, expire=600)
    return f'{authorization_url}&state={quote(encoded_state)}'


async def oauth2callback_hubspot(request: Request):
    if request.query_params.get('error'):
        raise HTTPException(status_code=400, detail=request.query_params.get('error'))

    code = request.query_params.get('code')
    encoded_state = request.query_params.get('state')

    if not encoded_state:
        raise HTTPException(status_code=400, detail="Missing 'state' parameter")

    decoded_state = unquote(encoded_state)

    try:
        state_data = json.loads(decoded_state)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format in state parameter")

    original_state = state_data.get('state')
    user_id = state_data.get('user_id')
    org_id = state_data.get('org_id')

    saved_state = await get_value_redis(f'hubspot_state:{org_id}:{user_id}')
    if not saved_state:
        raise HTTPException(status_code=400, detail="State not found in Redis (maybe expired?)")

    saved_state_data = json.loads(saved_state)
    if original_state != saved_state_data.get('state'):
        raise HTTPException(status_code=400, detail="State does not match")

    # Exchange code for access token
    async with httpx.AsyncClient() as client:
        response, _ = await asyncio.gather(
            client.post(
                'https://api.hubapi.com/oauth/v1/token',
                data={
                    'grant_type': 'authorization_code',
                    'code': code,
                    'redirect_uri': REDIRECT_URI,
                    'client_id': CLIENT_ID,
                    'client_secret': CLIENT_SECRET,
                },
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            ),
            delete_key_redis(f'hubspot_state:{org_id}:{user_id}'),
        )

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=f"HubSpot token error: {response.text}")

    # Save credentials to Redis
    await add_key_value_redis(
        f'hubspot_credentials:{org_id}:{user_id}',
        json.dumps(response.json()),
        expire=600
    )
    print("✅ Credentials stored:", f'hubspot_credentials:{org_id}:{user_id}')
    saved = await get_value_redis(f'hubspot_credentials:{org_id}:{user_id}')
    print("🔍 Redis readback:", saved)

   
    

    # Return success HTML
    close_window_script = """
    <html>
        <body>
            <script>window.close();</script>
        </body>
    </html>
    """
    return HTMLResponse(content=close_window_script)


async def get_hubspot_credentials(user_id, org_id):
    credentials = await get_value_redis(f'hubspot_credentials:{org_id}:{user_id}')
    if not credentials:
        raise HTTPException(status_code=400, detail='No credentials found.')
    credentials = json.loads(credentials)
    await delete_key_redis(f'hubspot_credentials:{org_id}:{user_id}')
    return credentials


async def create_integration_item_metadata_object(response_json: dict) -> IntegrationItem:
    """Creates an IntegrationItem object from HubSpot CRM API response."""
    properties = response_json.get("properties", {})
    name = (
        properties.get("dealname") or
        properties.get("firstname") or
        properties.get("name") or
        "Unnamed HubSpot Object"
    )

    integration_item_metadata = IntegrationItem(
        id=response_json.get("id"),
        type=response_json.get("objectTypeId", "hubspot_object"),
        name=name,
        creation_time=response_json.get("createdAt"),
        last_modified_time=response_json.get("updatedAt"),
        parent_id=None
    )
    return integration_item_metadata


async def get_items_hubspot(credentials) -> list[IntegrationItem]:
    """Aggregates all metadata relevant for a HubSpot integration."""
    credentials = json.loads(credentials)
    access_token = credentials.get("access_token")
    if not access_token:
        raise ValueError("No access token found in credentials")

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    endpoints = [
        'https://api.hubapi.com/crm/v3/objects/deals',
        'https://api.hubapi.com/crm/v3/objects/contacts',
        'https://api.hubapi.com/crm/v3/objects/companies'
    ]

    list_of_integration_item_metadata = []

    async with httpx.AsyncClient() as client:
        for url in endpoints:
            response = await client.get(url, headers=headers)
            if response.status_code != 200:
                raise Exception(f"HubSpot API returned {response.status_code}: {response.text}")
            data = response.json()
            results = data.get('results', [])
            for result in results:
                integration_item = await create_integration_item_metadata_object(result)
                list_of_integration_item_metadata.append(integration_item)

 
    return list_of_integration_item_metadata



   
