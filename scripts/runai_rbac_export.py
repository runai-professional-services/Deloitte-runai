import requests
import csv
from datetime import datetime
from collections import defaultdict

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

def get_all_users():
    """Get all users from the users endpoint"""
    token = get_bearer_token()
    
    url = f"{APP_URL}/api/v1/users"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print(f"Users API Response Type: {type(data)}")
        
        # Handle different possible response structures
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            # Check for common nested patterns
            for key in ['users', 'data', 'items', 'results']:
                if key in data and isinstance(data[key], list):
                    return data[key]
            # If no nested structure, might be a single user or metadata
            print(f"Users response keys: {list(data.keys())}")
            return []
        else:
            print(f"Unexpected users response type: {type(data)}")
            return []
    else:
        print(f"❌ Failed to get users: {response.status_code} - {response.text}")
        return []

def find_users_without_roles():
    """Find users who don't have any role assignments"""
    print("Fetching all users...")
    all_users = get_all_users()
    
    print("Fetching access rules...")
    access_rules = get_access_rules()
    
    if not all_users:
        print("No users found")
        return [], [], []
    
    if not access_rules:
        print("No access rules found")
        return all_users, [], []
    
    print(f"Found {len(all_users)} total users")
    print(f"Found {len(access_rules)} access rules")
    
    # Extract user identifiers from access rules
    users_with_roles = set()
    for rule in access_rules:
        user_id = rule.get('subjectId')
        if user_id:
            users_with_roles.add(user_id)
    
    print(f"Users with roles: {len(users_with_roles)}")
    
    # Find users without roles
    users_without_roles = []
    users_with_roles_details = []
    
    for user in all_users:
        # Try different possible user identifier fields
        user_identifier = (
            user.get('email') or 
            user.get('username') or 
            user.get('id') or 
            user.get('userId') or
            str(user)
        )
        
        if user_identifier in users_with_roles:
            users_with_roles_details.append({
                'user_data': user,
                'identifier': user_identifier
            })
        else:
            users_without_roles.append({
                'user_data': user,
                'identifier': user_identifier
            })
    
    return users_without_roles, users_with_roles_details, access_rules

def export_comprehensive_report():
    """Export comprehensive user and role report"""
    users_without_roles, users_with_roles, access_rules = find_users_without_roles()
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Export 1: All Access Rules
    access_rules_file = f"runai_access_rules_{timestamp}.csv"
    if access_rules:
        with open(access_rules_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            headers = [
                'User ID', 'User Type', 'Role Name', 'Role ID',
                'Scope Name', 'Scope Type', 'Scope ID', 'Rule ID',
                'Created At', 'Created By'
            ]
            writer.writerow(headers)
            
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
        
        print(f"✅ Access rules exported to {access_rules_file}")
    
    # Export 2: Users WITHOUT Roles
    if users_without_roles:
        no_roles_file = f"runai_users_without_roles_{timestamp}.csv"
        with open(no_roles_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Determine headers based on first user's structure
            if users_without_roles:
                sample_user = users_without_roles[0]['user_data']
                if isinstance(sample_user, dict):
                    headers = ['Identifier'] + list(sample_user.keys())
                else:
                    headers = ['Identifier', 'User Data']
                
                writer.writerow(headers)
                
                for user_info in users_without_roles:
                    user_data = user_info['user_data']
                    identifier = user_info['identifier']
                    
                    if isinstance(user_data, dict):
                        row = [identifier] + [user_data.get(key, '') for key in sample_user.keys()]
                    else:
                        row = [identifier, str(user_data)]
                    
                    writer.writerow(row)
        
        print(f"⚠️  Users without roles exported to {no_roles_file}")
    else:
        print("✅ All users have role assignments!")
    
    # Export 3: Summary Report
    summary_file = f"runai_user_role_summary_{timestamp}.txt"
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("RunAI User and Role Assignment Summary\n")
        f.write("=" * 50 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write(f"Total Users: {len(users_without_roles) + len(users_with_roles)}\n")
        f.write(f"Users with Roles: {len(users_with_roles)}\n")
        f.write(f"Users without Roles: {len(users_without_roles)}\n")
        f.write(f"Total Access Rules: {len(access_rules)}\n\n")
        
        if users_without_roles:
            f.write("USERS WITHOUT ROLE ASSIGNMENTS:\n")
            f.write("-" * 35 + "\n")
            for user_info in users_without_roles:
                f.write(f"- {user_info['identifier']}\n")
            f.write("\n")
        
        # Role distribution
        if access_rules:
            role_counts = defaultdict(int)
            for rule in access_rules:
                role = rule.get('roleName', 'Unknown')
                role_counts[role] += 1
            
            f.write("ROLE DISTRIBUTION:\n")
            f.write("-" * 18 + "\n")
            for role, count in sorted(role_counts.items()):
                f.write(f"- {role}: {count} assignments\n")
    
    print(f"📊 Summary report saved to {summary_file}")
    
    # Print console summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"Total Users: {len(users_without_roles) + len(users_with_roles)}")
    print(f"Users with Roles: {len(users_with_roles)}")
    print(f"Users without Roles: {len(users_without_roles)}")
    
    if users_without_roles:
        print(f"\n⚠️  USERS WITHOUT ROLE ASSIGNMENTS:")
        for user_info in users_without_roles[:10]:  # Show first 10
            print(f"   - {user_info['identifier']}")
        if len(users_without_roles) > 10:
            print(f"   ... and {len(users_without_roles) - 10} more")

if __name__ == "__main__":
    export_comprehensive_report()
