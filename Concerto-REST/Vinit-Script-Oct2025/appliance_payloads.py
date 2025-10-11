#!/usr/bin/bash

site_create = '''
{
        "entity": {
                "name": "{{ name }}",
                "directorUuid": "{{ director_uuid }}",
                "regionUuid": "{{ region_uuid }}",
                "location": {
                        "streetAddress": "{{ street }}",
                        "city": "{{ city }}",
                        "state": "{{ state }}",
                        "country": "{{ country }}",
                        "zip": "{{ zipcode }}",
                        "latitude": "{{ latitude }}",
                        "longitude": "{{ longitude }}"
                }
                {% if site_uuid %}
                ,
                "uuid": "{{ site_uuid }}"
                {% endif %}
        },
        "permissionGraph": null,
        "parameterGraph": null,
        "parentReference": {
                "uuid": "{{ parent_reference_uuid }}",
                "name": "Site",
                "version": "V1",
                "type": "FOLDER",
                "subtype": null,
                "category": null,
                "originId": null
        }
}
'''

appliance_create = '''
{
        "entity": {
                "name": "{{ appliance_name }}",
                "siteUUID": "{{ site_uuid }}",
                "serial": "{{ serial_number }}",
                "hub": {{ isHub }},
                "hubPriority": null,
                "bandwidth": {{ bandwidth }},
                "vpnProfile": "{{ vpn_profile }}",
                "stagingController": "{{ stagingController }}",
                "ztpType": "{{ ztp_type }}",
                "solution_tier": null,
                "ztpEmail": "{{ ztp_email }}",
                "masterProfile": {
                        "uuid": "{{ master_profile_uuid }}",
                        "name": "{{ master_profile_name }}",
                        "version": "{{ master_profile_version }}",
                        "type": "MASTER_PROFILE",
                        "subtype": "{{ master_profile_type }}",
                        "category": null,
                        "modifyDate": null
                }
        },
        "permissionGraph": null,
        "parameterGraph": null,
        "parentReference": {
                "uuid": "{{ parent_reference_uuid }}",
                "name": "Appliance",
                "version": "V1",
                "type": "FOLDER",
                "subtype": null,
                "category": null,
                "originId": null
        }
}
'''
appliance_publish = '''
{
        "entity": {
                "federatedPaths": ["DeploymentLifecycleGraph/APPLIANCES/Appliance//{{ appliancename }}-1"]
        },
        "permissionGraph": null,
        "parameterGraph": null,
        "parentReference": {
                "uuid": "{{ parent_reference_uuid }}",
                "name": "Appliance",
                "version": "V1",
                "type": "FOLDER",
                "subtype": null,
                "category": null,
                "originId": null
        }
}
'''

appliance_update_master_profile = '''
{
    "applianceList": ["{{ appliance_uuid }}"],
        "federatedPathMasterProfile": "ConfigurationLifecycleGraph/PROFILES/Master Profiles/{{ masterprofiletype }}//{{ masterprofilename }}-{{ masterprofileversion }}"
}
'''
