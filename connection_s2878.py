from .connection import (register_connection, Connection)
from .yaml_const import (CONFIG_DEVICE_CONNECTION_PARAMS, CONFIG_DEVICE_CONECTION_TEMPLATE)
from socket import * 
import json
import logging
import sys
import ssl
import traceback

CONNECTION_TYPE_S2878 = 'samsung_2878'

CONF_PORT = 'port'
CONF_HOST = 'host'
CONF_DUID = 'duid'
CONF_TOKEN = 'token'

xml_test = '<?xml version="1.0" encoding="utf-8" ?><Response Type="DeviceState" Status="Okay"><DeviceState><Device DUID="XXXXXXX" GroupID="AC" ModelID="AC" ><Attr ID="AC_FUN_ENABLE" Type="RW" Value="Enable"/><Attr ID="AC_FUN_TEMPNOW" Type="R" Value="79"/><Attr ID="AC_FUN_TEMPSET" Type="RW" Value="24"/><Attr ID="AC_FUN_POWER" Type="RW" Value="On"/><Attr ID="AC_FUN_OPMODE" Type="RW" Value="Cool"/><Attr ID="AC_FUN_WINDLEVEL" Type="RW" Value="Auto"/><Attr ID="AC_FUN_ERROR" Type="R" Value="30303030"/><Attr ID="AC_ADD_STARTWPS" Type="RW" Value="0"/><Attr ID="AC_ADD_APMODE_END" Type="W" Value="0"/></Device></DeviceState></Response>'

@register_connection
class ConnectionSamsung2878(Connection):
    def __init__(self, logger):
        super(ConnectionSamsung2878, self).__init__(logger)
        self._params = {}
        self._port = 2878
        self._token = None
        self._duid = None
        self._host = None
        self._connection_init_template = None
        
    def ssl_wrap_socket(self, sock):
        try:
            sslContext = ssl.create_default_context()
            sslContext.set_ciphers("HIGH:!DH:!aNULL")
            sslContext.check_hostname = False
            sslContext.verify_mode = ssl.CERT_NONE
            return sslContext.wrap_socket(sock, server_side=False, server_hostname=HOST)
        except ssl.SSLError:
            self.logger.error("wrap socket failed!")
            self.logger.error(traceback.format_exc())
            sock.close()
        return None

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
                if CONF_PORT in params_node:
                    self._port = params_node[CONF_PORT]
                    self._params[CONF_PORT] = self._port
                    self.logger.info(self._port)
                if CONF_HOST in params_node:
                    self._host = params_node[CONF_HOST]
                    self._params[CONF_HOST] = self._host
                else:
                    print ("ERROR: missing 'host' parameter in connection section")
                    return False
                if CONF_DUID in params_node:
                    self._duid = params_node[CONF_DUID]
                    self._params[CONF_DUID] = self._duid
                    self.logger.info(self._duid)
                else:
                    print ("ERROR: missing 'duid' parameter in connection section")
                    return False
                if CONF_TOKEN in params_node:
                    self._token = params_node[CONF_TOKEN]
                    self._params[CONF_TOKEN] = self._token
                    self.logger.info(self._token)
                else:
                    print ("ERROR: missing 'token' parameter in connection section")
                    return False
    #            if CONF_CERT in params_node:
    #                self._cert = params_node[CONF_CERT]
    #            else:
    #                print ("ERROR: missing 'cert' parameter in connection section")
    #                return False
            self._params.update(node.get(CONFIG_DEVICE_CONNECTION_PARAMS, {}))    
            return True
        return False

    @staticmethod
    def match_type(type):
        return type == CONNECTION_TYPE_S2878

    def create_updated(self, node):
        c = ConnectionSamsung2878(self.logger)
        c._port = self._port
        c._token = self._token
        c._duid = self._duid
        c._host = self._host
        c._connection_init_template = self._connection_init_template
        c.load_from_yaml(node, self)
        return c

    def execute(self, template, v):
        from collections import OrderedDict
        from xml.etree.ElementTree import fromstring
        import xmljson

        params = self._params
        params.update({ 'value' : v})
        init_message = ''
        if self._connection_init_template is not None:
            init_message = self._connection_init_template.render(**params)

        message = v
        if template is not None:
            message = template.render(**params)

        xml_string = '</>'
#        xml_string = xml_test
#        """
        clientSocket = socket(AF_INET, SOCK_STREAM)
        sslSocket = self.ssl_wrap_socket(clientSocket)
        if sslSocket is not None:
            try:
                sslSocket.connect((self._host, self._port))
                reply = sslSocket.recv(1024)
                self.logger.info(reply) # DRC-1.00
                reply = sslSocket.recv(1024)
                self.logger.info(reply)  # <?xml version="1.0" encoding="utf-8" ?><Update Type="InvalidateAccount"/>
                sslSocket.send(init_message)
                reply = sslSocket.recv(1024)
                self.logger.info(reply) # <?xml version="1.0" encoding="utf-8" ?><Response Type="AuthToken" Status="Okay" StartFrom="2019-03-12/11:57:18"/>
                sslSocket.send(message)
                xml_string = sslSocket.recv(1024).decode("utf-8")

            except:
                self.logger.error('ConnectionSamsung2878: socket error')
                sslSocket.shutdown(SHUT_RDWR)
                sslSocket.close()

            finally:
                sslSocket.close()
#        """
        #self.logger.info("XML response: {}".format(xml_string))
        try:
            conv = xmljson.Abdera(dict_type=OrderedDict)
            j = conv.data(fromstring(xml_string))
            #self.logger.info("JSON response: {}".format(json.dumps(j)))
            return j
        except:
            return {}
        
        return None
