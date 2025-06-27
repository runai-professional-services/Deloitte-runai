import requests
import csv
from datetime import datetime

# Configuration
CLIENT_ID = 'xx'
CLIENT_SECRET = 'xx'
APP_URL = 'https://dummy.com'   
REALM = 'runai'

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

def get_access_rules():
    """Get all access rules"""
    token = get_bearer_token()
    
    url = f"{APP_URL}/api/v1/authorization/access-rules"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        return data.get('accessRules', [])
    else:
        print(f"❌ Failed to get access rules: {response.status_code} - {response.text}")
        return []

def export_to_csv():
    """Export access rules to CSV file"""
    print("Fetching access rules...")
    access_rules = get_access_rules()
    
    if not access_rules:
        print("No access rules found")
        return
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"runai_access_rules_{timestamp}.csv"
    
    # CSV headers
    headers = [
        'User ID', 
        'User Type', 
        'Role Name', 
        'Role ID',
        'Scope Name', 
        'Scope Type', 
        'Scope ID',
        'Rule ID',
        'Created At',
        'Created By'
    ]
    
    print(f"Writing {len(access_rules)} rules to {filename}...")
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        
        # Write headers
        writer.writerow(headers)
        
        # Write data rows
        for rule in access_rules:
            row = [
                rule.get('subjectId', ''),
                rule.get('subjectType', ''),
                rule.get('roleName', ''),
                rule.get('roleId', ''),
                rule.get('scopeName', ''),
                rule.get('scopeType', ''),
                rule.get('scopeId', ''),
                rule.get('id', ''),
                rule.get('createdAt', ''),
                rule.get('createdBy', '')
            ]
            writer.writerow(row)
    
    print(f"✅ Successfully exported to {filename}")
    
    # Print summary
    print(f"\nSummary:")
    print(f"Total rules: {len(access_rules)}")
    
    # Count unique users
    unique_users = set(rule.get('subjectId', '') for rule in access_rules)
    print(f"Unique users: {len(unique_users)}")
    
    # Count by role
    role_counts = {}
    for rule in access_rules:
        role = rule.get('roleName', 'Unknown')
        role_counts[role] = role_counts.get(role, 0) + 1
    
    print(f"Roles distribution:")
    for role, count in sorted(role_counts.items()):
        print(f"  - {role}: {count}")

if __name__ == "__main__":
    export_to_csv()
