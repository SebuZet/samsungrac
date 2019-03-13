from .connection import (register_connection, Connection)
from .yaml_const import (CONFIG_DEVICE_CONNECTION_PARAMS)
import json
import logging

CONNECTION_TYPE_REQUEST = 'request'
CONNECTION_TYPE_REQUEST_PRINT = 'request_print'

@register_connection
class ConnectionRequest(Connection):
    def __init__(self, logger):
        super(ConnectionRequest, self).__init__(logger)
        logging.getLogger('urllib3.connectionpool').setLevel(logging.ERROR)

    def load_from_yaml(self, node, connection_base):
        self._params = {} if connection_base is None else connection_base._params.copy()
        if node is not None:
            self._params.update(node.get(CONFIG_DEVICE_CONNECTION_PARAMS, {}))    
        return True

    @staticmethod
    def match_type(type):
        return type == CONNECTION_TYPE_REQUEST

    def create_updated(self, node):
        c = ConnectionRequest(self.logger)
        c.load_from_yaml(node, self)
        return c

    def execute(self, template, value):
        import requests, warnings
        from requests.packages.urllib3.exceptions import InsecureRequestWarning

        params = self._params
        if template is not None:
            params.update(json.loads(template.render(value=value)))
        
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=InsecureRequestWarning)
            with requests.sessions.Session() as session:
                self.logger.info(self._params)
                resp = session.request(**self._params)
                session.close()
        
        if resp is not None and resp.ok:
            try:
                j = resp.json()
            except:
                self.logger.warning("ERROR parsing response json")
                j = {}
            return j
        else:
            self.logger.error("ERROR response error")
        
        return None

test_json = {'Alarms':[{'alarmType':'Device','code':'FilterAlarm','id':'0','triggeredTime':'2019-02-25T08:46:01'}],'ConfigurationLink':{'href':'/devices/0/configuration'},'Diagnosis':{'diagnosisStart':'Ready'},'EnergyConsumption':{'saveLocation':'/files/usage.db'},'InformationLink':{'href':'/devices/0/information'},'Mode':{'modes':['Auto'],'options':['Comode_Off','Sleep_0','Autoclean_Off','Spi_Off','FilterCleanAlarm_0','OutdoorTemp_63','CoolCapa_35','WarmCapa_40','UsagesDB_254','FilterTime_10000','OptionCode_54458','UpdateAllow_0','FilterAlarmTime_500','Function_15','Volume_100'],'supportedModes':['Cool','Dry','Wind','Auto']},'Operation':{'power':'Off'},'Temperatures':[{'current':22.0,'desired':25.0,'id':'0','maximum':30,'minimum':16,'unit':'Celsius'}],'Wind':{'direction':'Fix','maxSpeedLevel':4,'speedLevel':0},'connected':True,'description':'TP6X_RAC_16K','id':'0','name':'RAC','resources':['Alarms','Configuration','Diagnosis','EnergyConsumption','Information','Mode','Operation','Temperatures','Wind'],'type':'Air_Conditioner','uuid':'00000000-0000-0000-0000-000000000000'}

@register_connection
class ConnectionRequestPrint(Connection):
    def __init__(self, logger):
        super(ConnectionRequestPrint, self).__init__(logger)

    def load_from_yaml(self, node, connection_base):
        self._params = {} if connection_base is None else connection_base._params.copy()
        if node is not None:
            self._params.update(node.get(CONFIG_DEVICE_CONNECTION_PARAMS, {}))    
        return True  

    @staticmethod
    def match_type(type):
        return type == CONNECTION_TYPE_REQUEST_PRINT

    def create_updated(self, node):
        c = ConnectionRequestPrint(self.logger)
        c.load_from_yaml(node, self)
        return c

    def execute(self, template, value):
        self.logger.info("ConnectionRequestPrint, execute with params: {}".format(self._params))
        return test_json