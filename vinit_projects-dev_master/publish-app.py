#!/usr/bin/python3

import requests
requests.packages.urllib3.disable_warnings()
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
from datetime import datetime
import threading

class CsvHandler(object):
    def __init__(self,csvfile):
        self.csvlist = self.convert_csv_dict(csvfile)
        self.deviceinfo = self.fetch_device_info(self.csvlist)

    def convert_csv_dict(self,csvfile):
        '''
        Helper to convert csv to dict
        '''
        csvobject = open(csvfile)
        reader = csv.DictReader(csvobject)
        return [ line for line in reader ]

    def fetch_device_info(self,csvlist):
        '''
        Helper to fetch the device info in the required format
        '''
        deviceInfo = []
        for elt in csvlist:
            d1 = {'parameters':{}}
            for key in elt.keys():
                if 'parameter_' in key:
                    d1['parameters'][key.split('parameter_')[1]] = elt[key]
                else:
                    d1[key] = elt[key]
            deviceInfo.append(d1)
        return deviceInfo

        
class RestApi(object):
    def __init__(self,ecp_ip,user,password):
        self.lock = threading.Lock()
        self.ecp_ip = ecp_ip
        self.user = user
        self.password = password
        self.logger = log_handler.Logger()

        self.report = open('report_%s.csv' % datetime.now().strftime('%Y_%m_%d_%H_%M_%S'),'w')
        self.report.write("Device Name,Task UUID,Status,Summary,startTime,endTime,Duration-in-SEC\r\n")
        self.report.flush()
        #headers = {'Content-Type': 'application/json','Accept': 'application/json,application/xml'}
        #headers = {'Content-Type': 'application/json','Accept': 'application/json'}
        #headers = {'Accept': 'application/json'}
        self.headers = {}
        self.SESSION_COOKIE = None
        self.CSRF_TOKEN = None
        self.auth()

    def auth(self,thread='MAIN'):
        oauth_user = 'concerto'
        oauth_password = 'Concerto123@'
        url = "https://%s/portalapi/v1/auth/token" % self.ecp_ip
        headers = {'Content-Type': 'application/json','Accept': 'application/json'}
        
        payload = '{ \"client_id\": \"%s\", \"client_secret\": \"%s\", \"grant_type\": \"password\", \"password\": \"%s\", \"username\": \"%s\" }' % \
		(oauth_user, oauth_password, self.password, self.user)

        response = requests.request("POST", url, 
                headers=headers, 
                data=payload, 
                verify=False, 
                timeout=60)

        if int(int(response.status_code)/100) != 2:
            self.logger.error_log(thread,'Api Failed')
            self.logger.error_log(thread,'Api Response Status code: %s' % response.status_code)
            self.logger.error_log(thread,'Api Response Reason: %s' % response.reason)
            self.logger.error_log(thread,'Api Response Text: %s' % json.dumps(json.loads(response.text),indent=4))
            return sys.exit(1)

        token = response.json()['access_token']
        headers['Authorization'] =  "Bearer %s" % token
        self.headers = headers

    def api_call(self,method,url,data,thread='MAIN'):
        '''
        Helper to execute api's
        '''
        self.logger.info_log(thread,'Executing Api : %s' % url)
        self.logger.info_log(thread,'Api Method : %s' % method)
        self.logger.info_log(thread,'Api Header : %s' % json.dumps(self.headers,indent=4))
        try:
            data_dict = json.loads(data)
            self.logger.info_log(thread,'Api data : %s' % json.dumps(data_dict,indent=4))
        except Exception:
            self.logger.info_log(thread,'Api data : %s' % json.dumps(data,indent=4))
        #catch connection refused
        try:
            resp = requests.request(method, url, headers=self.headers, data=data,verify=False,cookies=self.SESSION_COOKIE, timeout=60)

            #self.SESSION_COOKIE = resp.cookies
            #self.CSRF_TOKEN = resp.cookies['ECP-CSRF-TOKEN']
            #self.headers['X-CSRF-TOKEN'] =  self.CSRF_TOKEN
            if int(int(resp.status_code)/100) != 2:
                #import pdb;pdb.set_trace()
                self.logger.error_log(thread,'Api Failed')
                self.logger.error_log(thread,'Api Response Status code: %s' % resp.status_code)
                self.logger.error_log(thread,'Api Response Reason: %s' % resp.reason)
                self.logger.error_log(thread,'Api Response Text: %s' % json.dumps(json.loads(resp.text),indent=4))
                #if "Access token doesn't exist for the session" in resp.text:
                if "Unauthorized" in resp.reason:
                    self.auth(thread)
                    resp_text = self.api_call(method,url,data,thread)
                elif int(int(resp.status_code)/100) == 5:
                    time.sleep(60)
                    resp_text = self.api_call(method,url,data,thread)
            else:
                self.logger.info_log(thread,'Api Succeeded')
                self.logger.info_log(thread,'Api Response Status code: %s' % resp.status_code)
                self.logger.info_log(thread,'Api Response Reason: %s' % resp.reason)
                self.logger.info_log(thread,'Api Response Text: %s' % json.dumps(json.loads(resp.text),indent=4))
                try:
                    if not resp:
                        self.logger.error_log(thread,'FAILED Api : %s' % url)
                        self.logger.error_log(thread,'Api Method : %s' % method)
                        self.logger.error_log(thread,'Api Header : %s' % json.dumps(self.headers,indent=4))
                        try:
                            data_dict = json.loads(data)
                            self.logger.error_log(thread,'Api data : %s' % json.dumps(data_dict,indent=4))
                        except Exception:
                            self.logger.error_log(thread,'Api data : %s' % json.dumps(data,indent=4))
                        self.logger.error_log(thread,'Api Response Status code: %s' % resp.status_code)
                        self.logger.error_log(thread,'Api Response Reason: %s' % resp.reason)
                        self.logger.error_log(thread,'Api Response Text: %s' % json.dumps(json.loads(resp.text),indent=4))
                except Exception as ex:
                    self.logger.error_log(thread,'FAILED API exception for %s : %s' % (url, ex))
                    self.auth(thread)
                    resp_text = self.api_call(method,url,data,thread)
                resp_text = resp.text
            resp.close()
            return resp_text
        except Exception as ex:
            self.logger.error_log(thread,'Exception caught while executing url %s : %s' % (url, ex))
            #if "read timeout" in ex:
            #    self.auth(thread)
            time.sleep(60)
            return self.api_call(method,url,data,thread)

    def generate_url(self,api):
        '''
        Helper to generate url from api
        '''
        return "https://%s%s" % (self.ecp_ip,api)

    def fetch_tenant_uuid(self,name,thread='MAIN'):
        self.logger.info_log(thread,'Fetching tenant %s uuid' % name)
        url = self.generate_url('/portalapi/v1/tenants/tenant/name/%s' % name)
        resp = self.api_call(method='GET',url=url,data='',thread=thread)
        if not resp:
            self.logger.error_log(thread,'Failed to fetch tenant %s uuid' % name)
            sys.exit(1)
        json_dict = json.loads(resp)
        #JSONPath_expr = JSONPath('$.tenantInfo.uuid').parse(resp)[0]
        #uuid = JSONPath_expr.find(json_dict)[0].value
        uuid  = JSONPath('$.tenantInfo.uuid').parse(json_dict)[0]
        return uuid

    def fetch_profile_perspective(self,tenant_name,tenant_uuid,thread='MAIN'):
        url = self.generate_url('/portalapi/v1/tenants/%s/configuration/perspective/profile' % tenantuuid)
        resp = self.api_call(method='GET',url=url,data='',thread=thread)
        if not resp:
            self.logger.error_log(thread,'Failed to fetch the profile perspective for tenant %s' % tenant_name)
            sys.exit(1)
        return json.loads(resp)


    def fetch_profile_elements_perspective(self,tenant_name,tenant_uuid,thread='MAIN'):
        url = self.generate_url('/portalapi/v1/tenants/%s/configuration/perspective/profile-elements' % tenantuuid)
        resp = self.api_call(method='GET',url=url,data='',thread=thread)
        if not resp:
            self.logger.error_log(thread,'Failed to fetch the profile element perspective for tenant %s' % tenant_name)
            sys.exit(1)
        return json.loads(resp)

    def fetch_site_perspective(self,tenant_name,tenant_uuid,thread='MAIN'):
        url = self.generate_url('/portalapi/v1/tenants/%s/deploy/perspective/site' % tenantuuid)
        resp = self.api_call(method='GET',url=url,data='',thread=thread)
        if not resp:
            self.logger.error_log(thread,'Failed to fetch the site perspective for tenant %s' % tenant_name)
            #sys.exit(1)
        return json.loads(resp)

    def fetch_appliance_perspective(self,tenant_name,tenant_uuid,thread='MAIN'):
        url = self.generate_url('/portalapi/v1/tenants/%s/deploy/perspective/appliance' % tenantuuid)
        resp = self.api_call(method='GET',url=url,data='',thread=thread)
        if not resp:
            self.logger.error_log(thread,'Failed to fetch the profile element perspective for tenant %s' % tenant_name)
            #sys.exit(1)
        return json.loads(resp)

    def fetch_tenant_summary(self,tenant_name,thread='MAIN'):
        url = self.generate_url('/portalapi/v1/tenants/tenant/name/%s' % tenant_name)
        resp = self.api_call(method='GET',url=url,data='',thread=thread)
        if not resp:
            self.logger.error_log(thread,'Failed to fetch the config summary for tenant %s' % tenant_name)
            sys.exit(1)
        return json.loads(resp)

    def fetch_site_summary(self,tenant_name,
            tenant_uuid,site_name,thread='MAIN'):
        url = self.generate_url('/portalapi/v1/tenants/%s/sites/getByName/%s' % (tenant_uuid,site_name))
        resp = self.api_call(method='GET',url=url,data='',thread=thread)
        if not resp:
            self.logger.error_log(thread,'Failed to fetch the site summary for tenant %s' % tenant_name)
            #sys.exit(1)
            return json.loads('{}')
        return json.loads(resp)

    def fetch_appliance_summary(self,tenant_name,
            tenant_uuid,
            tenant_summary,
            site_uuid,thread='MAIN'):
        url = self.generate_url('/portalapi/v1/tenants/%s/sites/%s/summarize' % (tenant_uuid,site_uuid))
        resp = self.api_call(method='GET',url=url,data='',thread=thread)
        if not resp:
            self.logger.error_log(thread,'Failed to fetch the site summary for tenant %s' % tenant_name)
            sys.exit(1)
        return json.loads(resp)

    def fetch_basic_mp_summary(self,tenant_name,
            tenant_uuid,masterprofilename,thread='MAIN'):
        url = self.generate_url('/portalapi/v1/tenants/%s/profiles/basic/summarize?nextWindowNumber=0&windowSize=100&stackVersionName=%s' % (tenant_uuid, masterprofilename))
        resp = self.api_call(method='GET',url=url,data='',thread=thread)
        if not resp:
            self.logger.error_log(thread,'Failed to fetch the basic master profile summary for tenant %s' % tenant_name)
            sys.exit(1)
        return json.loads(resp)

    def fetch_standard_mp_summary(self,tenant_name,
            tenant_uuid,masterprofilename,thread='MAIN'):
        url = self.generate_url('/portalapi/v1/tenants/%s/profiles/standard/summarize?nextWindowNumber=0&windowSize=10&stackVersionName=%s' % (tenant_uuid, masterprofilename))
        resp = self.api_call(method='GET',url=url,data='',thread=thread)
        if not resp:
            self.logger.error_log(thread,'Failed to fetch the standard master profile summary for tenant %s' % tenant_name)
            sys.exit(1)
        return json.loads(resp)
    
    def fetch_regions(self,tenant_name,tenant_uuid,thread='MAIN'):
        url = self.generate_url('/portalapi/v1/tenants/%s/regions/summary' % (tenant_uuid))
        resp = self.api_call(method='GET',url=url,data='',thread=thread)
        if not resp:
            self.logger.error_log(thread,'Failed to fetch the regions configured for tenant %s' % tenant_name)
            sys.exit(1)
        return json.loads(resp)

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
            region='',
            latitude='',
            longitude='',
            thread='MAIN'):
        site_uuid=None
        if not region:
            region = 'Default'

        region_uuid = JSONPath('$.data[?(@.name=="%s")].uuid' % region).parse(region_summary)[0]
        site_summary = self.fetch_site_summary(tenant_name,tenant_uuid,site_name,thread)
        result = 0
        try:
            result = JSONPath('$.entityRef.uuid').parse(site_summary)
        except:
            print ("*** NO SITE FOUND ***")
        if result:
            self.logger.info_log(thread,'Site %s exits' % site_name)
            site_uuid = result[0]
            method = 'PUT'
            self.logger.info_log(thread,'Updating Site %s on tenant %s' % (site_name,tenant_name))
            url_site = self.generate_url('/portalapi/v1/tenants/%s/sites/%s' % (tenant_uuid,site_uuid))
        else:
            method = 'POST'
            self.logger.info_log(thread,'Creating Site %s on tenant %s' % (site_name,tenant_name))
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
        FETCH_LAT_LONG = 0 
        if FETCH_LAT_LONG:
            url = 'https://maps.googleapis.com/maps/api/geocode/json?=&channel=director&key=AIzaSyClGMMbtFFOWlXD3AdcVZq4oE4kjknY9Gc&address='
            if street:
                url = url + street + ','
            if city:
                url = url + city + ','
            if state:
                url = url + state + ','
            url = url + country + ',' + zipcode
            headers = {'Content-Type': 'application/json','Accept': 'application/json'}
            response = requests.request("GET", url, headers=headers, data='', verify=False, timeout=60)
            if not isinstance(json.loads(response.text)['results'],list):
                self.logger.error_log(thread,'Failed to fetch latitude longitude info for the location : {street} , {city} , {state}, {country}, {zipcode}. Please check the address'.format(street=street, city=city, state=state, country=country,zipcode=zipcode))
                sys.exit(1)
            elif not json.loads(response.text)['results']:
                self.logger.error_log(thread,'Failed to fetch latitude longitude info for the location : {street} , {city} , {state}, {country}, {zipcode}. Please check the address'.format(street=street, city=city, state=state, country=country,zipcode=zipcode))
                sys.exit(1) 
            latitude = JSONPath('$..lat').parse(json.loads(response.text))[0]
            longitude = JSONPath('$..lng').parse(json.loads(response.text))[0]
        #latitude = '20.00'
        #longitude = '80.00'
        parent_reference_uuid=JSONPath('$.perspective[0].uuid').parse(site_perspective)[0]

        template = Template(appliance_payloads.site_create)
        data = template.render(name=site_name,director_uuid=directoruuid,street=street,city=city,state=state,country=country,zipcode=zipcode,latitude=latitude,longitude=longitude,parent_reference_uuid=parent_reference_uuid,site_uuid=site_uuid,region_uuid=region_uuid)
        resp = self.api_call(method=method,url=url_site,data=data)
        if not resp:
            self.logger.error_log(thread,'Failed to create the site %s for tenant %s' % (site_name,tenant_name))
            sys.exit(1)
        return json.loads(resp)

    def create_device(self,tenant_name,
            tenant_uuid,
            tenant_summary,
            site_name,
            appliance_name,
            appliance_perspective,
            deviceInfo,
            thread='MAIN'):
        self.logger.info_log(thread,'Publish Appliance %s on tenant %s' % (appliance_name,tenant_name))

        url = self.generate_url('/portalapi/v1/tenants/%s/appliances/publish' % tenant_uuid)
        parent_reference_uuid =  JSONPath('$.perspective[0].uuid').parse(appliance_perspective)[0]
        template = Template(appliance_payloads.appliance_publish)
        data = template.render(appliancename=appliance_name,parent_reference_uuid=parent_reference_uuid)
        resp = self.api_call(method='PUT',url=url,data=data,thread=thread)
        if not resp:
            self.logger.error_log(thread,'Failed to publish device %s for tenant %s' % (appliance_name,tenant_name))
            self.logger.error_log(thread,'SITE FAILED: DEVICE %s for tenant %s' % (appliance_name,tenant_name))
            #sys.exit(1) ; VS Continuing with next site
            self.write_msg_csv(appliance_name, 'null', 'FAILED', 'Failed to publish device %s for tenant %s' % (appliance_name,tenant_name),thread)
            return False
        task_id = list(json.loads(resp).values())[0]
        
        #self.logger.info_log(thread,'Check publish appliance %s status on tenant %s' % (appliance_name,tenant_name))
        #if self.check_task_status(task_id, appliance_name):
        #    return True
        #else:
        #    #sys.exit(1) ; VS Site create failed and yet continuing
        #    self.logger.info_log(thread,'FINAL: SITE / DEVICE FAILED FOR %s'%(appliance_name))
        #    return True
        return task_id

    def check_task_status(self,task_id_list,thread='MAIN'):
        '''
        Used to check the status of publish tasks
        '''
        task_completed_list = []
        #url = self.generate_url('/portalapi/v1/tasks/task/%s' % task_id)
        api = '/portalapi/v1/tasks/summary?nextWindowNumber=0&windowSize=100&deep=true'

        for task in task_id_list:
            api = api + "&uuids=%s" % task
        url = self.generate_url(api)
        
        resp = self.api_call(method='GET',url=url,data='',thread=thread)
        if not resp:
            return []

            #if int(int(resp.status_code)/100) != 2:
            #    self.logger.error_log(thread,'Failed to fetch task data')
                #sys.exit(1) ; VS -Director API Failed - continue
            #    return []
        #else:
        #    return []

        #task = JSONPath('$.data[?(@.uuid=="%s")]' % task_id).parse(json.loads(resp))[0]
        task_summary_list = json.loads(resp)
        for task_summary in task_summary_list['data']:
            if task_summary:
                #Calculate task runtime
                task_runtime = datetime.now().timestamp() - datetime.fromtimestamp(task_summary['createDate']/1000).timestamp()
                #task_runtime = datetime.now().timestamp() - datetime.fromtimestamp(task_summary['createDate'])
                #timeout task after 1 hr
                if task_runtime > 3600:
                    self.logger.info_log(thread,'Timing out task %s' % task)
                    task_completed_list.append(task_summary['uuid'])
                    self.write_msg_csv(task_summary['name'], task_summary['uuid'], "Script Timeout", "Script Timeout",thread)
                elif not task_summary['percentageCompletion'] == 100:
                    self.logger.info_log(thread,'Task in progress.')
                    continue
                else:
                    task_completed_list.append(task_summary['uuid'])
                    if task_summary['status'] == 'SUCCESS':
                        self.logger.info_log(thread,'Task successfull.')
                        self.logger.info_log(thread,'FINAL: SITE / DEVICE PUBLISHED FOR %s'%(task_summary['name']))
                        message = JSONPath('$.messages[?(@.finalMessage==True)]').parse(task_summary)[0]['description']
                        starttime = task_summary['createDate'] / 1000
                        endtime = task_summary['completionDate'] / 1000
                        task_duration_in_sec = str(round((endtime - starttime), 2))
                        starttime = datetime.fromtimestamp(starttime).strftime('%Y-%m-%d %H:%M:%S')
                        endtime = datetime.fromtimestamp(endtime).strftime('%Y-%m-%d %H:%M:%S')
                        self.write_msg_csv_new(task_summary['name'], task_summary['uuid'],
                                               task_summary['status'], task_summary['description'], thread,
                                               starttime, endtime, task_duration_in_sec)
                        ##self.write_msg_csv(task_summary['name'], task_summary['uuid'], task_summary['status'], message,thread)
                        break
                    else:
                        self.logger.error_log(thread,'Task Failed')
                        #Write to csv
                        message = JSONPath('$.messages[?(@.finalMessage==True)]').parse(task_summary)[0]['description']
                        #self.report.write("Device Name,Task UUID,Status,Summary\r\n")
                        self.write_msg_csv(task_summary['name'], task_summary['uuid'], task_summary['status'], message,thread)
            else:
                self.logger.error_log(thread,'Failed to fetch task data')
                return []
        return task_completed_list

    def get_latest_task_detals(self,thread='MAIN'):
        pdb.set_trace()
        api = '/portalapi/v1/tasks/summary?nextWindowNumber=0&windowSize=1&deep=true'
        url = self.generate_url(api)
        resp = self.api_call(method='GET',url=url,data='',thread=thread)
        task_json = json.loads(resp)
        starttime = task_json['data'][0]['createDate']/1000
        endtime =  task_json['data'][0]['completionDate']/1000
        task_duration_in_sec = str(round((endtime - starttime),2))
        starttime = datetime.fromtimestamp(starttime).strftime('%Y-%m-%d %H:%M:%S')
        endtime = datetime.fromtimestamp(endtime).strftime('%Y-%m-%d %H:%M:%S')
        self.write_msg_csv_new(task_json['data'][0]['name'], task_json['data'][0]['uuid'],task_json['data'][0]['status'], task_json['data'][0]['description'],starttime,endtime,task_duration_in_sec,thread)
        return task_json

    def write_msg_csv(self,appliance_name, task, status, message,thread):
        self.logger.info_log(thread,'Acquiring Write lock')
        self.lock.acquire()
        self.logger.info_log(thread,'Acquired Write lock, writing to report')
        self.report.write("%s,%s,%s,%s\r\n" % (appliance_name,task,status,message))
        self.report.flush()
        self.lock.release()
        self.logger.info_log(thread,'Releasing Write lock')

    def write_msg_csv_new(self, appliance_name, task, status, message, thread, starttime="DUMMY", endtime="DUMMY", duration="DUMMY"):
        self.logger.info_log(thread, 'Acquiring Write lock')
        self.lock.acquire()
        self.logger.info_log(thread, 'Acquired Write lock, writing to report')
        self.report.write(
            "%s,%s,%s,%s,%s,%s,%s\r\n" % (appliance_name, task, status, message, starttime, endtime, duration))
        self.report.flush()
        self.lock.release()
        self.logger.info_log(thread, 'Releasing Write lock')

    def check_address(self,
            country, 
            zipcode,
            street='',
            city='',
            state='',
            thread='MAIN'):
        url = 'https://maps.googleapis.com/maps/api/geocode/json?=&channel=director&key=AIzaSyClGMMbtFFOWlXD3AdcVZq4oE4kjknY9Gc&address='
        if street:
            url = url + street + ','
        if city:
            url = url + city + ','
        if state:
            url = url + state + ','
        url = url + country + ',' + zipcode
        headers = {'Content-Type': 'application/json','Accept': 'application/json'}
        response = requests.request("GET", url, headers=headers, data='', verify=False,timeout=60)
        if not isinstance(json.loads(response.text)['results'],list):
            self.logger.error_log(thread,'Failed to fetch latitude longitude info for the location : {street} , {city} , {state}, {country}, {zipcode}. Please check the address'.format(street=street, city=city, state=state, country=country,zipcode=zipcode))
            sys.exit(1)
        elif not json.loads(response.text)['results']:
            self.logger.error_log(thread,'Failed to fetch latitude longitude info for the location : {street} , {city} , {state}, {country}, {zipcode}. Please check the address'.format(street=street, city=city, state=state, country=country,zipcode=zipcode))
            sys.exit(1)
        return True

def deploy_device(device_info,restHdl,dca,thread='MAIN'):
    try:
        task_id_list = []
        for elt in device_info:
            task_id = restHdl.create_device(tenant_name=tenant,
                                tenant_uuid=tenantuuid,
                                tenant_summary=tenant_summary,
                                site_name=elt['site_name'],
                                appliance_name=elt['devicename'],
                                appliance_perspective=appliance_perspective,
                                deviceInfo=elt,
                                thread=thread)
            #time.sleep(10)
            if task_id:     
                task_id_list.append(task_id)
            #Set Bollean
            poll_task = True
            tasks_completed = []
            while poll_task:
                #Remove tasks from polling list
                for task in tasks_completed:
                    task_id_list.remove(task)

                if (len(task_id_list) >= max_publish) and ((device_info.index(elt) + 1) < len(device_info)):
                    poll_task = True
                elif (len(task_id_list) > 0) and (max_publish > (len(device_info) - ((device_info.index(elt) + 1)))) :
                    poll_task = True
                else:
                    poll_task = False
                print('%s : %s out of %s devices left to publish' % (thread, (len(device_info) - device_info.index(elt)),
                                                    len(device_info)))
                if poll_task:
                    #Check task status
                    tasks_completed = restHdl.check_task_status(task_id_list,thread=thread)
                    time.sleep(10)
    except Exception as ex:
        restHdl.logger.error_log(thread,'Exception caught during device deploy : %s' % ex)

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
    parser.add_argument('-csv',
                        help='csv file path')
    parser.add_argument('-max-publish',
                        help='maximum parallel publish tasks per dca',
                        default=10)
    args = parser.parse_args()
    ip = args.ip
    user = args.user
    password = args.password
    tenant = args.tenant
    csvfile = args.csv
    max_publish = int(args.max_publish)
    csvHdl = CsvHandler(csvfile)
    restHdl = RestApi(ip,user,password)
    try:
        tenant_summary = restHdl.fetch_tenant_summary(tenant)
        tenantuuid = restHdl.fetch_tenant_uuid(name=tenant)
        tenant_summary = restHdl.fetch_tenant_summary(tenant_name=tenant)
        site_perspective = restHdl.fetch_site_perspective(tenant_name=tenant,tenant_uuid=tenantuuid)
        appliance_perspective = restHdl.fetch_appliance_perspective(tenant_name=tenant,tenant_uuid=tenantuuid)
        
        unique_dca_set = set(JSONPath('$[*].director_cluster_name').parse(csvHdl.deviceinfo))
        unique_dca_list = [*unique_dca_set]
        device_info_dict = {}
        if unique_dca_list:
            for dca in unique_dca_list:
                device_info_dict[dca] = JSONPath('$[?(@.director_cluster_name=="%s")]' % dca).parse(csvHdl.deviceinfo)
        else:
            task_id_dict['default']
            device_info_dict['default'] = csvHdl.deviceinfo

        job_list = []
        for elt in device_info_dict:
            #import pdb;pdb.set_trace()
            #p = deploy_device(device_info_dict[elt],restHdl,elt,elt)
            p = threading.Thread(name=elt, target=deploy_device,args=(device_info_dict[elt],restHdl,elt,elt))
            job_list.append(p)

        for job in job_list:
            job.start()
        
        for job in job_list:
            job.join()

        restHdl.report.close()
    except Exception as ex:
        print("Exception caught : {ex}".format(ex))
        restHdl.report.close()
        sys.exit(1)
    sys.exit(0)
