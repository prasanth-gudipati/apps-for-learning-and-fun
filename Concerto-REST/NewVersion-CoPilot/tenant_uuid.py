#!/usr/bin/env python3
"""
Concerto REST API Client - Get Tenant UUID
Simple script to retrieve the UUID of a given tenant by name.
"""

import requests
import json
import urllib3
from typing import Optional

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class ConcertoRestClient:
    """Simple REST client for Concerto API operations."""
    
    def __init__(self, ecp_ip: str, username: str, password: str):
        """
        Initialize the REST client.
        
        Args:
            ecp_ip: IP address or hostname of the ECP server
            username: Username for authentication
            password: Password for authentication
        """
        self.ecp_ip = ecp_ip
        self.username = username
        self.password = password
        self.base_url = f"https://{ecp_ip}"  # Use standard HTTPS port 443
        self.session = requests.Session()
        self.session.verify = False  # Disable SSL verification
        self.csrf_token = None
    
    def test_connectivity(self) -> bool:
        """
        Test basic connectivity to the ECP server.
        
        Returns:
            bool: True if server is reachable, False otherwise
        """
        try:
            print(f"🔍 Testing connectivity to {self.ecp_ip}:443...")
            # Just try to establish a connection without authentication
            response = self.session.get(f"{self.base_url}/", timeout=10)
            print("✓ Server is reachable")
            return True
        except requests.exceptions.ConnectTimeout:
            print("✗ Connection timeout - Server may be down or unreachable")
            return False
        except requests.exceptions.ConnectionError as e:
            if "Failed to establish a new connection" in str(e):
                print("✗ Connection failed - Server may be down or network issue")
            else:
                print(f"✗ Connection error: {e}")
            return False
        except Exception as e:
            print(f"✗ Connectivity test failed: {e}")
            return False

    def authenticate(self) -> bool:
        """
        Authenticate with the ECP server using CSRF token method.
        
        Returns:
            bool: True if authentication successful, False otherwise
        """
        try:
            # Step 1: Get CSRF token
            print(f"� Authenticating with ECP server at {self.ecp_ip}...")
            print("   Step 1: Getting CSRF token...")
            
            response = self.session.get(f"{self.base_url}/", timeout=30)
            if response.status_code != 200:
                print(f"✗ Failed to get CSRF token: HTTP {response.status_code}")
                return False
            
            # Extract CSRF token from cookies
            csrf_token = None
            for cookie_name in ['ECP-CSRF-TOKEN', 'EECP-CSRF-TOKEN']:
                if cookie_name in self.session.cookies:
                    csrf_token = self.session.cookies[cookie_name]
                    break
            
            if not csrf_token:
                print("✗ No CSRF token found in response cookies")
                return False
            
            print(f"   ✓ CSRF token obtained: {csrf_token[:20]}...")
            self.csrf_token = csrf_token
            
            # Step 2: Login with credentials and CSRF token
            print("   Step 2: Logging in with credentials...")
            
            login_url = f"{self.base_url}/v1/auth/login"
            login_data = {
                "username": self.username,
                "password": self.password
            }
            
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'X-CSRF-TOKEN': csrf_token
            }
            
            response = self.session.post(login_url, json=login_data, headers=headers, timeout=30)
            
            if response.status_code == 200:
                print("✓ Authentication successful")
                return True
            else:
                print(f"✗ Login failed: HTTP {response.status_code}")
                if response.text:
                    print(f"   Response: {response.text[:200]}...")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"✗ Authentication error: {e}")
            return False
    
    def get_tenant_uuid(self, tenant_name: str) -> Optional[str]:
        """
        Get the UUID of a tenant by its name.
        
        Args:
            tenant_name: Name of the tenant to find
            
        Returns:
            str: UUID of the tenant if found, None otherwise
        """
        if not self.csrf_token:
            print("✗ Not authenticated. Please authenticate first.")
            return None
        
        # Use the same API endpoint as the working script
        tenant_url = f"{self.base_url}/portalapi/v1/tenants/tenant/name/{tenant_name}"
        
        try:
            print(f"🔍 Searching for tenant: {tenant_name}")
            response = self.session.get(tenant_url, timeout=30)
            
            if response.status_code == 200:
                tenant_data = response.json()
                
                # Extract UUID from response
                if 'uuid' in tenant_data:
                    uuid = tenant_data['uuid']
                    print(f"✓ Found tenant '{tenant_name}' with UUID: {uuid}")
                    return uuid
                else:
                    print(f"✗ No UUID found in response for tenant '{tenant_name}'")
                    return None
                
            elif response.status_code == 404:
                print(f"✗ Tenant '{tenant_name}' not found")
                return None
                
            else:
                print(f"✗ Failed to get tenant: HTTP {response.status_code}")
                print(f"Response: {response.text[:200]}...")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"✗ Error getting tenant UUID: {e}")
            return None
    
def main():
    """Main function to demonstrate tenant UUID lookup."""
    print("=" * 60)
    print("🎯 Concerto REST API - Tenant UUID Lookup")
    print("=" * 60)
    
    # Configuration - Update these values for your environment
    print("📋 Current Configuration:")
    ECP_IP = "10.73.70.70"  # Change this to your ECP server IP
    USERNAME = "dev1"       # Change this to your username
    PASSWORD = "dev1Versa123@"    # Change this to your password
    
    print(f"   ECP Server: {ECP_IP}:9182")
    print(f"   Username: {USERNAME}")
    print(f"   Password: {'*' * len(PASSWORD)}")
    print()
    
    # Ask user if they want to use different settings
    use_different = input("Would you like to use different connection settings? (y/n): ").strip().lower()
    if use_different == 'y':
        ECP_IP = input(f"Enter ECP Server IP (current: {ECP_IP}): ").strip() or ECP_IP
        USERNAME = input(f"Enter Username (current: {USERNAME}): ").strip() or USERNAME
        PASSWORD = input(f"Enter Password: ").strip() or PASSWORD
    
    # Create REST client
    client = ConcertoRestClient(ECP_IP, USERNAME, PASSWORD)
    
    # Authenticate
    if not client.authenticate():
        print("\n❌ Failed to authenticate. Please check your credentials and ECP server.")
        return
    
    # Simple tenant lookup
    print("\n" + "=" * 60)
    tenant_name = input("Enter tenant name (default: CNN1001): ").strip()
    if not tenant_name:
        tenant_name = "CNN1001"
    
    print(f"\n🔍 Looking up tenant: {tenant_name}")
    uuid = client.get_tenant_uuid(tenant_name)
    
    if uuid:
        print(f"\n🎯 Success! Tenant '{tenant_name}' has UUID: {uuid}")
    else:
        print(f"\n❌ Tenant '{tenant_name}' not found or error occurred")


if __name__ == "__main__":
    main()