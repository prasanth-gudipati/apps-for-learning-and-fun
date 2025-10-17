#!/usr/bin/python3

import requests
import time
from jsonpath_ng import parse
import re
import argparse

# JSONPath compatibility class
class JSONPath:
    def __init__(self, path):
        self.path = path
        self.expr = parse(path)
    
    def parse(self, data):
        matches = self.expr.find(data)
        return [match.value for match in matches]
import pdb
import json
import appliance_payloads
import uuid
from jinja2 import Template
import log_handler
import sys
import csv

class CsvHandler(object):
    def __init__(self,csvfile):
        self.csvlist = self.convert_csv_dict(csvfile)
        self.deviceinfo = self.fetch_device_info(self.csvlist)

    def convert_csv_dict(self,csvfile):
        '''
        Helper to convert csv to dict
        '''
        csvobject = open(csvfile, newline='')
        reader = csv.DictReader(csvobject)
        return [ line for line in reader ]

    def fetch_device_info(self,csvlist):
        '''
        Helper to fetch the device info in the required format
        '''
        deviceInfo = []
        for elt in csvlist:
            d1 = {'parameters':{}}
            for key in [ *elt.keys() ]:
                if 'parameter_' in key:
                    d1['parameters'][key.split('parameter_')[1]] = elt[key]
                else:
                    d1[key] = elt[key]
            deviceInfo.append(d1)
        return deviceInfo

        
class RestApi(object):
    def __init__(self,ecp_ip,user,password):
        self.ecp_ip = ecp_ip
        self.user = user
        self.password = password
        self.logger = log_handler.Logger()
        #headers = {'Content-Type': 'application/json','Accept': 'application/json,application/xml'}
        #headers = {'Content-Type': 'application/json','Accept': 'application/json'}
        #headers = {'Accept': 'application/json'}
        headers = {}
        payload = ''
        url = "https://%s" % ecp_ip

        response = requests.request("GET", url, headers=headers, data=payload, verify=False)
        tmp_token = response.cookies['ECP-CSRF-TOKEN']

        headers = {'Content-Type': 'application/json','Accept': 'application/json'}
        headers['X-CSRF-TOKEN'] = tmp_token
        self.logger.banner_log('login to ecp and fetch session cookie')
        payload = '{"username":"%s","password":"%s"}' % (self.user,self.password)
        session = requests.request("POST", "https://%s/v1/auth/login" % self.ecp_ip, 
                headers=headers, 
                data=payload, 
                verify=False, 
                cookies=response.cookies)

        if int(int(session.status_code)/100) != 2:
            self.logger.console_log(f'Login Failed: {session.status_code} - {session.reason}', "ERROR")
            self.logger.error_log('Api Failed')
            self.logger.error_log('Api Response Status code: %s' % session.status_code)
            self.logger.error_log('Api Response Reason: %s' % session.reason)
            self.logger.payload_log('LOGIN ERROR RESPONSE', json.dumps(json.loads(session.text), indent=4), "ERROR")
            return sys.exit(1)

        self.SESSION_COOKIE = session.cookies
        self.CSRF_TOKEN = session.cookies['ECP-CSRF-TOKEN']
        #overwrite csrf token
        headers['X-CSRF-TOKEN'] =  self.CSRF_TOKEN
        self.headers = headers
    
    def api_call(self,method,url,data):
        '''
        Helper to execute api's
        '''
        # Console logs (short info only)
        self.logger.console_log(f'Executing API: {method} {url}')
        
        # File logs (detailed info)
        self.logger.info_log('Executing Api : %s' % url)
        self.logger.info_log('Api Method : %s' % method)
        
        # Log headers and data to payload log file (not console)
        self.logger.payload_log('API REQUEST HEADERS', json.dumps(self.headers, indent=4))
        
        if data:
            try:
                data_dict = json.loads(data)
                self.logger.payload_log('API REQUEST PAYLOAD', json.dumps(data_dict, indent=4))
            except Exception:
                self.logger.payload_log('API REQUEST PAYLOAD (RAW)', str(data))

        resp = requests.request(method, url, headers=self.headers, data=data,verify=False,cookies=self.SESSION_COOKIE)
        if int(int(resp.status_code)/100) != 2:
            self.logger.console_log(f'API Failed: {resp.status_code} - {resp.reason}', "ERROR")
            self.logger.error_log('Api Failed')
            self.logger.error_log('Api Response Status code: %s' % resp.status_code)
            self.logger.error_log('Api Response Reason: %s' % resp.reason)
            if resp.text:
                self.logger.payload_log('API ERROR RESPONSE', json.dumps(json.loads(resp.text), indent=4), "ERROR")
            return False
        else:
            self.logger.console_log(f'API Succeeded: {resp.status_code}')
            self.logger.info_log('Api Succeeded')
            self.logger.info_log('Api Response Status code: %s' % resp.status_code)
            self.logger.info_log('Api Response Reason: %s' % resp.reason)
            if resp.text:
                self.logger.payload_log('API SUCCESS RESPONSE', json.dumps(json.loads(resp.text), indent=4))
            return resp

    def generate_url(self,api):
        '''
        Helper to generate url from api
        '''
        return "https://%s%s" % (self.ecp_ip,api)
    
    def json_extract(self, json_data, path):
        '''
        Helper to extract data using JSONPath
        '''
        jsonpath_expr = parse(path)
        matches = jsonpath_expr.find(json_data)
        return [match.value for match in matches] if matches else []

    def fetch_tenant_uuid(self,name):
        self.logger.info_log('Fetching tenant %s uuid' % name)
        url = self.generate_url('/portalapi/v1/tenants/tenant/name/%s' % name)
        resp = self.api_call(method='GET',url=url,data='')
        if not resp:
            self.logger.error_log('Failed to fetch tenant %s uuid' % name)
            sys.exit(1)
        json_dict = json.loads(resp.text)
        # Using helper method for JSONPath extraction
        uuid_list = self.json_extract(json_dict, '$.tenantInfo.uuid')
        if uuid_list:
            uuid = uuid_list[0]
        else:
            self.logger.error_log('Failed to find tenant UUID in response')
            sys.exit(1)
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

    def fetch_site_perspective(self,tenant_name,tenant_uuid):
        url = self.generate_url('/portalapi/v1/tenants/%s/deploy/perspective/site' % tenantuuid)
        resp = self.api_call(method='GET',url=url,data='')
        if not resp:
            self.logger.error_log('Failed to fetch the site perspective for tenant %s' % tenant_name)
            sys.exit(1)
        return json.loads(resp.text)

    def fetch_appliance_perspective(self,tenant_name,tenant_uuid):
        url = self.generate_url('/portalapi/v1/tenants/%s/deploy/perspective/appliance' % tenantuuid)
        resp = self.api_call(method='GET',url=url,data='')
        if not resp:
            self.logger.error_log('Failed to fetch the profile element perspective for tenant %s' % tenant_name)
            sys.exit(1)
        return json.loads(resp.text)

    def fetch_tenant_summary(self,tenant_name):
        url = self.generate_url('/portalapi/v1/tenants/tenant/name/%s' % tenant_name)
        resp = self.api_call(method='GET',url=url,data='')
        if not resp:
            self.logger.error_log('Failed to fetch the config summary for tenant %s' % tenant_name)
            sys.exit(1)
        return json.loads(resp.text)

    def fetch_site_summary(self,tenant_name,
            tenant_uuid,site_name):
        #url = self.generate_url('/portalapi/v1/tenants/%s/sites/getByName/%s' % (tenant_uuid,site_name))
        url = self.generate_url('/portalapi/v1/tenants/%s/sites?nextWindowNumber=0&windowSize=10&searchKeyword=%s' % (tenant_uuid,site_name))
        resp = self.api_call(method='GET',url=url,data='')
        if not resp:
            self.logger.error_log('Failed to fetch the site summary for tenant %s' % tenant_name)
            return {}
        return json.loads(resp.text)

    def fetch_appliance_summary(self,tenant_name,
            tenant_uuid,
            tenant_summary,
            site_uuid):
        url = self.generate_url('/portalapi/v1/tenants/%s/sites/%s/summarize' % (tenant_uuid,site_uuid))
        resp = self.api_call(method='GET',url=url,data='')
        if not resp:
            self.logger.error_log('Failed to fetch the site summary for tenant %s' % tenant_name)
            sys.exit(1)
        return json.loads(resp.text)

    def fetch_basic_mp_summary(self,tenant_name,
            tenant_uuid,masterprofilename):
        url = self.generate_url('/portalapi/v1/tenants/%s/profiles/basic/summarize?nextWindowNumber=0&windowSize=100&stackVersionName=%s' % (tenant_uuid, masterprofilename))
        resp = self.api_call(method='GET',url=url,data='')
        if not resp:
            self.logger.error_log('Failed to fetch the basic master profile summary for tenant %s' % tenant_name)
            sys.exit(1)
        return json.loads(resp.text)

    def fetch_standard_mp_summary(self,tenant_name,
            tenant_uuid,masterprofilename):
        url = self.generate_url('/portalapi/v1/tenants/%s/profiles/standard/summarize?nextWindowNumber=0&windowSize=10&stackVersionName=%s' % (tenant_uuid, masterprofilename))
        resp = self.api_call(method='GET',url=url,data='')
        if not resp:
            self.logger.error_log('Failed to fetch the standard master profile summary for tenant %s' % tenant_name)
            sys.exit(1)
        return json.loads(resp.text)
    
    def fetch_regions(self,tenant_name,tenant_uuid):
        url = self.generate_url('/portalapi/v1/tenants/%s/regions/summary' % (tenant_uuid))
        resp = self.api_call(method='GET',url=url,data='')
        if not resp:
            self.logger.error_log('Failed to fetch the regions configured for tenant %s' % tenant_name)
            sys.exit(1)
        return json.loads(resp.text)

    def create_site(self,tenant_name,
            director_name,
            tenant_uuid,
            tenant_summary,
            region_summary,
            site_perspective,
            site_name, 
            country, 
            zipcode,
            street='',
            city='',
            state='',
            region=''):
        site_uuid=None
        if not region:
            region = 'Default'

        region_uuid = JSONPath('$.data[?(@.name=="%s")].uuid' % region).parse(region_summary)[0]
        site_summary = self.fetch_site_summary(tenant_name,tenant_uuid,site_name)
        #result = JSONPath('$.entityRef.uuid').parse(site_summary)
        result = JSONPath('$.siteData[0].entity.uuid').parse(site_summary)
        if result:
            self.logger.info_log('Site %s exits' % site_name)
            site_uuid = result[0]
            method = 'PUT'
            self.logger.info_log('Updating Site %s on tenant %s' % (site_name,tenant_name))
            url_site = self.generate_url('/portalapi/v1/tenants/%s/sites/%s' % (tenant_uuid,site_uuid))
        else:
            method = 'POST'
            self.logger.info_log('Creating Site %s on tenant %s' % (site_name,tenant_name))
            url_site = self.generate_url('/portalapi/v1/tenants/%s/sites/' % tenant_uuid)
        
        result = JSONPath('$..defaultDirector').parse(tenant_summary)
        if result[0]['name'] == director_name:
            directoruuid = result[0]['uuid']
        else:
            result = JSONPath('$..directors[?(@.name=="%s")].uuid' % director_name).parse(tenant_summary)
            if result:
                directoruuid = result[0]
            else:
                self.logger.error.log('Failed to find director %s in the database' % director_name)
                sys.exit(1)

        url = 'https://maps.googleapis.com/maps/api/geocode/json?=&channel=director&key=AIzaSyClGMMbtFFOWlXD3AdcVZq4oE4kjknY9Gc&address='
        if street:
            url = url + street + ','
        if city:
            url = url + city + ','
        if state:
            url = url + state + ','
        url = url + country + ',' + zipcode
        headers = {'Content-Type': 'application/json','Accept': 'application/json'}
        response = requests.request("GET", url, headers=headers, data='', verify=False)
        if not isinstance(json.loads(response.text)['results'],list):
            self.logger.error_log('Failed to fetch latitude longitude info for the location : {street} , {city} , {state}, {country}, {zipcode}. Please check the address'.format(street=street, city=city, state=state, country=country,zipcode=zipcode))
            sys.exit(1)
        elif not json.loads(response.text)['results']:
            self.logger.error_log('Failed to fetch latitude longitude info for the location : {street} , {city} , {state}, {country}, {zipcode}. Please check the address'.format(street=street, city=city, state=state, country=country,zipcode=zipcode))
            sys.exit(1) 
        latitude = JSONPath('$..lat').parse(json.loads(response.text))[0]
        longitude = JSONPath('$..lng').parse(json.loads(response.text))[0]

        parent_reference_uuid=JSONPath('$.perspective[0].uuid').parse(site_perspective)[0]

        template = Template(appliance_payloads.site_create)
        data = template.render(name=site_name,director_uuid=directoruuid,street=street,city=city,state=state,country=country,zipcode=zipcode,latitude=latitude,longitude=longitude,parent_reference_uuid=parent_reference_uuid,site_uuid=site_uuid,region_uuid=region_uuid)
        resp = self.api_call(method=method,url=url_site,data=data)
        if not resp:
            self.logger.error_log('Failed to create the site %s for tenant %s' % (site_name,tenant_name))
            sys.exit(1)
        return json.loads(resp.text)

    def create_device(self,tenant_name,
            tenant_uuid,
            tenant_summary,
            site_name,
            appliance_name,
            appliance_perspective,
            deviceInfo):
        self.logger.info_log('Fetch Site summary on tenant %s' % tenant_name)
        site_summary = restHdl.fetch_site_summary(tenant_name=tenant,tenant_uuid=tenantuuid,site_name=site_name)
        siteuuid = None

        result = JSONPath('$.siteData[0].entity.uuid').parse(site_summary)
        #result = JSONPath('$.entityRef.uuid').parse(site_summary)
        if result:
            siteuuid = result[0]
        
        if not siteuuid:
            self.logger.error_log('Failed to find site %s in the database' % site_name)
            sys.exit(1)

        if deviceInfo['masterprofiletype'].lower() == 'standard':
            self.logger.info_log('Fetch Standard Master Profile summary for tenant %s' % tenant_name)
            resp = self.fetch_standard_mp_summary(tenant_name=tenant,tenant_uuid=tenantuuid,masterprofilename=deviceInfo['masterprofilename'])
        else:
            self.logger.info_log('Fetch Basic Master Profile summary for tenant %s' % tenant_name)
            resp = self.fetch_basic_mp_summary(tenant_name=tenant,tenant_uuid=tenantuuid,masterprofilename=deviceInfo['masterprofilename'])
        
        masterprofileuuid = None
        result = JSONPath('$.data[?(@.entity.name=="%s" and @.entity.version=="%s")].entity.uuid' % (deviceInfo['masterprofilename'],deviceInfo['masterprofileversion'])).parse(resp)
        if result:
            masterprofileuuid = result[0]
        #for masterprofile in JSONPath('$.data[*].entity').parse(resp):
        #    if masterprofile['name'] == deviceInfo['masterprofilename'] and masterprofile['version'] == deviceInfo['masterprofileversion']:
        #        masterprofileuuid = masterprofile['uuid']
        #        break

        if not masterprofileuuid:
            self.logger.error_log('Failed to find the master profile %s in the database' % deviceInfo['masterprofilename'])
            sys.exit(1)

        parent_reference_uuid =  JSONPath('$.perspective[0].uuid').parse(appliance_perspective)[0]
    
        self.logger.info_log('Check for Appliance %s on site %s' % (appliance_name,site_name))
        url = self.generate_url('/portalapi/v1/tenants/%s/sites/%s/appliances?nextWindowNumber=0&windowSize=100' % (tenant_uuid,siteuuid))
        data = ''
        resp = self.api_call(method='GET',url=url,data=data)
        if not resp:
            self.logger.error_log('Failed to fetch appliance list from the site %s on tenant %s' % (site_name,tenant_name))
            sys.exit(1)

        result = JSONPath('$.data[?(@.entity.name=="%s")].entity.uuid' % appliance_name).parse(json.loads(resp.text))
        if not result:
            self.logger.info_log('Create Appliance %s on site %s' % (appliance_name,site_name))
            url = self.generate_url('/portalapi/v1/tenants/%s/appliances' % tenantuuid)
            template = Template(appliance_payloads.appliance_create)
            data = template.render(appliance_name=appliance_name,
                    site_uuid=siteuuid,
                    serial_number=deviceInfo['serialnum'],
                    bandwidth=deviceInfo['bandwidth'],
                    vpn_profile=deviceInfo['vpn_profile'],
                    stagingController=deviceInfo['stagingController'],
                    ztp_type=deviceInfo['ztptype'],
                    ztp_email=deviceInfo['ztpemail'],
                    isHub = 'false',
                    master_profile_name=deviceInfo['masterprofilename'],
                    master_profile_version=deviceInfo['masterprofileversion'],
                    master_profile_uuid=masterprofileuuid,
                    master_profile_type=deviceInfo['masterprofiletype'],
                    parent_reference_uuid=parent_reference_uuid)
            
            resp = self.api_call(method='POST',url=url,data=data)
            if not resp:
                self.logger.error_log('Failed to create appliance %s on site %s' % (appliance_name,site_name))
                sys.exit(1)
            #For HA pair deploy redundant device
            if 'redundant_devicename' in deviceInfo:
                if deviceInfo['redundant_devicename']:
                    primary_appliance_uuid = JSONPath('$.entity.uuid').parse(json.loads(resp.text))[0]
                    url = self.generate_url('/portalapi/v1/tenants/%s/appliances/%s/redundant/' % (tenantuuid,primary_appliance_uuid))
                    data = template.render(appliance_name=deviceInfo['redundant_devicename'],
                            site_uuid=siteuuid,
                            serial_number=deviceInfo['redundant_serialnum'],
                            bandwidth=deviceInfo['bandwidth'],
                            vpn_profile=deviceInfo['vpn_profile'],
                            stagingController=deviceInfo['stagingController'],
                            ztp_type=deviceInfo['ztptype'],
                            ztp_email=deviceInfo['ztpemail'],
                            isHub = 'false',
                            master_profile_name=deviceInfo['masterprofilename'],
                            master_profile_version=deviceInfo['masterprofileversion'],
                            master_profile_uuid=masterprofileuuid,
                            master_profile_type=deviceInfo['masterprofiletype'],
                            parent_reference_uuid=parent_reference_uuid)
                    resp = self.api_call(method='POST',url=url,data=data)
            if not resp:
                self.logger.error_log('Failed to create appliance %s on site %s' % (deviceInfo['redundant_devicename'],site_name))
                sys.exit(1)
        else:
            appliance_uuid = result[0]
            self.logger.info_log('Updating Master Profile on Appliance %s on site %s' % (appliance_name,site_name))
            url = self.generate_url('/portalapi/v1/tenants/%s/appliances/setProfile' % tenantuuid)
            template = Template(appliance_payloads.appliance_update_master_profile)
            data = template.render(appliance_uuid=appliance_uuid,masterprofiletype=deviceInfo['masterprofiletype'].capitalize(),masterprofilename=deviceInfo['masterprofilename'],masterprofileversion=deviceInfo['masterprofileversion'])
            resp = self.api_call(method='PUT',url=url,data=data)
            if not resp:
                self.logger.error_log('Failed to update the master profile for appliance %s on the site %s' % (appliance_name,site_name))
                sys.exit(1)
 
        self.logger.info_log('Fill bind data for Appliance %s on site %s' % (appliance_name,site_name))
        
        url = self.generate_url('/portalapi/v1/tenants/{tenant_uuid}/profiles/basic/DeploymentLifecycleGraph%252FAPPLIANCES%252FAppliance%252F%252F{appliance_name}-1%252F{masterprofilename}-{masterprofileversion}'.format(tenant_uuid=tenant_uuid,appliance_name=appliance_name,masterprofilename=deviceInfo['masterprofilename'],masterprofileversion=deviceInfo['masterprofileversion']))
        deployment_graph = self.api_call(method='GET',url=url,data='').text
        
        permission_graph = json.loads(json.loads(deployment_graph)['permissionGraph'])
        permissions_list = []
        for elt in permission_graph['permissionsGraph']['permissionsGraph']:
            if elt['nodeType'] == 'ENTITY':
                elt['entityPermissions'] = []
                elt.pop('entityEditMode')
                elt.pop('permissions')
            permissions_list.append(elt)
        permission_graph['permissionsGraph']['permissionsGraph'] = permissions_list

        parameter_graph = json.loads(json.loads(deployment_graph)['parameterGraph'])
        variable_list = []
        for variable in parameter_graph['parameterGraph']['parameterDefinitions']['variables']:
            variable['value'] = deviceInfo['parameters'][variable['name']]
            variable_list.append(variable)
        parameter_graph['parameterGraph']['parameterDefinitions']['variables'] = variable_list
        
        deployment_graph_dict = json.loads(deployment_graph)
        deployment_graph_dict['parameterGraph'] = json.dumps(parameter_graph)
        deployment_graph_dict['permissionGraph'] = json.dumps(permission_graph)
        updated_deployment_graph = json.dumps(deployment_graph_dict,indent=4)
        
        url = self.generate_url('/portalapi/v1/tenants/%s/transaction/startFederatedTransaction' % tenant_uuid)
        data = json.dumps({"entityFederatedPath": JSONPath('$.entity.federatedPath').parse(deployment_graph_dict)[0]})
        resp = self.api_call(method='POST',url=url,data=data)
        if not resp:
            self.logger.error_log('Failed to start federated transaction for tenant %s' % tenant_name)
            sys.exit(1) 
        transaction_id = json.loads(resp.text)["transactionId"]

        url = self.generate_url('/portalapi/v1/tenants/{tenant_uuid}/profiles/basic/DeploymentLifecycleGraph%252FAPPLIANCES%252FAppliance%252F%252F{appliance_name}-1%252F{masterprofilename}-{masterprofileversion}'.format(tenant_uuid=tenant_uuid,appliance_name=appliance_name,masterprofilename=deviceInfo['masterprofilename'],masterprofileversion=deviceInfo['masterprofileversion']))
        resp = self.api_call(method='PUT',url=url,data=updated_deployment_graph)
        if not resp:
            self.logger.error_log('Failed to update device binddata for tenant %s' % appliance_name)
            sys.exit(1) 

        url = self.generate_url('/portalapi/v1/tenants/%s/transaction/%s/commit' % (tenant_uuid,transaction_id))
        resp = self.api_call(method='POST',url=url,data='')
        if not resp:
            self.logger.error_log('Failed to update device binddata for tenant %s' % tenant_name)
            sys.exit(1) 
        
        self.logger.info_log('Publish Appliance %s on tenant %s' % (appliance_name,tenant_name))

        url = self.generate_url('/portalapi/v1/tenants/%s/appliances/publish' % tenant_uuid)
        parent_reference_uuid =  JSONPath('$.perspective[0].uuid').parse(appliance_perspective)[0]
        template = Template(appliance_payloads.appliance_publish)
        data = template.render(appliancename=appliance_name,parent_reference_uuid=parent_reference_uuid)
        resp = self.api_call(method='PUT',url=url,data=data)
        if not resp:
            self.logger.error_log('Failed to publish device %s for tenant %s' % (appliance_name,tenant_name))
            sys.exit(1)
        task_id = [ *json.loads(resp.text).values() ][0]
        
        self.logger.info_log('Check publish appliance %s status on tenant %s' % (appliance_name,tenant_name))
        if not self.check_task_status(task_id):
            sys.exit(1)
        

        if 'redundant_devicename' in deviceInfo:
            if deviceInfo['redundant_devicename']:
                self.logger.info_log('Publish Redundant Appliance %s on tenant %s' % (deviceInfo['redundant_devicename'],tenant_name))
                data = template.render(appliancename=deviceInfo['redundant_devicename'],parent_reference_uuid=parent_reference_uuid)
                resp = self.api_call(method='PUT',url=url,data=data)
                if not resp:
                    self.logger.error_log('Failed to publish device %s for tenant %s' % (deviceInfo['redundant_devicename'],tenant_name))
                    sys.exit(1)
                task_id = [ *json.loads(resp.text).values() ][0]
                
                self.logger.info_log('Check publish appliance %s status on tenant %s' % (deviceInfo['redundant_devicename'],tenant_name))
                if not self.check_task_status(task_id):
                    sys.exit(1)
        return True
    
    def check_task_status(self,task_id):
        '''
        Will only fetch one task . Make sure the method is called immediately after the task is created
        '''
        url = self.generate_url('/portalapi/v1/tasks/task/%s' % task_id)
        #url = self.generate_url('/portalapi/v1/tasks/summary?nextWindowNumber=0&windowSize=10&deep=true')
        while True:
            resp = self.api_call(method='GET',url=url,data='')
            if not resp:
                self.logger.error_log('Failed to fetch task data')
                sys.exit(1)

            #task = JSONPath('$.data[?(@.uuid=="%s")]' % task_id).parse(json.loads(resp.text))[0]
            task = json.loads(resp.text)
            if task:
                if not task['percentageCompletion'] == 100:
                    self.logger.info_log('Task in progress.')
                    time.sleep(10)
                    continue
                else:
                    if task['status'] == 'SUCCESS':
                        self.logger.info_log('Task successfull.')
                        break
                    else:
                        self.logger.error_log('Task Failed')
                        return False
            else:
                self.logger.error_log('Failed to fetch task data')
                return False
        return True


    def check_address(self,
            country, 
            zipcode,
            street='',
            city='',
            state=''):
        url = 'https://maps.googleapis.com/maps/api/geocode/json?=&channel=director&key=AIzaSyClGMMbtFFOWlXD3AdcVZq4oE4kjknY9Gc&address='
        if street:
            url = url + street + ','
        if city:
            url = url + city + ','
        if state:
            url = url + state + ','
        url = url + country + ',' + zipcode
        headers = {'Content-Type': 'application/json','Accept': 'application/json'}
        response = requests.request("GET", url, headers=headers, data='', verify=False)
        if not isinstance(json.loads(response.text)['results'],list):
            self.logger.error_log('Failed to fetch latitude longitude info for the location : {street} , {city} , {state}, {country}, {zipcode}. Please check the address'.format(street=street, city=city, state=state, country=country,zipcode=zipcode))
            sys.exit(1)
        elif not json.loads(response.text)['results']:
            self.logger.error_log('Failed to fetch latitude longitude info for the location : {street} , {city} , {state}, {country}, {zipcode}. Please check the address'.format(street=street, city=city, state=state, country=country,zipcode=zipcode))
            sys.exit(1)
        return True

    def create_tenant(self,payload):
        url = self.generate_url('/portalapi/v1/tenants/tenant/deploy')
        resp = self.api_call(method='POST',url=url,data=payload)
        if not resp:
            self.logger.error_log('Failed to create tenant')
            sys.exit(1)
        task_id = [ *json.loads(resp.text).values() ][0]
        
        self.logger.console_log('Waiting 1 minute before checking tenant publish status...')
        self.logger.info_log('Adding 1 minute delay before checking publish status')
        time.sleep(60)  # Wait 1 minute (60 seconds)
        
        self.logger.info_log('Check publish for tenant')
        if not self.check_task_status(task_id):
            sys.exit(1)
        
        self.logger.info_log('Successfully published tenant')
        return True

if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument('-ip',
                        help='ecp_ip',default='10.73.70.70')
    parser.add_argument('-user',
                        help='user',default='Script1')
    parser.add_argument('-password',
                        help='password',default='scr1@Versa123')
    parser.add_argument('-payload',
                        help='JSON payload file for tenant creation',
                        default='TenantTemplate-Oct2025.json')
    parser.add_argument('--action',
                        help='Action to perform: fetch_uuid or create_tenant',
                        choices=['fetch_uuid', 'create_tenant'],
                        default='create_tenant')
    parser.add_argument('--global-id',
                        help='Global ID for tenant creation (overrides JSON file value)',
                        type=int,
                        default=49)
    parser.add_argument('--tenant-name',
                        help='Tenant name (overrides JSON file value)',
                        type=str,
                        default=None)
    parser.add_argument('--description',
                        help='Tenant description (overrides JSON file value)',
                        type=str,
                        default="Tenant Created by REST API Script")
    parser.add_argument('--bandwidth',
                        help='SASE bandwidth value (overrides JSON file value)',
                        type=int,
                        default=1000)
    parser.add_argument('--max-tunnels',
                        help='Maximum tunnels (overrides JSON file value)',
                        type=str,
                        default="5")
    parser.add_argument('--license-year',
                        help='License year (overrides JSON file value)',
                        type=str,
                        default="2019")
    parser.add_argument('--sdwan-enabled',
                        help='Enable SDWAN functionality (default: True)',
                        action='store_true',
                        default=True)
    parser.add_argument('--no-sdwan-enabled',
                        help='Disable SDWAN functionality',
                        action='store_true',
                        default=False)
    parser.add_argument('--sase-enabled',
                        help='Enable SASE functionality (default: True)',
                        action='store_true', 
                        default=True)
    parser.add_argument('--no-sase-enabled',
                        help='Disable SASE functionality',
                        action='store_true',
                        default=False)
    parser.add_argument('--use-static-json',
                        help='Use static JSON file instead of template processing',
                        action='store_true')
    args = parser.parse_args()
    
    # Set default tenant name dynamically based on global-id if not provided
    if args.tenant_name is None:
        args.tenant_name = f"Script-Tenant-{args.global_id}"
    
    # Set default description dynamically based on tenant name if not provided
    if args.description is None:
        args.description = f"{args.tenant_name} description"
    
    # Handle boolean logic for enable/disable flags
    sdwan_enabled = args.sdwan_enabled and not args.no_sdwan_enabled
    sase_enabled = args.sase_enabled and not args.no_sase_enabled
    
    ip = args.ip
    user = args.user
    password = args.password
    payload_file = args.payload
    action = args.action
    
    restHdl = RestApi(ip, user, password)

    if action == 'fetch_uuid':
        # Existing functionality - fetch tenant UUID
        tenant_uuid = restHdl.fetch_tenant_uuid('CNN1001')
        restHdl.logger.console_log(f"Tenant UUID: {tenant_uuid}")
    
    elif action == 'create_tenant':
        # New functionality - create tenant from JSON payload
        try:
            if args.use_static_json:
                # Read static JSON payload file directly (legacy mode)
                with open(payload_file, 'r') as f:
                    tenant_payload = json.load(f)
                restHdl.logger.console_log(f'Using static JSON file: {payload_file}')
                restHdl.logger.info_log(f'Using static JSON file: {payload_file}')
                restHdl.logger.payload_log('STATIC JSON PAYLOAD', json.dumps(tenant_payload, indent=4))
            else:
                # Default: Process template file with variable substitution
                with open(payload_file, 'r') as f:
                    template_content = f.read()
                
                # Define template variables with defaults (using command args or defaults)
                template_vars = {
                    'TENANT_NAME': args.tenant_name,
                    'DESCRIPTION': args.description,
                    'BANDWIDTH_VALUE': args.bandwidth,
                    'GLOBAL_ID': args.global_id,
                    'LICENSE_YEAR': args.license_year,
                    'MAX_TUNNELS': args.max_tunnels,
                    'SDWAN_ENABLED': str(sdwan_enabled).lower(),
                    'SASE_ENABLED': str(sase_enabled).lower()
                }
                
                # Replace template variables
                for var_name, var_value in template_vars.items():
                    placeholder = f'{{{{{var_name}}}}}'
                    template_content = template_content.replace(placeholder, str(var_value))
                
                # Console log (short info)
                restHdl.logger.console_log(f'Template processing - Variables: {list(template_vars.keys())}')
                
                # File log (detailed info)
                restHdl.logger.info_log(f'Template processing mode - Variables applied: {template_vars}')
                
                # Parse the processed template as JSON
                tenant_payload = json.loads(template_content)
                
                # Log the final payload to file only (not console)
                restHdl.logger.payload_log('FINAL TENANT PAYLOAD', json.dumps(tenant_payload, indent=4))
            
            # Template mode handles all parameters via variable substitution
            # No additional overrides needed since template variables are already applied
            
            restHdl.logger.console_log(f'Creating tenant: {tenant_payload.get("name", "Unknown")} (Global ID: {tenant_payload.get("globalId", "Not set")})')
            restHdl.logger.info_log(f'Creating tenant from template: {payload_file}')
            restHdl.logger.info_log(f'Tenant name: {tenant_payload.get("name", "Unknown")}')
            restHdl.logger.info_log(f'Global ID: {tenant_payload.get("globalId", "Not set")}')
            
            # Convert dict to JSON string for the API call
            payload_json = json.dumps(tenant_payload, indent=2)
            
            # Create the tenant
            result = restHdl.create_tenant(payload_json)
            
            if result:
                restHdl.logger.console_log(f"✓ Successfully created tenant: {tenant_payload.get('name', 'Unknown')}")
            else:
                restHdl.logger.console_log("✗ Failed to create tenant", "ERROR")
                
        except FileNotFoundError:
            restHdl.logger.console_log(f"Error: Payload file '{payload_file}' not found", "ERROR")
            sys.exit(1)
        except json.JSONDecodeError as e:
            restHdl.logger.console_log(f"Error: Invalid JSON in payload file '{payload_file}': {e}", "ERROR")
            sys.exit(1)
        except Exception as e:
            restHdl.logger.console_log(f"Error creating tenant: {e}", "ERROR")
            sys.exit(1)
