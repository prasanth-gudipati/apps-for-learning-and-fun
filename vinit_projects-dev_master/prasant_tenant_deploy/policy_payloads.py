#!/usr/bin/python3

federated_transaction = '''
{
        "entityFederatedPath": "{{ federated_path }}"
}
'''

device_policy_graph = '''
        "entity": {
                "uuid": "{{ device_policy_uuid }}",
                "name": "{{ policy_name }}",
                "type": "POLICY",
                "category": "INTERFACE",
                "subtype": "DEVICE",
                "tags": [],
                "children": []
        },
        "permissionGraph": "{\\"permissionsGraph\\":{\\"permissionDefinitions\\":[{\\"r\\":false,\\"w\\":false,\\"p\\":false,\\"id\\":1},{\\"r\\":false,\\"w\\":false,\\"p\\":true,\\"id\\":2},{\\"r\\":true,\\"w\\":false,\\"p\\":false,\\"id\\":3},{\\"r\\":true,\\"w\\":false,\\"p\\":true,\\"id\\":4},{\\"r\\":true,\\"w\\":true,\\"p\\":false,\\"id\\":5},{\\"r\\":true,\\"w\\":true,\\"p\\":true,\\"id\\":6}],\\"permissionsGraph\\":[{\\"id\\":1,\\"parentId\\":null,\\"uuid\\":\\"{{ device_policy_uuid }}\\",\\"parameterReferenceId\\":null,\\"nodeType\\":\\"ENTITY\\",\\"entityPermissions\\":[]}]}}",
        "parameterGraph": "",
        "parentReference": {
                "uuid": "{{ parent_reference_uuid }}",
                "name": "Interface",
                "type": "FOLDER",
                "subtype": null,
                "category": null,
                "version": "V1",
                "originId": null,
                "nodeLabel": "Interface",
                "federatedPath": "ConfigurationLifecycleGraph/PROFILE_ELEMENTS/Policies/Device Policies/Interface//"
        }
}
'''

interface_attach = '''
{
        "federatedPaths": ["ConfigurationLifecycleGraph/PROFILE_ELEMENTS/Policy Elements/Device/Interface//WAN1-1", "ConfigurationLifecycleGraph/PROFILE_ELEMENTS/Policy Elements/Device/Interface//LAN1-1"],
        "target": "ConfigurationLifecycleGraph/PROFILE_ELEMENTS/Policies/Device Policies/Interface//Interface_Policy-0/",
        "sourceCategory": "INTERFACE",
        "targetCategory": "INTERFACE"
}
'''
