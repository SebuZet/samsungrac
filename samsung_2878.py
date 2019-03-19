from .connection import (register_connection, Connection)
from .yaml_const import (CONFIG_DEVICE_CONNECTION_PARAMS, 
    CONFIG_DEVICE_CONECTION_TEMPLATE, CONF_CERT,
)
from homeassistant.const import (CONF_PORT, CONF_TOKEN, CONF_MAC, CONF_IP_ADDRESS)
from .properties import (register_status_getter, DeviceProperty)
from socket import * 
import json
import logging
import sys
import ssl
import traceback
import re
import os

CONNECTION_TYPE_S2878 = 'samsung_2878'

CONF_DUID = 'duid'
CONST_STATUS_OK_STR = 'Status="Okay"'

xml_test = '<?xml version="1.0" encoding="utf-8" ?><Response Type="DeviceState" Status="Okay"><DeviceState><Device DUID="XXXXXXX" GroupID="AC" ModelID="AC" ><Attr ID="AC_FUN_ENABLE" Type="RW" Value="Enable"/><Attr ID="AC_FUN_TEMPNOW" Type="R" Value="79"/><Attr ID="AC_FUN_TEMPSET" Type="RW" Value="24"/><Attr ID="AC_FUN_POWER" Type="RW" Value="On"/><Attr ID="AC_FUN_OPMODE" Type="RW" Value="Cool"/><Attr ID="AC_FUN_WINDLEVEL" Type="RW" Value="Auto"/><Attr ID="AC_FUN_ERROR" Type="R" Value="30303030"/><Attr ID="AC_ADD_STARTWPS" Type="RW" Value="0"/><Attr ID="AC_ADD_APMODE_END" Type="W" Value="0"/></Device></DeviceState></Response>'

class connection_config():
    def __init__(self, host, port, token, cert, duid):
        self.host = host
        self.port = port
        self.token = token
        self.duid = duid
        self.cert = cert
        self.socket = None

@register_connection
class ConnectionSamsung2878(Connection):
    def __init__(self, hass_config, logger):
        super(ConnectionSamsung2878, self).__init__(hass_config, logger)
        self._params = {}
        self._connection_init_template = None
        self._cfg = connection_config(None, None, None, None, None)
        self.update_configuration_from_hass(hass_config)
    
    def update_configuration_from_hass(self, hass_config):
        if hass_config is not None:
            cert_file = hass_config.get(CONF_CERT, None)
            if cert_file == '':
                cert_file = None
            if cert_file is not None:
                if cert_file.find('\\') == -1 and cert_file.find('/') == -1:
                    cert_file = os.path.join(os.path.dirname(__file__), cert_file)

            duid = None
            mac = hass_config.get(CONF_MAC, None)
            if mac is not None:
                duid = re.sub(':', '', mac)
            
            cfg = connection_config(
                hass_config.get(CONF_IP_ADDRESS, None), 
                hass_config.get(CONF_PORT, 2878), 
                hass_config.get(CONF_TOKEN, None),
                cert_file,
                duid)

            self._cfg = cfg
            self._params[CONF_DUID] = cfg.duid
            self._params[CONF_TOKEN] = cfg.token

    def load_from_yaml(self, node, connection_base):
        from jinja2 import Template
        if connection_base is not None:
            self._params.update(connection_base._params.copy())
        
        if node is not None:
            params_node = node.get(CONFIG_DEVICE_CONNECTION_PARAMS, {})
            if CONFIG_DEVICE_CONECTION_TEMPLATE in params_node:
                self._connection_init_template = Template(params_node[CONFIG_DEVICE_CONECTION_TEMPLATE])
            elif connection_base is None:
                self.logger.error("ERROR: missing 'connection_template' parameter in connection section")
                return False
            
            if connection_base is None:
                if self._cfg.host is None:
                    self.logger.error("ERROR: missing 'host' parameter in configuration section")
                    return False
                if self._cfg.token is None or self._cfg.token == '':
                    self.logger.error("ERROR: missing 'token' parameter in configuration section")
                    return False
                if self._cfg.duid == None:
                    self.logger.error("ERROR: missing 'mac' parameter in configuration section")
                    return False
                if self._cfg.cert is None:
                    self.logger.warning("WARNING: 'cert' parameter is empty, skipping certificate validation")
                self.logger.info("Configuration, host: {}:{}".format(self._cfg.host, self._cfg.port))
                self.logger.info("Configuration, token: {}".format(self._cfg.token))
                self.logger.info("Configuration, duid: {}".format(self._cfg.duid))
                self.logger.info("Configuration, cert: {}".format(self._cfg.cert))
            self._params.update(node.get(CONFIG_DEVICE_CONNECTION_PARAMS, {}))    
            return True

        return False

    @staticmethod
    def match_type(type):
        return type == CONNECTION_TYPE_S2878

    def create_updated(self, node):
        c = ConnectionSamsung2878(None, self.logger)
        c._cfg = self._cfg
        c._connection_init_template = self._connection_init_template
        c.load_from_yaml(node, self)
        return c

    def create_connection(self):
        sslSocket = None
        cfg = self._cfg
        try:
            self.logger.info("Creating ssl context")
            sslContext = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
            self.logger.info("Setting up ciphers")
            sslContext.set_ciphers("HIGH:!DH:!aNULL")
            self.logger.info("Setting up verify mode")
            sslContext.verify_mode = ssl.CERT_REQUIRED if cfg.cert is not None else ssl.CERT_NONE
            if cfg.cert is not None:
                self.logger.info("Setting up verify location: {}".format(cfg.cert))
                sslContext.load_verify_locations(cafile = cfg.cert)
                self.logger.info("Setting up load cert chain: {}".format(cfg.cert))
                sslContext.load_cert_chain(cfg.cert)
            else:
                self.logger.info("Cert is empty, skipping verification")
            self.logger.info("Wrapping socket")
            sslSocket = sslContext.wrap_socket(socket(AF_INET, SOCK_STREAM), server_hostname = cfg.host)
            self.logger.info("Socket wrapped: {}".format(True if sslSocket is not None else False))
        except:
            self.logger.error('ERROR creating socket')
            if sslSocket is not None:
                sslSocket.close()
                sslSocket = None
            traceback.print_exc()

        if sslSocket is not None:
            try:
                self.logger.info("Connecting with {}:{}".format(cfg.host, cfg.port))
                sslSocket.connect((cfg.host, cfg.port))
                reply = sslSocket.recv(1024)
                self.logger.info("Response: {}".format(reply.decode("utf-8")))
                reply = sslSocket.recv(1024)
                self.logger.info("Response: {}".format(reply.decode("utf-8")))
                self.logger.info("Socket created successful")
                return sslSocket
            except:
                self.logger.error('ERROR connecting socket')
                if sslSocket is not None:
                    sslSocket.close()
                traceback.print_exc()
        else:
            self.logger.info("ERROR Wrapping socket")

        return None

    def validate_connection(self, sslSocket, init_message):
        if sslSocket is not None:
            try:
                self.logger.info("Sending init message: {}".format(init_message))
                sslSocket.sendall(init_message.encode('utf-8'))
                self.logger.info("Message sent")
                reply = sslSocket.recv(4096)
                if reply is not None:
                    reply_str = reply.decode("utf-8")
                    self.logger.info("Response: {}".format(reply_str))
                    if reply_str.find(CONST_STATUS_OK_STR) != -1:
                        self.logger.info('Connection status OK')
                        return True
                    else:
                        self.logger.error('ERROR while validating connection, response error')

            except:
                self.logger.error('ERROR while validating connection, send error')
                traceback.print_exc()
        
        return False

    def get_socket(self, init_message):
        sslSocket = self._cfg.socket
        if sslSocket is None:
            sslSocket = self.create_connection()
            if not self.validate_connection(sslSocket, init_message):
                self.logger.error("ERROR connecting to device!")
                self._cfg.socket = None
                return None
                
            self.logger.info("Socket created!")
            self._cfg.socket = sslSocket
        
        return sslSocket

    def execute(self, template, v):
        params = self._params
        params.update({ 'value' : v })
        init_message = ''
        if self._connection_init_template is not None:
            init_message = self._connection_init_template.render(**params) + '\n'

        message = v
        if template is not None:
            message = template.render(**params) + '\n'

        xml_response = None
        sslSocket = self.get_socket(init_message)
        if sslSocket is not None:
            try:
                self.logger.info("Sending command: {}".format(message))
                sslSocket.sendall(message.encode('utf-8'))
                self.logger.info("Message sent")
                xml_response = sslSocket.recv(4096).decode("utf-8")
                self.logger.info("Response: {}".format(xml_response))
                return xml_response

            except:
                self.logger.error('ERROR sending command to device')
                if sslSocket is not None:
                    sslSocket.close()
                    self._cfg.socket = None
                traceback.print_exc()
        else:
            self.logger.error('ERROR socket not created')
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
                conn.logger.error("ERROR while converting XML to JSON")
                device_state = {}

        self._json_status = device_state
        self._value = self._json_status
        self._attrs['state_json'] = json.dumps(self._json_status)
        if self.status_template is not None and self._json_status is not None:
            try:
                v = self.status_template.render(device_state=self._json_status)
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
