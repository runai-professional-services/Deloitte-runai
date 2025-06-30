import requests
import json

# Configuration
CLIENT_ID = 'xxx'
CLIENT_SECRET = 'xxxx'
APP_URL = 'https://dummy.com'   
REALM = 'xx'
TENANT_ID = 'xx'
ROLE_ID = 'xx'  # The role ID you want to update

def get_bearer_token():
    """Get authentication token"""
    token_url = f"{APP_URL}/auth/realms/{REALM}/protocol/openid-connect/token"
    payload = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    response = requests.post(token_url, data=payload, headers=headers)
    response.raise_for_status()
    return response.json()["access_token"]

def get_existing_role(role_id):
    """Get the current role configuration"""
    token = get_bearer_token()
    
    url = f"{APP_URL}/api/v2/authorization/roles/{role_id}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        role = response.json()
        return role
    else:
        return None

def update_role(role_id, updated_role_data):
    """Update an existing role with PUT request"""
    token = get_bearer_token()
    
    url = f"{APP_URL}/api/v2/authorization/roles/{role_id}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    response = requests.put(url, headers=headers, json=updated_role_data)
    
    if response.status_code == 200:
        updated_role = response.json()
        return updated_role
    else:
        return None

if __name__ == "__main__":
    # Step 1: Get the existing role configuration
    existing_role = get_existing_role(ROLE_ID)
    
    if existing_role:
        # Step 2: Remove read-only fields and add the missing kubernetesPermissions block
        update_payload = {
            "name": existing_role["name"],
            "description": existing_role["description"],
            "permissions": existing_role["permissions"],
            "scopeType": existing_role["scopeType"],
            "scopeId": existing_role["scopeId"],
            "enabled": existing_role["enabled"],
            "kubernetesPermissions": {
                "predefinedRole": "10"
            }
        }
        
        # Step 3: Update the role
        updated_role = update_role(ROLE_ID, update_payload)
        
        if updated_role:
            print("Role updated successfully")
        else:
            print(" Failed to update role")
    else:
        print("Failed to retrieve role")
