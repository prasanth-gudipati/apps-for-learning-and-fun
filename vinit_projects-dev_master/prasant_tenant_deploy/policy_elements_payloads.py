#!/usr/bin/python3

static_wan = '''
{
        "entity": {
                "uuid": "{{ elt_uuid }}",
                "name": "{{ name }}",
                "type": "POLICY_ELEMENTS",
                "subtype": "DEVICE",
                "category": "INTERFACE",
                "tags": [],
                "attributes": {
                        "category": {
                                "value": "WAN"
                        },
                        "isVirtual": {
                                "value": "false"
                        },
                        "isEnabled": {
                                "value": true
                        },
                        "wan": {
                                "value": {
                                        "blockIcmp": false,
                                        "subCategory": {
                                                "value": "WIRED"
                                        },
                                        "connection": {
                                                "value": {
                                                        "address": {
                                                                "value": {
                                                                        "type": {
                                                                                "value": "STATIC"
                                                                        },
                                                                        "ip": {
                                                                                "value": "",
                                                                                "uuid": "{{ intf_ip_uuid }}"
                                                                        },
                                                                        "nexthop": {
                                                                                "value": "",
                                                                                "uuid": "{{ intf_next_hp_uuid }}"
                                                                        }
                                                                }
                                                        },
                                                        "monitor": {
                                                                "value": {
                                                                        "isEnable": true,
                                                                        "type": {
                                                                                "value": "GATEWAY"
                                                                        }
                                                                }
                                                        },
                                                        "type": {
                                                                "value": "BROADBAND"
                                                        },
                                                        "name": {
                                                                "value": "{{ name }}"
                                                        }
                                                }
                                        },
                                        "link": {
                                                "value": {
                                                        "speed": {
                                                                "value": "AUTO"
                                                        },
                                                        "mode": {
                                                                "value": "AUTO_DUPLEX"
                                                        }
                                                }
                                        },
                                        "location": {
                                                "value": "{{ location }}"
                                        }
                                }
                        }
                }
        },
        "permissionGraph": "{\\"permissionsGraph\\":{\\"permissionDefinitions\\":[{\\"r\\":false,\\"w\\":false,\\"p\\":false,\\"id\\":1},{\\"r\\":false,\\"w\\":false,\\"p\\":true,\\"id\\":2},{\\"r\\":true,\\"w\\":false,\\"p\\":false,\\"id\\":3},{\\"r\\":true,\\"w\\":false,\\"p\\":true,\\"id\\":4},{\\"r\\":true,\\"w\\":true,\\"p\\":false,\\"id\\":5},{\\"r\\":true,\\"w\\":true,\\"p\\":true,\\"id\\":6}],\\"permissionsGraph\\":[{\\"id\\":1,\\"parentId\\":null,\\"uuid\\":\\"{{ elt_uuid }}\\",\\"parameterReferenceId\\":null,\\"nodeType\\":\\"ENTITY\\",\\"entityPermissions\\":[]}]}}",
        "parameterGraph": "{\\"parameterGraph\\":{\\"parameterDefinitions\\":{\\"variables\\":[{\\"id\\":1,\\"name\\":\\"IP_{{ name }}\\",\\"type\\":\\"INTF_ADDRESS\\",\\"value\\":\\"\\"},{\\"id\\":2,\\"name\\":\\"{{ name }}_Next_Hop\\",\\"type\\":\\"IP_ADDRESS\\",\\"value\\":\\"\\"}],\\"references\\":[]},\\"parameterReferenceGraph\\":[{\\"id\\":1,\\"parentId\\":null,\\"uuid\\":\\"{{ elt_uuid }}\\",\\"parameterReferenceId\\":null,\\"nodeType\\":\\"ENTITY\\"},{\\"_comment\\":\\"leaf\\",\\"id\\":2,\\"parentId\\":1,\\"uuid\\":\\"{{ intf_ip_uuid }}\\",\\"parameterReferenceId\\":1,\\"nodeType\\":\\"VARIABLE\\"},{\\"_comment\\":\\"leaf\\",\\"id\\":3,\\"parentId\\":1,\\"uuid\\":\\"{{ intf_next_hp_uuid }}\\",\\"parameterReferenceId\\":2,\\"nodeType\\":\\"VARIABLE\\"}]}}",
        "parentReference": {
                "uuid": "{{ parent_reference_uuid }}",
                "name": "Interface",
                "type": "FOLDER",
                "subtype": null,
                "category": null,
                "version": "V1",
                "originId": null,
                "nodeLabel": "Interface",
                "federatedPath": "ConfigurationLifecycleGraph/PROFILE_ELEMENTS/Policy Elements/Device/Interface//"
        }
}
''' 

static_lan = '''
{
        "entity": {
                "uuid": "{{ elt_uuid }}",
                "name": "{{ name }}",
                "type": "POLICY_ELEMENTS",
                "subtype": "DEVICE",
                "category": "INTERFACE",
                "tags": [],
                "attributes": {
                        "category": {
                                "value": "LAN"
                        },
                        "isVirtual": {
                                "value": "false"
                        },
                        "isEnabled": {
                                "value": true
                        },
                        "lan": {
                                "value": {
                                        "subCategory": {
                                                "value": "WIRED"
                                        },
                                        "vpnMembership": {
                                                "value": {
                                                        "address": {
                                                                "value": {
                                                                        "type": {
                                                                                "value": "STATIC"
                                                                        },
                                                                        "dhcpRelay": {
                                                                                "value": {
                                                                                        "isEnable": false
                                                                                }
                                                                        },
                                                                        "ip": {
                                                                                "value": "",
                                                                                "uuid": "{{ lan_ip_uuid }}"
                                                                        }
                                                                }
                                                        },
                                                        "isGuestVPN": false,
                                                        "vpn": {
                                                                "value": {
                                                                        "name": "{{ tenant_name }}-Enterprise"
                                                                }
                                                        }
                                                }
                                        },
                                        "link": {
                                                "value": {
                                                        "speed": {
                                                                "value": "AUTO"
                                                        },
                                                        "mode": {
                                                                "value": "AUTO_DUPLEX"
                                                        }
                                                }
                                        },
                                        "location": {
                                                "value": "{{ location }}"
                                        }
                                }
                        }
                }
        },
        "permissionGraph": "{\\"permissionsGraph\\":{\\"permissionDefinitions\\":[{\\"r\\":false,\\"w\\":false,\\"p\\":false,\\"id\\":1},{\\"r\\":false,\\"w\\":false,\\"p\\":true,\\"id\\":2},{\\"r\\":true,\\"w\\":false,\\"p\\":false,\\"id\\":3},{\\"r\\":true,\\"w\\":false,\\"p\\":true,\\"id\\":4},{\\"r\\":true,\\"w\\":true,\\"p\\":false,\\"id\\":5},{\\"r\\":true,\\"w\\":true,\\"p\\":true,\\"id\\":6}],\\"permissionsGraph\\":[{\\"id\\":1,\\"parentId\\":null,\\"uuid\\":\\"{{ elt_uuid }}\\",\\"parameterReferenceId\\":null,\\"nodeType\\":\\"ENTITY\\",\\"entityPermissions\\":[]}]}}",
        "parameterGraph": "{\\"parameterGraph\\":{\\"parameterDefinitions\\":{\\"variables\\":[{\\"id\\":1,\\"name\\":\\"{{ name }}_IP\\",\\"type\\":\\"INTF_ADDRESS\\",\\"value\\":\\"\\"}],\\"references\\":[]},\\"parameterReferenceGraph\\":[{\\"id\\":1,\\"parentId\\":null,\\"uuid\\":\\"{{ elt_uuid }}\\",\\"parameterReferenceId\\":null,\\"nodeType\\":\\"ENTITY\\"},{\\"_comment\\":\\"leaf\\",\\"id\\":2,\\"parentId\\":1,\\"uuid\\":\\"{{ lan_ip_uuid }}\\",\\"parameterReferenceId\\":1,\\"nodeType\\":\\"VARIABLE\\"}]}}",
        "parentReference": {
                "uuid": "{{ parent_reference_uuid }}",
                "name": "Interface",
                "type": "FOLDER",
                "subtype": null,
                "category": null,
                "version": "V1",
                "originId": null,
                "nodeLabel": "Interface",
                "federatedPath": "ConfigurationLifecycleGraph/PROFILE_ELEMENTS/Policy Elements/Device/Interface//"
        }
}
'''
