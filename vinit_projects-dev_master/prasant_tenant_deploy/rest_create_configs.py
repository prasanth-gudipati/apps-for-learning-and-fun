#!/usr/bin/python3

import requests
#from jsonpath_ng import jsonpath, parse
from jsonpath import JSONPath
import re
import argparse
import pdb
import json
import policy_elements_payloads
import uuid
from jinja2 import Template
import log_handler
import sys
import csv

class RestApi(object):
    def __init__(self,ecp_ip,user,password):
        self.ecp_ip = ecp_ip
        self.user = user
        self.password = password
        self.logger = log_handler.Logger()
        headers = {'Content-Type': 'application/json','Accept': 'application/json'}
        payload = ''
        url = "https://%s" % ecp_ip

        response = requests.request("GET", url, headers=headers, data=payload, verify=False)
        tmp_token = response.cookies['ECP-CSRF-TOKEN']
        headers['X-CSRF-TOKEN'] = tmp_token
        self.logger.banner_log('login to ecp and fetch session cookie')
        payload = '{"username":"%s","password":"%s"}' % (self.user,self.password)
        session = requests.request("POST", "https://%s/v1/auth/login" % self.ecp_ip, 
                headers=headers, 
                data=payload, 
                verify=False, 
                cookies=response.cookies)

        if int(int(session.status_code)/100) != 2:
            self.logger.error_log('Api Failed')
            self.logger.error_log('Api Response Status code: %s' % session.status_code)
            self.logger.error_log('Api Response Reason: %s' % session.reason)
            self.logger.error_log('Api Response Text: %s' % json.dumps(json.loads(session.text),indent=4))
            return sys.exit(1)

        self.SESSION_COOKIE = session.cookies
        self.CSRF_TOKEN = session.cookies['ECP-CSRF-TOKEN']
        #overwrite csrf token
        headers['X-CSRF-TOKEN'] =  self.CSRF_TOKEN
        self.headers = headers
    
    def convert_csv_dict(self,csv):
        '''
        Helper to convert csv to dict
        '''
        with open(csv, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
        return reader

    def api_call(self,method,url,data):
        '''
        Helper to execute api's
        '''
        self.logger.info_log('Executing Api : %s' % url)
        self.logger.info_log('Api Method : %s' % method)
        self.logger.info_log('Api Header : %s' % json.dumps(self.headers,indent=4))
        self.logger.info_log('Api data : %s' % json.dumps(data,indent=4))

        resp = requests.request(method, url, headers=self.headers, data=data,verify=False,cookies=self.SESSION_COOKIE)
        if int(int(resp.status_code)/100) != 2:
            self.logger.error_log('Api Failed')
            self.logger.error_log('Api Response Status code: %s' % resp.status_code)
            self.logger.error_log('Api Response Reason: %s' % resp.reason)
            self.logger.error_log('Api Response Text: %s' % json.dumps(json.loads(resp.text),indent=4))
            return False
        else:
            self.logger.info_log('Api Succeeded')
            self.logger.info_log('Api Response Status code: %s' % resp.status_code)
            self.logger.info_log('Api Response Reason: %s' % resp.reason)
            self.logger.info_log('Api Response Text: %s' % json.dumps(json.loads(resp.text),indent=4))
            return resp

    def generate_url(self,api):
        '''
        Helper to generate url from api
        '''
        return "https://%s%s" % (self.ecp_ip,api)

    def fetch_tenant_uuid(self,name):
        self.logger.info_log('Fetching tenant %s uuid' % name)
        url = self.generate_url('/portalapi/v1/tenants/tenant/name/%s' % name)
        resp = self.api_call(method='GET',url=url,data='')
        if not resp:
            self.logger.error_log('Failed to fetch tenant %s uuid' % name)
            sys.exit(1)
        json_dict = json.loads(resp.text)
        #jsonpath_expr = JSONPath('$.tenantInfo.uuid').parse(resp.text)[0]
        #uuid = jsonpath_expr.find(json_dict)[0].value
        uuid  = JSONPath('$.tenantInfo.uuid').parse(json_dict)[0]
        return uuid

    def fetch_profile_perspective(self,tenant_name,tenant_uuid):
        url = self.generate_url('/portalapi/v1/tenants/%s/configuration/perspective/profile' % tenantuuid)
        resp = self.api_call(method='GET',url=url,data='')
        if not resp:
            self.logger.error_log('Failed to fetch the profile perspective for tenant %s' % tenant_name)
            sys.exit(1)
        return json.loads(resp.text)


    def fetch_profile_elements_perspective(self,tenant_name,tenant_uuid):
        url = self.generate_url('/portalapi/v1/tenants/%s/configuration/perspective/profile-elements' % tenantuuid)
        resp = self.api_call(method='GET',url=url,data='')
        if not resp:
            self.logger.error_log('Failed to fetch the profile element perspective for tenant %s' % tenant_name)
            sys.exit(1)
        return json.loads(resp.text)

    def create_static_wan(self,
            tenant_name,
            tenant_uuid,
            profile_element_perspective,
            wan_name,location):
        parent_reference_uuid = JSONPath('$.perspective[?(@.name=="Policy Elements")]..nodes[?(@.name=="Interface")].uuid').parse(profile_element_perspective)[0]
        self.logger.info_log('Creating wan interface %s on tenant %s' % (wan_name,tenant_name))
        url = self.generate_url('/portalapi/v1/tenants/%s/rules/device' % tenant_uuid)
        template = Template(policy_elements_payloads.static_wan)
        payload = template.render(elt_uuid=str(uuid.uuid4()),
                            intf_ip_uuid=str(uuid.uuid4()),
                            intf_next_hp_uuid=str(uuid.uuid4()),
                            parent_reference_uuid=parent_reference_uuid,
                            name=wan_name,
                            location=location)

        resp = self.api_call(method='POST',url=url,data=payload)
        if not resp:
            self.logger.error_log('Failed to create wan interface %s on tenant %s' % (wan_name,tenant_name))
            sys.exit(1)
        return resp

    def create_static_lan(self,
            tenant_name,
            tenant_uuid,
            profile_element_perspective,
            lan_name,
            location):
        parent_reference_uuid = JSONPath('$.perspective[?(@.name=="Policy Elements")]..nodes[?(@.name=="Interface")].uuid').parse(profile_element_perspective)[0]
        self.logger.info_log('Creating lan interface %s on tenant %s' % (lan_name,tenant_name))

        url = self.generate_url('/portalapi/v1/tenants/%s/rules/device' % tenant_uuid)
        template = Template(policy_elements_payloads.static_lan)
        payload = template.render(elt_uuid=str(uuid.uuid4()),
                            lan_ip_uuid=str(uuid.uuid4()),
                            parent_reference_uuid=parent_reference_uuid,
                            name=lan_name,
                            location=location)

        resp = self.api_call(method='POST',url=url,data=payload)
        if not resp:
            self.logger.error_log('Failed to create wan interface %s on tenant %s' % (lan_name,tenant_name))
            sys.exit(1)
        return resp
    
    def create_device_policy(self,
            tenant_name,
            tenant_uuid,
            profile_element_perspective,
            policy_name,
            location):
        parent_reference_uuid = JSONPath('$.perspective[?(@.name=="Policies")]..nodes[?(@.name=="Interface")].uuid').parse(profile_element_perspective)[0]
        
        self.logger.info_log('Generate Device Policy Graph')
        url =self.generate_url('/portalapi/v1/tenants/%s/policies/device/interface' % tenant_uuid)
        template = Template(policy_payloads.device_policy_graph)
        payload = template.render(device_policy_uuid=device_policy_uuid,
                            parent_reference_uuid=parent_reference_uuid,
                            policy_name=policy_name)

        device_policy_graph = self.api_call(method='POST',url=url,data=payload)
        if not device_policy_graph:
            self.logger.error_log('Failed to create Device Policy Graph %s on tenant %s' % (policy_name,tenant_name))
            sys.exit(1)

        self.logger.info_log('Fetch all interface ref')
        url = self.generate_url('/portalapi/v1/tenants/%s/rules/device/all/getInterfaceRef' % tenant_uuid)
        interface_ref = self.api_call(method='POST',url=url,data=payload)

        self.logger.info_log('Start federated transcation')
        url = self.generate_url('/portalapi/v1/tenants/%s/transaction/startFederatedTransaction' % tenant_uuid)
        interface_ref = self.api_call(method='POST',url=url,data=payload)

        self.logger.info_log('Attach Interfaces')
        url = self.generate_url('/portalapi/v1/tenants/%s/rules/device/attach' % tenant_uuid)
        interface_ref = self.api_call(method='POST',url=url,data=payload)
        self.logger.info_log('Creating a device policy %s on tenant %s' % (policy_name,tenant_name))
        
            

        url = self.generate_url('/portalapi/v1/tenants/%s/rules/device' % tenant_uuid)
        template = Template(policy_elements_payloads.static_lan)
        payload = template.render(elt_uuid=str(uuid.uuid4()),
                            lan_ip_uuid=str(uuid.uuid4()),
                            parent_reference_uuid=parent_reference_uuid,
                            name=lan_name,
                            location=location)

        resp = self.api_call(method='POST',url=url,data=payload)
        if not resp:
            self.logger.error_log('Failed to create wan interface %s on tenant %s' % (lan_name,tenant_name))
            sys.exit(1)
        return resp
       
if __name__ == '__main__':
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument('-ip',
                        help='ecp_ip')
    parser.add_argument('-user',
                        help='user')
    parser.add_argument('-password',
                        help='password')
    parser.add_argument('-tenant',
                        help='tenant name')

    args = parser.parse_args()
    ip = args.ip
    user = args.user
    password = args.password
    tenant = args.tenant
    restHdl = RestApi(ip,user,password)
    tenantuuid = restHdl.fetch_tenant_uuid(name=tenant)
    profile_element_perspective = restHdl.fetch_profile_elements_perspective(tenant_name=tenant,tenant_uuid=tenantuuid)
    profile_perspective = restHdl.fetch_profile_perspective(tenant_name=tenant,tenant_uuid=tenantuuid)
    restHdl.create_static_wan(tenant_name=tenant,
                                tenant_uuid=tenantuuid,
                                profile_element_perspective=profile_element_perspective,
                                wan_name='WAN1',
                                location='vni-0/0')
    restHdl.create_static_lan(tenant_name=tenant,
                                tenant_uuid=tenantuuid,
                                profile_element_perspective=profile_element_perspective,
                                lan_name='LAN1',
                                location='vni-0/1')
