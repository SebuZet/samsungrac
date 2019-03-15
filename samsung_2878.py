from .connection import (register_connection, Connection)
from .yaml_const import (CONFIG_DEVICE_CONNECTION_PARAMS, CONFIG_DEVICE_CONECTION_TEMPLATE)
from .properties import (register_status_getter, DeviceProperty)
from socket import * 
import json
import logging
import sys
import ssl
import traceback
import re

CONNECTION_TYPE_S2878 = 'samsung_2878'

CONF_PORT = 'port'
CONF_HOST = 'host'
CONF_TOKEN = 'token'
CONF_CERT = 'cert'
CONF_DUID = 'duid'
CONF_MAC = 'mac'
CONST_STATUS_OK_STR = 'Status="Okay"'

xml_test = '<?xml version="1.0" encoding="utf-8" ?><Response Type="DeviceState" Status="Okay"><DeviceState><Device DUID="XXXXXXX" GroupID="AC" ModelID="AC" ><Attr ID="AC_FUN_ENABLE" Type="RW" Value="Enable"/><Attr ID="AC_FUN_TEMPNOW" Type="R" Value="79"/><Attr ID="AC_FUN_TEMPSET" Type="RW" Value="24"/><Attr ID="AC_FUN_POWER" Type="RW" Value="On"/><Attr ID="AC_FUN_OPMODE" Type="RW" Value="Cool"/><Attr ID="AC_FUN_WINDLEVEL" Type="RW" Value="Auto"/><Attr ID="AC_FUN_ERROR" Type="R" Value="30303030"/><Attr ID="AC_ADD_STARTWPS" Type="RW" Value="0"/><Attr ID="AC_ADD_APMODE_END" Type="W" Value="0"/></Device></DeviceState></Response>'

class connection_config():
    def __init__(self, h, p, t, c):
        self.host = h
        self.port = p
        self.token = t
        self.duid = None
        self.cert = None

@register_connection
class ConnectionSamsung2878(Connection):
    def __init__(self, logger):
        super(ConnectionSamsung2878, self).__init__(logger)
        self._params = {}
        self._cfg = connection_config(None, None, None, None)
        self._connection_init_template = None
        
    def load_from_yaml(self, node, connection_base):
        from jinja2 import Template
        self._params = {} if connection_base is None else connection_base._params.copy()
        if node is not None:
            params_node = node.get(CONFIG_DEVICE_CONNECTION_PARAMS, {})
            if CONFIG_DEVICE_CONECTION_TEMPLATE in params_node:
                self._connection_init_template = Template(params_node[CONFIG_DEVICE_CONECTION_TEMPLATE])
            elif connection_base is None:
                print ("ERROR: missing 'connection_template' parameter in connection section")
                return False
            if connection_base is None:
                self._cfg.port = params_node.get(CONF_PORT, 2878)
                if CONF_HOST in params_node:
                    self._cfg.host = params_node[CONF_HOST]
                else:
                    print ("ERROR: missing 'host' parameter in connection section")
                    return False
                if CONF_TOKEN in params_node:
                    self._cfg.token = params_node[CONF_TOKEN]
                    self._params[CONF_TOKEN] = self._cfg.token
                else:
                    print ("ERROR: missing 'token' parameter in connection section")
                    return False
                self._cfg.duid = params_node.get(CONF_DUID, None)
                if self._cfg.duid == None:
                    mac = params_node.get(CONF_MAC, None)
                    if mac != None:
                        self._cfg.duid = re.sub(':', '', mac)
                if self._cfg.duid == None:
                    print ("ERROR: Nor 'duid' or 'mac' parameter found in connection section")
                    return False
                if CONF_CERT in params_node:
                    self._cfg.cert = params_node[CONF_CERT]
                else:
                    print ("ERROR: missing 'cert' parameter in connection section")
                    return False
                self.logger.info("Configuration, host: {}".format(self._cfg.host))
                self.logger.info("Configuration, port: {}".format(self._cfg.port))
                self.logger.info("Configuration, token: {}".format(self._cfg.token))
                self.logger.info("Configuration, duid: {}".format(self._cfg.duid))
            self._params.update(node.get(CONFIG_DEVICE_CONNECTION_PARAMS, {}))    
            return True
        return False

    @staticmethod
    def match_type(type):
        return type == CONNECTION_TYPE_S2878

    def create_updated(self, node):
        c = ConnectionSamsung2878(self.logger)
        c._cfg = self._cfg
        c._connection_init_template = self._connection_init_template
        c.load_from_yaml(node, self)
        return c

    def create_socket(self, init_message):
        sslSocket = None
        cfg = self._cfg
        try:
            self.logger.info("Creating ssl context")
            sslContext = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
            self.logger.info("Setting up verify mode")
            sslContext.verify_mode = ssl.CERT_REQUIRED
            self.logger.info("Setting up verify location: {}".format(cfg.cert))
            sslContext.load_verify_locations(cafile = cfg.cert)
            self.logger.info("Setting up ciphers")
            sslContext.set_ciphers("HIGH:!DH:!aNULL")
            self.logger.info("Setting up load cert chain: {}".format(cfg.cert))
            sslContext.load_cert_chain(cfg.cert)
            self.logger.info("Wrapping socket")
            sslSocket = sslContext.wrap_socket(socket(AF_INET, SOCK_STREAM), server_hostname = cfg.host)
            if sslSocket is not None:
                self.logger.info("Connecting with {}:{}".format(cfg.host, cfg.port))
                sslSocket.connect((cfg.host, cfg.port))
                sslSocket.recv(1024) # DRC-1.00
                sslSocket.recv(1024) # <?xml version="1.0" encoding="utf-8" ?><Update Type="InvalidateAccount"/>
                sslSocket.sendall(init_message.encode('utf-8'))
                reply = sslSocket.recv(4096)
                if reply is not None:
                    reply_str = reply.decode("utf-8")
                    if reply_str.find(CONST_STATUS_OK_STR) != -1:
                        return sslSocket
            else:
                self.logger.info("Wrapping socket FAILED")

        except:
            self.logger.error('Error creating socket')
            if sslSocket is not None:
                sslSocket.close()
        return None

    def execute(self, template, v):
        params = self._params
        params.update({ 'value' : v, 'duid' : self._cfg.duid })
        init_message = ''
        if self._connection_init_template is not None:
            init_message = self._connection_init_template.render(**params) + '\n'

        message = v
        if template is not None:
            message = template.render(**params) + '\n'

        xml_response = None
        self.logger.info(init_message)
        self.logger.info(message)
        sslSocket = self.create_socket(init_message)
        if sslSocket is not None:
            try:
                sslSocket.sendall(message.encode('utf-8'))
                xml_response = sslSocket.recv(4096).decode("utf-8")
                sslSocket.close()
                return xml_response

            except:
                self.logger.error('Socket error')
                if sslSocket is not None:
                    sslSocket.close()

            finally:
                if sslSocket is not None:
                    sslSocket.close()
        
        return xml_response

@register_status_getter
class GetSamsung2878Status(DeviceProperty):
    def __init__(self, name, connection):
        super(GetSamsung2878Status, self).__init__(name, connection)
        self._json_status = None
        self._xml_status = None
        self._attrs = {}

    @staticmethod
    def match_type(type):
        return type == CONNECTION_TYPE_S2878

    def update_state(self, device_state, debug):
        from collections import OrderedDict
        from xml.etree.ElementTree import fromstring
        import xmljson

        self._attrs = {}
        conn = self.get_connection(None)
        device_state = conn.execute(self._connection_template, None)
        self._xml_status = device_state
        self._attrs['state_xml'] = self._xml_status

        if self._xml_status is not None:
            # convert xml to json
            try:
                conv = xmljson.Abdera(dict_type=OrderedDict)
                device_state = conv.data(fromstring(self._xml_status))
            except:
                conn.logger.error("Error while converting XML to JSON")
                device_state = {}

        self._json_status = device_state
        self._value = self._json_status
        self._attrs['state_json'] = json.dumps(self._json_status)
        if self.status_template is not None and self._json_status is not None:
            try:
                v = self.status_template.render(device_state=self._json_status)
                v = v.replace("'", '"')
                v = v.replace("True", '"True"')
                self._value = json.loads(v)
            except:
                self._value = self._json_status
        self._attrs['device_state'] = self.value
        self._attrs['duid'] = conn._cfg.duid
        return self.value

    @property
    def state_attributes(self):
        """Return dictionary with property attributes."""
        return self._attrs
