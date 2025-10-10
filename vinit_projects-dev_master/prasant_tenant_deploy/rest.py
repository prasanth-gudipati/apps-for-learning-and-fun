#!/usr/bin/python3

import requests
import time
from jsonpath import JSONPath
import re
import argparse
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
    
    def api_call(self,method,url,data):
        '''
        Helper to execute api's
        '''
        self.logger.info_log('Executing Api : %s' % url)
        self.logger.info_log('Api Method : %s' % method)
        self.logger.info_log('Api Header : %s' % json.dumps(self.headers,indent=4))
        try:
            data_dict = json.loads(data)
            self.logger.info_log('Api data : %s' % json.dumps(data_dict,indent=4))
        except Exception:
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
        
        self.logger.info_log('Check publish for tenant')
        if not self.check_task_status(task_id):
            sys.exit(1)
        
        self.logger.info_log('Successfully published tenant')
        return True


if __name__ == '__main__':

    
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument('-ip',
                        help='ecp_ip')
    parser.add_argument('-user',
                        help='user')
    parser.add_argument('-password',
                        help='password')
    #parser.add_argument('-tenant',
    #                    help='tenant name')
    #parser.add_argument('-csv',
    #                    help='csv file path')
    args = parser.parse_args()
    ip = args.ip
    user = args.user
    password = args.password
    #tenant = args.tenant
    #csvfile = args.csv
    #csvHdl = CsvHandler(csvfile)
    restHdl = RestApi(ip,user,password)
    #tenant_summary = restHdl.fetch_tenant_summary(tenant)
    #tenantuuid = restHdl.fetch_tenant_uuid(name=tenant)
    #tenant_summary = restHdl.fetch_tenant_summary(tenant_name=tenant)
    #profile_element_perspective = restHdl.fetch_profile_elements_perspective(tenant_name=tenant,tenant_uuid=tenantuuid)
    #profile_perspective = restHdl.fetch_profile_perspective(tenant_name=tenant,tenant_uuid=tenantuuid)
    #site_perspective = restHdl.fetch_site_perspective(tenant_name=tenant,tenant_uuid=tenantuuid)
    #appliance_perspective = restHdl.fetch_appliance_perspective(tenant_name=tenant,tenant_uuid=tenantuuid)
    #region_summary = restHdl.fetch_regions(tenant_name=tenant,tenant_uuid=tenantuuid)
    #for elt in csvHdl.deviceinfo:
    #    restHdl.check_address(country=elt['country'],
    ##                    zipcode=elt['zipcode'],
    #                    street=elt['street'],
    #                    city=elt['city'],
    #                    state=elt['state'])

    payload = {
                "name": "{{tenant_name}}",
                "version": "1",
                "sdwanEnabled": True,
                "saseProductInfo": {
                    "usageType": "USER",
                    "bandwidthValue": 1000,
                    "saseProductTypeMode": "ALACARTE",
                    "alacarteList": [
                        {"alacarteType": "SECURE_WEB_GATEWAY", "flavour": "Essential"},
                        {"alacarteType": "VERSA_SECURE_ACCESS", "flavour": "Essential"},
                    ],
                    "disableDAI": False,
                    "swgValue": "2000",
                    "swgStartDate": "2023-10-05",
                    "swgEndDate": "2023-11-30",
                    "vsaValue": "1000",
                    "vsaStartDate": "2023-10-05",
                    "vsaEndDate": "2023-11-30",
                    "swgVsaValue": "500",
                    "swgVsaStartDate": "2023-10-05",
                    "swgVsaEndDate": "2023-11-30",
                    "webLogs": "ANALYTICS",
                    "dnsLogs": "ANALYTICS",
                    "cgnatLogs": "ANALYTICS",
                },
                "originalStatus": {
                    "status": True,
                    "roles": [
                        "a196b539-0ae2-42d2-955d-5d13c26f9694",
                        "b9d2bc89-2748-4031-895c-0f69d4d83ea4",
                        "29c18a35-053a-4924-8f4d-fff7dcaf3ab4",
                        "f78c5184-9514-4843-a655-f6868082a0e9",
                    ],
                },
                "parentTenantUUID": "8f475c01-e35c-4cca-b10f-bdbfbc5adf21",
                "directors": [
                    "50d7e170-503b-41cb-8dc7-02b9124c2132",
                    "b9d18e10-8f09-46d0-b7a1-431874bfc2c2",
                ],
                "status": True,
                "resources": [
                    "ConfigurationLifecycleGraph/PROFILE_ELEMENTS/Policy Elements/Device/Interface//Bridge-Interface-Underlay-v100-1",
                    "ConfigurationLifecycleGraph/PROFILE_ELEMENTS/Policy Elements/Device/Interface//CC-vni_0_4-1",
                    "ConfigurationLifecycleGraph/PROFILE_ELEMENTS/Policy Elements/Device/Interface//Internet1-ATT-AA-2",
                    "ConfigurationLifecycleGraph/PROFILE_ELEMENTS/Policy Elements/Device/Interface//Internet1-ATT-Static-1",
                    "ConfigurationLifecycleGraph/PROFILE_ELEMENTS/Policy Elements/Device/Interface//Internet1-ATT-1",
                    "ConfigurationLifecycleGraph/PROFILE_ELEMENTS/Policy Elements/Device/Interface//Internet2-VZ-1",
                    "ConfigurationLifecycleGraph/PROFILE_ELEMENTS/Policy Elements/Device/Interface//Lan-vni_0_3-100-1",
                    "ConfigurationLifecycleGraph/PROFILE_ELEMENTS/Policy Elements/Device/Interface//Lan-vni_0_3-101-1",
                    "ConfigurationLifecycleGraph/PROFILE_ELEMENTS/Policy Elements/Device/Interface//Lan-vni_0_3-102-1",
                    "ConfigurationLifecycleGraph/PROFILE_ELEMENTS/Policy Elements/Device/Interface//MPLS-ATT-1",
                    "ConfigurationLifecycleGraph/PROFILE_ELEMENTS/Policy Elements/Device/Interface//RealInternet-WAN4-1",
                    "ConfigurationLifecycleGraph/PROFILE_ELEMENTS/Policy Elements/Device/Interface//vni04-1",
                    "ConfigurationLifecycleGraph/PROFILE_ELEMENTS/Policy Elements/VPN Elements/VPN Instance//Hub-Enterprise-1",
                    "ConfigurationLifecycleGraph/PROFILE_ELEMENTS/Policy Elements/VPN Elements/VPN Instance//Hub-LAN1-1",
                    "ConfigurationLifecycleGraph/PROFILE_ELEMENTS/Policy Elements/VPN Elements/VPN Instance//Hub-LAN2-1",
                    "ConfigurationLifecycleGraph/PROFILE_ELEMENTS/Policy Elements/VPN Elements/VPN Instance//SPK-Enterprise-1",
                    "ConfigurationLifecycleGraph/PROFILE_ELEMENTS/Policy Elements/VPN Elements/VPN Instance//SPK-LAN1-1",
                    "ConfigurationLifecycleGraph/PROFILE_ELEMENTS/Policy Elements/VPN Elements/VPN Instance//SPK-LAN2-1",
                    "ConfigurationLifecycleGraph/PROFILE_ELEMENTS/Elements/Application/Forwarding Profile//FwdPro-001-1",
                    "ConfigurationLifecycleGraph/PROFILE_ELEMENTS/Elements/Monitor/Application Monitor//google-8.8.8.8-1",
                    "ConfigurationLifecycleGraph/PROFILE_ELEMENTS/Elements/VPN Name//LAN3-1",
                    "ConfigurationLifecycleGraph/PROFILE_ELEMENTS/Elements/VPN Name//LAN2-1",
                    "ConfigurationLifecycleGraph/PROFILE_ELEMENTS/Elements/VPN Name//LAN1-1",
                    "ConfigurationLifecycleGraph/PROFILE_ELEMENTS/Elements/VPN Name//provider-org-Enterprise-1",
                ],
                "controllers": [
                    "87ef7290-6003-4ac9-9d6e-5052ef885879",
                    "4b55559a-b6e8-43c0-baed-e9d3bd37f6c4",
                    "45463a11-e04f-478c-a5c9-e6cf81de6fa2",
                    "59e1f349-4b1e-4445-8dea-b9285db24500",
                ],
                "roles": [
                    "a196b539-0ae2-42d2-955d-5d13c26f9694",
                    "b9d2bc89-2748-4031-895c-0f69d4d83ea4",
                    "29c18a35-053a-4924-8f4d-fff7dcaf3ab4",
                    "f78c5184-9514-4843-a655-f6868082a0e9",
                ],
                "defaultDirector": "50d7e170-503b-41cb-8dc7-02b9124c2132",
                "authenticationType": "PSK",
                "ztpType": "SERIAL_NO",
                "saseEnabled": True,
                "mSPEnabled": False,
                "gatewayType": "SHARED",
                "regionInfos": [
                    {
                        "regionName": "US-EAST-200",
                        "regionUUID": "969974a8-3c4a-482a-94cc-32cb3de03dcc",
                        "selectedGateways": [
                            {
                                "saseGatewayUUID": "6d0b8f0a-8f01-4b61-b43a-f840cbbe8e9d",
                                "gatewayName": "saseGW14b-br4-tb278",
                                "tenantCount": 1,
                                "gatewayLabel": None,
                                "portalEnabled": True,
                                "tenantSaseGatewayVPNInfos": [
                                    {
                                        "vpnName": "{{tenant_name}}-LAN1",
                                        "tenantSaseGatewayVPNClientPoolInfos": [
                                            {
                                                "poolName": "lan1-pool1",
                                                "poolPrefix": "10.42.11.0/24",
                                            },
                                            {
                                                "poolName": "lan1-pool2",
                                                "poolPrefix": "10.42.12.0/24",
                                            },
                                        ],
                                    },
                                    {
                                        "vpnName": "{{tenant_name}}-LAN2",
                                        "tenantSaseGatewayVPNClientPoolInfos": [
                                            {
                                                "poolName": "lan2-pool1",
                                                "poolPrefix": "10.42.21.0/24",
                                            },
                                            {
                                                "poolName": "lan2-pool2",
                                                "poolPrefix": "10.42.22.0/24",
                                            },
                                        ],
                                    },
                                ],
                                "expanded": True,
                            }
                        ],
                        "selected": True,
                    },
                    {
                        "regionName": "US-WEST-100",
                        "regionUUID": "df93a294-fba5-44aa-8964-b7a5036cc8f4",
                        "selectedGateways": [
                            {
                                "saseGatewayUUID": "7f7284cf-0479-42c7-a166-9550b5ffad01",
                                "gatewayName": "saseGW4-br4-tb163",
                                "tenantCount": 1,
                                "gatewayLabel": None,
                                "portalEnabled": True,
                                "tenantSaseGatewayVPNInfos": [
                                    {
                                        "vpnName": "{{tenant_name}}-LAN1",
                                        "tenantSaseGatewayVPNClientPoolInfos": [
                                            {
                                                "poolName": "lan1-pool1",
                                                "poolPrefix": "10.41.11.0/24",
                                            },
                                            {
                                                "poolName": "lan1-pool2",
                                                "poolPrefix": "10.41.12.0/24",
                                            },
                                        ],
                                    },
                                    {
                                        "vpnName": "{{tenant_name}}-LAN2",
                                        "tenantSaseGatewayVPNClientPoolInfos": [
                                            {
                                                "poolName": "lan2-pool1",
                                                "poolPrefix": "10.41.21.0/24",
                                            },
                                            {
                                                "poolName": "lan2-pool2",
                                                "poolPrefix": "10.41.22.0/24",
                                            },
                                        ],
                                    },
                                ],
                                "expanded": True,
                            }
                        ],
                        "selected": True,
                    },
                ],
                "internetProtectionRulesMaximum": 500,
                "privateAppProtectionRulesMaximum": 50,
                "nameMappings": [
                    {
                        "parentMapping": "LAN3",
                        "childMapping": "{{tenant_name}}-LAN3",
                        "resourceKey": "VPN_NAME",
                        "isGuestVpn": False,
                    },
                    {
                        "parentMapping": "LAN2",
                        "childMapping": "{{tenant_name}}-LAN2",
                        "resourceKey": "VPN_NAME",
                        "isGuestVpn": False,
                    },
                    {
                        "parentMapping": "LAN1",
                        "childMapping": "{{tenant_name}}-LAN1",
                        "resourceKey": "VPN_NAME",
                        "isGuestVpn": False,
                    },
                    {
                        "parentMapping": "provider-org-Enterprise",
                        "childMapping": "{{tenant_name}}-Enterprise",
                        "resourceKey": "VPN_NAME",
                        "isGuestVpn": False,
                    },
                ],
                "solutionTiers": [
                    "Work-From-Home",
                    "Premier-Secure-SDWAN",
                    "Prime-Secure-SDWAN",
                    "Prime-SDWAN",
                    "Premier-Elite-SDWAN",
                ],
                "maxTunnels": "1000",
                "saseEnterpriseNames": ["{{tenant_name}}"],
                "formMode": "CREATE",
                "deploy": True,
            }
    
    template = Template(json.dumps(payload,indent=4))
    json_data = template.render(tenant_name='Demo3')
    restHdl.create_tenant(payload=json_data)
   
    #resp = restHdl.create_site(tenant_name=tenant,
    #        tenant_uuid=tenantuuid,
    #        tenant_summary=tenant_summary,
    #        site_perspective=site_perspective,
    #        site_name='test_site2',
    #        country='USA',
    #        zipcode='95002',
    #        street='6001 Great America Parkway',
    #        city='San Jose',
    #        state='CA')

    #deviceInfo = {'name':'testsite2app1',
    #            'serialnum':'testsite2app1',
    #            'bandwidth':'100',
    #            'vpn_profile':'WAN1-SDWAN-Controller1-StagingIpsec',
    #            'stagingController':'SDWAN-Controller1',
    #            'ztpemail':'vinit@test.com',
    #            'ztptype':'SERIAL_NO',
    #            'masterprofilename':'Master_Profile1',
    #            'masterprofileversion':'2',
    #            'masterprofiletype':'STANDARD',
    #            'parameters':{'IP_WAN1':'1.1.1.1/24',
    #                        'LAN1_IP':'2.2.2.2/24',
    #                        'WAN1_Next_Hop':'1.1.1.2'}
    #            }
 
    #restHdl.create_device(tenant_name=tenant,
    #                    tenant_uuid=tenantuuid,
    #                    tenant_summary=tenant_summary,
    #                    site_name='test_site2',
    #                    appliance_name='testsite2app1',
    #                    appliance_perspective=appliance_perspective,
    #                    deviceInfo=deviceInfo)
               
