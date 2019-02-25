"""
Samsung platform that offers support for climate device.

For more details about this platform, please refer to the repository
https://github.com/SebuZet/samsungrac

"""
from homeassistant.components.climate import (ClimateDevice,
    ATTR_TARGET_TEMP_HIGH, ATTR_TARGET_TEMP_LOW, ATTR_CURRENT_TEMPERATURE,
    ATTR_SWING_MODE, ATTR_FAN_MODE, ATTR_OPERATION_MODE,
    STATE_AUTO, STATE_COOL, STATE_FAN_ONLY, STATE_HEAT, STATE_DRY, 
    SUPPORT_TARGET_TEMPERATURE, SUPPORT_TARGET_TEMPERATURE_LOW, SUPPORT_TARGET_TEMPERATURE_HIGH,
    SUPPORT_FAN_MODE, SUPPORT_OPERATION_MODE, SUPPORT_SWING_MODE, SUPPORT_ON_OFF,
    DOMAIN
)
from homeassistant.const import (
    TEMP_CELSIUS, TEMP_FAHRENHEIT, 
    ATTR_ENTITY_ID, ATTR_TEMPERATURE, ATTR_NAME,
    STATE_OFF, STATE_ON, STATE_UNKNOWN,
    CONF_ACCESS_TOKEN, CONF_HOST, CONF_TEMPERATURE_UNIT
)
from homeassistant.exceptions import PlatformNotReady
from homeassistant.helpers.config_validation import (PLATFORM_SCHEMA, PLATFORM_SCHEMA_BASE)
from homeassistant.util.temperature import convert as convert_temperature
from homeassistant.helpers.service import extract_entity_ids
import homeassistant.helpers.entity_component
import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from datetime import timedelta
import functools as ft

import json
import logging
import time
import asyncio

REQUIREMENTS = ['requests>=2.21.0']

DEFAULT_CONF_CERT_FILE = '/config/custom_components/climate/ac14k_m.pem'
DEFAULT_CONF_NAME = 'samsung'
DEFAULT_CONF_TEMP_UNIT = 'C'

CONF_CERT_FILE = 'cert_file'
CONF_DEBUG = 'debug'

LIST_OPERATION = 'op_list'
LIST_COMMANDS = 'op_cmds_list'
LIST_COMMANDS_REMAP = 'op_user_cmds_list'

SUPPORTED_FEATURES = 'supported_features'
TEMPERATURE_UNIT = 'temperature_unit'

OP_SPECIAL_MODE = 'special_mode'
OP_PURIFY = 'purify_mode'
OP_CLEAN = 'clean_mode'
OP_SLEEP = 'sleep_mode'
OP_MODE = 'mode'
OP_TARGET_TEMP = 'temp'
OP_TEMP_MIN = 'min_temp'
OP_TEMP_MAX = 'max_temp'
OP_FAN_MODE = 'fan_mode'
OP_FAN_MODE_MAX = 'fan_mode_max'
OP_SWING = 'swing'
OP_POWER = 'power'
OP_GOOD_SLEEP = 'good_sleep'
OP_GET_STATE = 'get_state'
OP_GET_CONFIG = 'get_config'
OP_GET_INFO = 'get_info'

SUPPORT_OP_SPECIAL_MODE = 1
SUPPORT_OP_PURIFY = 2
SUPPORT_OP_CLEAN = 4
SUPPORT_OP_FAN_MODE_MAX = 8
SUPPORT_OP_GOOD_SLEEP = 16

ATTR_OP_SPECIAL_MODE = 'special_mode'
ATTR_OP_SPECIAL_MODE_LIST = 'special_list'
ATTR_OP_PURIFY = 'purify'
ATTR_OP_PURIFY_LIST = 'purify_list'
ATTR_OP_CLEAN = 'autoclean'
ATTR_OP_CLEAN_LIST = 'autoclean_list'
ATTR_OP_SLEEP = 'goodsleep'
ATTR_OP_SLEEP_LIST = 'goodsleep_list'
ATTR_OP_FAN_MODE_MAX = 'fan_mode_max'
ATTR_OP_FAN_MODE_MAX_LIST = 'fan_mode_max_list'
ATTR_OP_GOOD_SLEEP = 'good_sleep'

ATTR_OPTIONS = 'options'
ATTR_POWER = 'power'
ATTR_FAN_MODE_MAX = 'fan_mode_max'
ATTR_DESCRIPTION = 'description'

STATE_SLEEP = 'sleep'
STATE_SPEED = 'speed'
STATE_2STEP = '2step'
STATE_COMFORT = 'comfort'
STATE_QUIET = 'quiet'
STATE_SMART = 'smart'
STATE_WIND = 'wind'
STATE_LOW = 'low'
STATE_MEDIUM = 'medium'
STATE_HIGH = 'high'
STATE_TURBO = 'turbo'
STATE_ALL = 'all'
STATE_UP_DOWN = 'vertical'
STATE_LEFT_RIGHT = 'horizontal'
STATE_FIX = 'fix'

RAC_STATE_SLEEP = 'Comode_Sleep'
RAC_STATE_SPEED = 'Comode_Speed'
RAC_STATE_2STEP = 'Comode_2Step'
RAC_STATE_COMFORT = 'Comode_Comfort'
RAC_STATE_QUIET = 'Comode_Quiet'
RAC_STATE_SMART = 'Comode_Smart'
RAC_STATE_SPECIAL_MODE_OFF = 'Comode_Off'
REC_STATE_PURIFY_ON = 'Spi_On'
REC_STATE_PURIFY_OFF = 'Spi_Off'
REC_STATE_CLEAN_ON = 'Autoclean_On'
REC_STATE_CLEAN_OFF = 'Autoclean_Off'
RAC_STATE_WIND = 'Wind'
RAC_STATE_LOW = 1
RAC_STATE_MEDIUM = 2
RAC_STATE_HIGH = 3
RAC_STATE_TURBO = 4
RAC_STATE_ALL = 'All'
RAC_STATE_UP_DOWN = 'Up_And_Low'
RAC_STATE_LEFT_RIGHT = 'Left_And_Right'
RAC_STATE_FIX = 'Fix'
RAC_STATE_AUTO = 'Auto'
RAC_STATE_ON = 'On'
RAC_STATE_OFF = 'Off'
RAC_STATE_HEAT = 'Heat'
RAC_STATE_COOL = 'Cool'
RAC_STATE_DRY = 'Dry'

COMMAND_URL = 0
COMMAND_DATA = 1

SAMSUNGRAC_DATA = 'samsung_rac_data'
ENTITIES = 'entities'

AVAILABLE_OPERATIONS_MAP = {
    OP_SPECIAL_MODE : [STATE_OFF, STATE_SLEEP, STATE_SPEED, STATE_2STEP, STATE_COMFORT, STATE_QUIET, STATE_SMART],
    OP_PURIFY : [STATE_OFF, STATE_ON],
    OP_CLEAN : [STATE_OFF, STATE_ON],
#    OP_MODE : [STATE_OFF, STATE_HEAT, STATE_COOL, STATE_DRY, STATE_FAN_ONLY, STATE_AUTO],
    OP_MODE : [STATE_HEAT, STATE_COOL, STATE_DRY, STATE_FAN_ONLY, STATE_AUTO],
    OP_FAN_MODE : [STATE_AUTO, STATE_LOW, STATE_MEDIUM, STATE_HIGH, STATE_TURBO],
    OP_FAN_MODE_MAX : [STATE_AUTO, STATE_LOW, STATE_MEDIUM, STATE_HIGH, STATE_TURBO],
    OP_SWING : [STATE_ALL, STATE_UP_DOWN, STATE_LEFT_RIGHT, STATE_FIX],
    OP_POWER : [STATE_OFF, STATE_ON],
}

DEVICE_STATE_TO_HA = {
    OP_SPECIAL_MODE : { RAC_STATE_SPECIAL_MODE_OFF : STATE_OFF, RAC_STATE_SLEEP : STATE_SLEEP, RAC_STATE_SPEED : STATE_SPEED, RAC_STATE_2STEP : STATE_2STEP, RAC_STATE_COMFORT : STATE_COMFORT, RAC_STATE_QUIET : STATE_QUIET, RAC_STATE_SMART : STATE_SMART },
    OP_PURIFY : { REC_STATE_PURIFY_OFF : STATE_OFF, REC_STATE_PURIFY_ON : STATE_ON },
    OP_CLEAN : { REC_STATE_CLEAN_OFF : STATE_OFF, REC_STATE_CLEAN_ON : STATE_ON },
    OP_MODE : { RAC_STATE_OFF : STATE_OFF, RAC_STATE_HEAT : STATE_HEAT, RAC_STATE_COOL : STATE_COOL, RAC_STATE_DRY : STATE_DRY, RAC_STATE_WIND : STATE_FAN_ONLY, RAC_STATE_AUTO : STATE_AUTO },
    OP_FAN_MODE : { 0 : STATE_AUTO, 1 : STATE_LOW, 2 : STATE_MEDIUM, 3 : STATE_HIGH, 4 : STATE_TURBO },
    OP_FAN_MODE_MAX : { 0 : STATE_AUTO, 1 : STATE_LOW, 2 : STATE_MEDIUM, 3 : STATE_HIGH, 4 : STATE_TURBO },
    OP_SWING : { RAC_STATE_ALL : STATE_ALL, RAC_STATE_UP_DOWN : STATE_UP_DOWN, RAC_STATE_LEFT_RIGHT : STATE_LEFT_RIGHT, RAC_STATE_FIX : STATE_FIX },
    OP_POWER : { RAC_STATE_OFF : STATE_OFF, RAC_STATE_ON : STATE_ON },
}

HA_STATE_TO_DEVICE = {
    OP_SPECIAL_MODE : { STATE_OFF : RAC_STATE_SPECIAL_MODE_OFF, STATE_SLEEP : RAC_STATE_SLEEP, STATE_SPEED : RAC_STATE_SPEED, STATE_2STEP : RAC_STATE_2STEP, STATE_COMFORT : RAC_STATE_COMFORT, STATE_QUIET : RAC_STATE_QUIET, STATE_SMART : RAC_STATE_SMART },
    OP_PURIFY : { STATE_OFF : REC_STATE_PURIFY_OFF, STATE_ON : REC_STATE_PURIFY_ON },
    OP_CLEAN : { STATE_OFF : REC_STATE_CLEAN_OFF, STATE_ON : REC_STATE_CLEAN_ON },
    OP_MODE : { STATE_OFF : RAC_STATE_OFF, STATE_HEAT : RAC_STATE_HEAT, STATE_COOL : RAC_STATE_COOL, STATE_DRY : RAC_STATE_DRY, STATE_FAN_ONLY : RAC_STATE_WIND, STATE_AUTO : RAC_STATE_AUTO },
    OP_FAN_MODE : { STATE_AUTO : 0, STATE_LOW : 1, STATE_MEDIUM : 2, STATE_HIGH : 3, STATE_TURBO : 4 },
    OP_FAN_MODE_MAX : { STATE_AUTO : 0, STATE_LOW : 1, STATE_MEDIUM : 2, STATE_HIGH : 3, STATE_TURBO : 4 },
    OP_SWING : { STATE_ALL : RAC_STATE_ALL, STATE_UP_DOWN : RAC_STATE_UP_DOWN, STATE_LEFT_RIGHT : RAC_STATE_LEFT_RIGHT, STATE_FIX : RAC_STATE_FIX },
    OP_POWER : { STATE_OFF : RAC_STATE_OFF, STATE_ON : RAC_STATE_ON },
}

AVAILABLE_COMMANDS_MAP = {
    OP_SPECIAL_MODE : ['/devices/0/mode', '{left_bracket}"options": ["{value}"]{right_bracket}'],
    OP_PURIFY : ['/devices/0/mode', '{left_bracket}"options": ["{value}"]{right_bracket}'],
    OP_CLEAN : ['/devices/0/mode', '{left_bracket}"options": ["{value}"]{right_bracket}'],
    OP_MODE : ['/devices/0/mode', '{left_bracket}"modes": ["{value}"]{right_bracket}'],
    OP_TARGET_TEMP : ['/devices/0/temperatures/0', '{left_bracket}"desired": {value}{right_bracket}'],
    OP_TEMP_MIN : ['/devices/0/temperatures/0', '{left_bracket}"minimum": {value}{right_bracket}'],
    OP_TEMP_MAX : ['/devices/0/temperatures/0', '{left_bracket}"maximum": {value}{right_bracket}'],    
    OP_FAN_MODE : ['/devices/0/wind', '{left_bracket}"speedLevel": {value}{right_bracket}'],
    OP_FAN_MODE_MAX : ['/devices/0/wind', '{left_bracket}"maxSpeedLevel": {value}{right_bracket}'],
    OP_SWING : ['/devices/0/wind', '{left_bracket}"direction": "{value}"{right_bracket}'],
    OP_POWER : ['/devices/0', '{left_bracket}"Operation": {left_bracket}"power":"{value}"{right_bracket}{right_bracket}'],
    OP_GOOD_SLEEP : ['/devices/0/mode', '{left_bracket}"Operation": "{value}"{right_bracket}'],
    OP_GET_STATE : ['/devices'],
    OP_GET_CONFIG : ['/devices/0/configuration'],
    OP_GET_INFO : ['/devices/0/information']
}

AVAILABLE_COMMANDS_REMAP = {
    OP_MODE : {
        STATE_OFF : OP_POWER, # :-D
    }
}

OP_TO_ATTR_MAP = {
    OP_SPECIAL_MODE : ATTR_OP_SPECIAL_MODE,
    OP_PURIFY : ATTR_OP_PURIFY,
    OP_CLEAN : ATTR_OP_CLEAN,
    OP_SLEEP : ATTR_OP_SLEEP,
    OP_MODE : ATTR_FAN_MODE,
    OP_TARGET_TEMP : ATTR_TEMPERATURE,
    OP_TEMP_MIN : ATTR_TARGET_TEMP_LOW,
    OP_TEMP_MAX : ATTR_TARGET_TEMP_HIGH,
    OP_FAN_MODE : ATTR_OP_FAN_MODE_MAX,
    OP_FAN_MODE_MAX : ATTR_FAN_MODE_MAX,
    OP_SWING : ATTR_SWING_MODE,
    OP_POWER : ATTR_POWER,
    OP_GOOD_SLEEP : ATTR_OP_GOOD_SLEEP
}

ATTR_TO_OP_MAP = {
    ATTR_OP_SPECIAL_MODE : OP_SPECIAL_MODE,
    ATTR_OP_PURIFY : OP_PURIFY,
    ATTR_OP_CLEAN : OP_CLEAN,
    ATTR_OP_SLEEP : OP_SLEEP,
    ATTR_FAN_MODE : OP_MODE,
    ATTR_TEMPERATURE : OP_TARGET_TEMP,
    ATTR_TARGET_TEMP_LOW : OP_TEMP_MIN,
    ATTR_TARGET_TEMP_HIGH : OP_TEMP_MAX,
    ATTR_OP_FAN_MODE_MAX : OP_FAN_MODE,
    ATTR_FAN_MODE_MAX : OP_FAN_MODE_MAX,
    ATTR_SWING_MODE : OP_SWING,
    ATTR_POWER : OP_POWER,
    ATTR_OP_GOOD_SLEEP : OP_GOOD_SLEEP
}

DEFAULT_SUPPORT_FLAGS = SUPPORT_ON_OFF | SUPPORT_OPERATION_MODE | SUPPORT_SWING_MODE | SUPPORT_FAN_MODE | SUPPORT_TARGET_TEMPERATURE | SUPPORT_TARGET_TEMPERATURE_LOW | SUPPORT_TARGET_TEMPERATURE_HIGH
DEFAULT_SAMSUNG_SUPPORT_FLAGS = SUPPORT_OP_SPECIAL_MODE | SUPPORT_OP_PURIFY | SUPPORT_OP_CLEAN | SUPPORT_OP_FAN_MODE_MAX
DEFAULT_SAMSUNG_TEMP_MIN = 16
DEFAULT_SAMSUNG_TEMP_MAX = 32

UNIT_MAP = {
    'C': TEMP_CELSIUS,
    'c': TEMP_CELSIUS,
    'Celsius': TEMP_CELSIUS,
    'F': TEMP_FAHRENHEIT,
    'f': TEMP_FAHRENHEIT,
    'Fahrenheit': TEMP_FAHRENHEIT
}

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_HOST): cv.string,
    vol.Required(CONF_ACCESS_TOKEN): cv.string,
    vol.Optional(CONF_CERT_FILE, default=DEFAULT_CONF_CERT_FILE): cv.string,
    vol.Optional(CONF_TEMPERATURE_UNIT, default=DEFAULT_CONF_TEMP_UNIT): cv.string,
    vol.Optional(CONF_DEBUG, default=False): cv.boolean,
})

ATTR_CUSTOM_ATTRIBUTE = 'mode'
ATTR_CUSTOM_ATTRIBUTE_VALUE = 'value'
SERVICE_SET_CUSTOM_OPERATION = 'set_custom_mode'

SERVICE_SCHEMA = vol.Schema({
    vol.Optional(ATTR_ENTITY_ID): cv.entity_ids,
})

SET_CUSTOM_OPERATION_SCHEMA = SERVICE_SCHEMA.extend({
    vol.Required(ATTR_CUSTOM_ATTRIBUTE): cv.string,
    vol.Required(ATTR_CUSTOM_ATTRIBUTE_VALUE): cv.string,
})

_LOGGER = logging.getLogger(__name__)

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    _LOGGER.info("samsungrac: async setup platform")
    logging.getLogger('urllib3.connectionpool').setLevel(logging.ERROR)
    host = config.get(CONF_HOST)
    token = config.get(CONF_ACCESS_TOKEN)
    cert_file = config.get(CONF_CERT_FILE)
    temp_unit = config.get(CONF_TEMPERATURE_UNIT)
    debug = config.get(CONF_DEBUG)
    _LOGGER.setLevel(logging.INFO if debug else logging.ERROR)
    _LOGGER.info("samsungrac: configuration, host: " + host)
    _LOGGER.info("samsungrac: configuration, token: " + token)
    _LOGGER.info("samsungrac: configuration, cert: " + cert_file)
    _LOGGER.info("samsungrac: configuration, unit: " + temp_unit)
    _LOGGER.info("samsungrac: init controller")
    rac = SamsungRacController(host, token, cert_file, temp_unit, debug)
    rac.initialize()
    if not rac.connected:
        _LOGGER.error("samsungrac: platform not ready")
        return PlatformNotReady

    _LOGGER.info("samsungrac: adding entity")
    async_add_entities([SamsungRAC(rac)], True)

    async def async_service_handler(service):
        _LOGGER.info("samsungrac: async_service_handler: enter ")
        params = {key: value for key, value in service.data.items()
                  if key != ATTR_ENTITY_ID}

        devices = []
        entity_ids = service.data.get(ATTR_ENTITY_ID)
        _LOGGER.info("samsungrac: async_service_handler: entities " + str(entity_ids))
        if SAMSUNGRAC_DATA in hass.data:
            if entity_ids:
                devices = [device for device in hass.data[SAMSUNGRAC_DATA][ENTITIES] if
                    device.entity_id in entity_ids]
            else:
                devices = hass.data[SAMSUNGRAC_DATA][ENTITIES]

        update_tasks = []
        for device in devices:
            if not hasattr(device, 'async_set_custom_operation'):
                continue
            await getattr(device, 'async_set_custom_operation')(**params)
            update_tasks.append(device.async_update_ha_state(True))

        if update_tasks:
            await asyncio.wait(update_tasks, loop=hass.loop)

    hass.services.async_register(DOMAIN, SERVICE_SET_CUSTOM_OPERATION, 
        async_service_handler, schema=SET_CUSTOM_OPERATION_SCHEMA)

class SamsungRacController:
    def __init__(self, host, token, cert_file, temp_unit, debug):
        import requests
        _LOGGER.info("samsungrac: create controller")
        self.host = host
        self.token = token
        self.cert = cert_file
        self.debug = debug
        self.connected = False
        self.config = {}
        self.state = {}
        self.is_on = False
        self.extra_headers = { 'Authorization': 'Bearer ' + self.token, 'Content-Type': 'application/json' }
        self.config[TEMPERATURE_UNIT] = temp_unit if temp_unit in UNIT_MAP else DEFAULT_CONF_TEMP_UNIT
        self.custom_flags = DEFAULT_SAMSUNG_SUPPORT_FLAGS

    def convert_device_state_to_ha_state(self, op, state):
        if op in DEVICE_STATE_TO_HA and state in DEVICE_STATE_TO_HA[op]:
            return DEVICE_STATE_TO_HA[op][state]
        return state

    def convert_ha_state_to_device_state(self, op, state):
        if op in HA_STATE_TO_DEVICE and state in HA_STATE_TO_DEVICE[op]:
            return HA_STATE_TO_DEVICE[op][state]
        return state

    def get_device_json(self):
        import requests, requests.exceptions

        self.connected = False
        _LOGGER.info("samsungrac: get_device_json")
#        try:
        cmds = self.get_command_for_operation(OP_GET_STATE, None)
        url  =  cmds[COMMAND_URL] if cmds and len(cmds) > COMMAND_URL else ''
        _LOGGER.info("samsungrac: get_device_json: url: " + self.host + url)
        resp = requests.get(self.host + url, headers=self.extra_headers, verify=False, cert=self.cert, data=json.dumps({ 'sebu' : 'zet' }))
        if resp.ok:
            _LOGGER.info("samsungrac: get_device_json: parsing response")
            j = json.loads(resp.text)
            _LOGGER.info("samsungrac: get_device_json: json parsed: " + json.dumps(j))
            self.connected = True
            return j
        else:
            _LOGGER.info("samsungrac: get_device_json: response error: {}".format(resp.status_code))

#        except requests.exceptions.SSLError:
#            _LOGGER.error("samsungrac: SSL Error, make sure you have correct cert_file configuration")
#        except (requests.exceptions.RequestException, requests.exceptions.ConnectionError, exceptions.requests.HTTPError) :
#           _LOGGER.error("samsungrac: ambiguous exception occurred while connection to AC")
#        except:
#           _LOGGER.error("samsungrac: Cos poszlo nie tak!!!!")

        return None

    def initialize(self):
        _LOGGER.info("samsungrac: initialize")

        self.config[LIST_COMMANDS] = AVAILABLE_COMMANDS_MAP
        self.config[LIST_COMMANDS_REMAP] = AVAILABLE_COMMANDS_REMAP

        j = self.get_device_json()
        if j is not None:
            _LOGGER.info("samsungrac: initialize: updating device configuration")

            # hardcoded values
            operations_map = {}
            operations_map[OP_SWING] = AVAILABLE_OPERATIONS_MAP[OP_SWING]
            operations_map[OP_FAN_MODE] = AVAILABLE_OPERATIONS_MAP[OP_FAN_MODE]
            operations_map[OP_FAN_MODE_MAX] = AVAILABLE_OPERATIONS_MAP[OP_FAN_MODE_MAX]
            operations_map[OP_MODE] = AVAILABLE_OPERATIONS_MAP[OP_MODE]
            operations_map[OP_SPECIAL_MODE] = AVAILABLE_OPERATIONS_MAP[OP_SPECIAL_MODE]
            operations_map[OP_PURIFY] = AVAILABLE_OPERATIONS_MAP[OP_PURIFY]
            operations_map[OP_CLEAN] = AVAILABLE_OPERATIONS_MAP[OP_CLEAN]
            
            self.config[LIST_OPERATION] = operations_map
            
            # values read from device
            self.config[ATTR_DESCRIPTION] = j['Devices'][0]['description']
            self.config[SUPPORTED_FEATURES] = DEFAULT_SUPPORT_FLAGS

            dev_name = j['Devices'][0]['name']
            if dev_name:
                self.config[ATTR_NAME] = DEFAULT_CONF_NAME + "_" + dev_name.lower()
            else:
                self.config[ATTR_NAME] = DEFAULT_CONF_NAME

            temp_unit = j['Devices'][0]['Temperatures'][0]['unit']
            if temp_unit in UNIT_MAP[temp_unit]:
                self.config[TEMPERATURE_UNIT] = temp_unit
            
            # read device state
            self.update_state_from_json(j)

        _LOGGER.info("samsungrac: initialize: finished")

    def update_state_from_json(self, j):
        self.state[ATTR_OPERATION_MODE] = self.convert_device_state_to_ha_state(
            OP_MODE, j['Devices'][0]['Mode']['modes'][0])
        
        self.state[ATTR_POWER] = self.convert_device_state_to_ha_state(
            OP_POWER, j['Devices'][0]['Operation']['power'])
        
        self.state[ATTR_OPTIONS] = j['Devices'][0]['Mode']['options']
        
        supported_features = self.get_config(SUPPORTED_FEATURES)
        
        if supported_features & SUPPORT_TARGET_TEMPERATURE_HIGH:
            self.state[ATTR_TARGET_TEMP_HIGH] = self.convert_device_state_to_ha_state(
                OP_TEMP_MAX, j['Devices'][0]['Temperatures'][0]['maximum'])

        if supported_features & SUPPORT_TARGET_TEMPERATURE_LOW:
            self.state[ATTR_TARGET_TEMP_LOW] = self.convert_device_state_to_ha_state(
                OP_TEMP_MIN, j['Devices'][0]['Temperatures'][0]['minimum'])

        self.state[ATTR_CURRENT_TEMPERATURE] = self.convert_device_state_to_ha_state(
            OP_TARGET_TEMP, j['Devices'][0]['Temperatures'][0]['current'])

        self.state[ATTR_TEMPERATURE] = self.convert_device_state_to_ha_state(
            OP_TARGET_TEMP, j['Devices'][0]['Temperatures'][0]['desired'])
        
        if self.custom_flags & SUPPORT_OP_SPECIAL_MODE:
            self.state[ATTR_OP_SPECIAL_MODE] = self.convert_device_state_to_ha_state(
                OP_SPECIAL_MODE, j['Devices'][0]['Mode']['options'][0])
        
        if self.custom_flags & SUPPORT_OP_PURIFY:
            self.state[ATTR_OP_PURIFY] = self.convert_device_state_to_ha_state(
                OP_PURIFY, j['Devices'][0]['Mode']['options'][3])
        
        if self.custom_flags & SUPPORT_OP_CLEAN:
            self.state[ATTR_OP_CLEAN] = self.convert_device_state_to_ha_state(
                OP_CLEAN, j['Devices'][0]['Mode']['options'][2])

        if supported_features & SUPPORT_SWING_MODE:        
            self.state[ATTR_SWING_MODE] = self.convert_device_state_to_ha_state(
                OP_SWING, j['Devices'][0]['Wind']['direction'])
        
        if supported_features & SUPPORT_FAN_MODE:
            self.state[ATTR_FAN_MODE] = self.convert_device_state_to_ha_state(
                OP_FAN_MODE, j['Devices'][0]['Wind']['speedLevel'])
        
        if self.custom_flags & SUPPORT_OP_FAN_MODE_MAX:
            self.state[ATTR_FAN_MODE_MAX] = self.convert_device_state_to_ha_state(
                OP_FAN_MODE_MAX, j['Devices'][0]['Wind']['maxSpeedLevel'])
        
        if self.custom_flags & SUPPORT_OP_GOOD_SLEEP:
            self.state[ATTR_OP_GOOD_SLEEP] = self.convert_device_state_to_ha_state(
                OP_GOOD_SLEEP, j['Devices'][0]['Mode']['options'][1])

        self.is_on = self.state[ATTR_POWER] == STATE_ON

    def update_state(self):
        _LOGGER.info("samsungrac: update state")
        j = self.get_device_json()
        if j is not None:
            self.update_state_from_json(j)
        _LOGGER.info("samsungrac: update state completed")

    def get_command_for_operation(self, op, value):
        config = self.config
        _LOGGER.info("samsungrac: get_command_for_operation, {}, {}".format(op, value))
        if LIST_COMMANDS_REMAP in self.config and value is not None:
            if op in config[LIST_COMMANDS_REMAP]:
                if value in config[LIST_COMMANDS_REMAP][op]:
                    op = config[LIST_COMMANDS_REMAP][op][value]
                    _LOGGER.info("samsungrac: get_command_for_operation, command remaped to: {}".format(op))

        if LIST_COMMANDS in self.config:
            if op in config[LIST_COMMANDS]:
                command = config[LIST_COMMANDS][op]
                _LOGGER.info("samsungrac: get_command_for_operation, {}".format(command))
                return command

        _LOGGER.info("samsungrac: get_command_for_operation, NOT FOUND")
        return None

    def execute_operation_command(self, op, val, update_state=True):
        import requests

        _LOGGER.info("samsungrac: execute_operation_command({}, {})".format(op, val))
        org_op = op
        cmd = self.get_command_for_operation(op, val)
        if cmd and len(cmd) > COMMAND_DATA:
            command = cmd[COMMAND_DATA]
        if cmd and len(cmd) > COMMAND_URL:
            url = cmd[COMMAND_URL]
        if command is not None:        
            command = command.format(left_bracket="{", right_bracket="}", value=self.convert_ha_state_to_device_state(op, val))
            _LOGGER.info("samsungrac: execute_operation_command, formatted op: {}".format(command))
            try:
                url = self.host + (url if url else '')
                _LOGGER.error("samsungrac: EXECUTE {}, at {}".format(command, url))
                resp = requests.put(url, headers = self.extra_headers, verify=False, cert=self.cert, data=command)
                #_LOGGER.info("samsungrac: execute_operation_command complited: {}, status code: {}".format("OK" if resp.ok else "NOT OK", resp.status_code))
                if resp.ok:
                    if org_op in OP_TO_ATTR_MAP:
                        self.state[org_op] = val
                        if update_state:
                            self.rac.update_state()
                    return True
                else:
                    _LOGGER.error("samsungrac: execute_operation_command FAILED: status code: {}".format(resp.status_code))
                    _LOGGER.error("samsungrac: execute_operation_command FAILED: msg: {}".format(resp.text))
            except:
                _LOGGER.error("samsungrac: execute_operation_command: response error: {}".format(resp.status_code))
                _LOGGER.info("samsungrac: execute_operation_command, formatted op: {}".format(command))
            
        _LOGGER.error("samsungrac: execute_operation_command: FAILED: cannot find command")
        return False

    def get_state(self, key):
        return self.state[key] if key in self.state else None

    def get_config(self, key):
        if not key in self.config:
            _LOGGER.error("samsungrac: get_config({}): no config found for given key".format(key))
            if self.debug:
                return "IMPLEMENT ME: config for key " + key
            else:
                return None
        else:
            return self.config[key]

class SamsungRAC(ClimateDevice):
    """Representation of a Samsung climate device."""

    def __init__(self, rac_controller):
        self.rac = rac_controller

    @property
    def supported_features(self):
        flags = self.rac.get_config(SUPPORTED_FEATURES)
        return flags if flags else 0

    @property
    def min_temp(self):
        return convert_temperature(DEFAULT_SAMSUNG_TEMP_MIN, TEMP_CELSIUS, self.temperature_unit)

    @property
    def max_temp(self):
        return convert_temperature(DEFAULT_SAMSUNG_TEMP_MAX, TEMP_CELSIUS, self.temperature_unit)

    @property
    def should_poll(self):
        return True

    @property
    def name(self):
        return self.rac.get_config(ATTR_NAME)

    @property
    def state_attributes(self):
        data = super(SamsungRAC, self).state_attributes
        supported_features = self.rac.custom_flags
        config = self.rac.config
        
        if supported_features & SUPPORT_OP_SPECIAL_MODE:
            data[ATTR_OP_SPECIAL_MODE] = self.rac.get_state(ATTR_OP_SPECIAL_MODE)
            if OP_SPECIAL_MODE in self.rac.get_config(LIST_OPERATION):
                data[ATTR_OP_SPECIAL_MODE_LIST] = self.rac.get_config(LIST_OPERATION)[OP_SPECIAL_MODE]

        if supported_features & SUPPORT_OP_FAN_MODE_MAX:
            data[ATTR_OP_FAN_MODE_MAX] = self.rac.get_state(ATTR_OP_FAN_MODE_MAX)
            if OP_FAN_MODE_MAX in self.rac.get_config(LIST_OPERATION):
                data[ATTR_OP_FAN_MODE_MAX_LIST] = self.rac.get_config(LIST_OPERATION)[OP_FAN_MODE_MAX]

        if supported_features & SUPPORT_OP_PURIFY:
            data[ATTR_OP_PURIFY] = self.rac.get_state(ATTR_OP_PURIFY)
            if OP_PURIFY in self.rac.get_config(LIST_OPERATION):
                data[ATTR_OP_PURIFY_LIST] = self.rac.get_config(LIST_OPERATION)[OP_PURIFY]

        if supported_features & SUPPORT_OP_CLEAN:
            data[ATTR_OP_CLEAN] = self.rac.get_state(ATTR_OP_CLEAN)
            if OP_CLEAN in self.rac.get_config(LIST_OPERATION):
                data[ATTR_OP_CLEAN_LIST] = self.rac.get_config(LIST_OPERATION)[OP_CLEAN]

        if supported_features & SUPPORT_OP_GOOD_SLEEP:
            data[ATTR_OP_GOOD_SLEEP] = self.rac.get_state(ATTR_OP_GOOD_SLEEP)
            if OP_GOOD_SLEEP in self.rac.get_config(LIST_OPERATION):
                data[ATTR_OP_GOOD_SLEEP_LIST] = self.rac.get_config(LIST_OPERATION)[OP_GOOD_SLEEP]
            
        if self.rac.debug:
            data[ATTR_OPTIONS] = self.rac.get_state(ATTR_OPTIONS)
            if self.rac.get_config(ATTR_DESCRIPTION) is not None:
                data[ATTR_DESCRIPTION] = self.rac.get_config(ATTR_DESCRIPTION)

        return data

    @property
    def temperature_unit(self):
        unit = self.rac.get_config(TEMPERATURE_UNIT)
        return UNIT_MAP[unit] if unit in UNIT_MAP else TEMP_CELSIUS

    @property
    def current_temperature(self):
        return self.rac.get_state(ATTR_CURRENT_TEMPERATURE)

    @property
    def target_temperature(self):
        return self.rac.get_state(ATTR_TEMPERATURE)

    @property
    def target_temperature_step(self):
        return int(1)

    @property
    def target_temperature_high(self):
        return self.rac.get_state(ATTR_TARGET_TEMP_HIGH)

    @property
    def target_temperature_low(self):
        return self.rac.get_state(ATTR_TARGET_TEMP_LOW)

    @property
    def current_operation(self):
        if not self.rac.connected:
            return None
        
        return self.rac.get_state(ATTR_OPERATION_MODE)

    @property
    def operation_list(self):
        return self.rac.get_config(LIST_OPERATION)[OP_MODE]

    @property
    def is_on(self):
        return self.rac.is_on

    @property
    def current_fan_mode(self):
        return self.rac.get_state(ATTR_FAN_MODE)

    @property
    def fan_list(self):
        return self.rac.get_config(LIST_OPERATION)[OP_FAN_MODE]

    def set_temperature(self, **kwargs):
        if kwargs.get(ATTR_TEMPERATURE) is not None:
            self.rac.execute_operation_command(OP_TARGET_TEMP, int(kwargs.get(ATTR_TEMPERATURE)), False)
        if kwargs.get(ATTR_TARGET_TEMP_HIGH) is not None:
            self.rac.execute_operation_command(OP_TEMP_MAX, int(kwargs.get(ATTR_TARGET_TEMP_HIGH)), False)
        if kwargs.get(ATTR_TARGET_TEMP_LOW) is not None:
            self.rac.execute_operation_command(OP_TEMP_MIN, int(kwargs.get(ATTR_TARGET_TEMP_LOW)), False)
        self.rac.update_state()
        self.schedule_update_ha_state()

    def set_swing_mode(self, swing_mode):
        self.rac.execute_operation_command(OP_SWING, swing_mode)
        self.schedule_update_ha_state()

    def set_fan_mode(self, fan_mode):
        self.rac.execute_operation_command(OP_FAN_MODE, fan_mode)
        self.schedule_update_ha_state()

    def set_operation_mode(self, operation_mode):
        self.rac.execute_operation_command(OP_MODE, operation_mode)
        self.schedule_update_ha_state()

    @property
    def current_swing_mode(self):
        return self.rac.get_state(ATTR_SWING_MODE)

    @property
    def swing_list(self):
        return self.rac.get_config(LIST_OPERATION)[OP_SWING]

    def turn_on(self):
        self.rac.execute_operation_command(OP_POWER, STATE_ON)
        self.rac.update_state()
        self.schedule_update_ha_state()

    def turn_off(self):
        self.rac.execute_operation_command(OP_POWER, STATE_OFF)
        self.schedule_update_ha_state()

    def set_custom_operation(self, **kwargs):
        """Set custom device mode to specified value."""
        _LOGGER.error("samsungrac: set_custom_operation")
        op = kwargs.get(ATTR_CUSTOM_ATTRIBUTE)
        val = kwargs.get(ATTR_CUSTOM_ATTRIBUTE_VALUE)
        self.rac.execute_operation_command(op, val)
        self.schedule_update_ha_state()

    def async_set_custom_operation(self, **kwargs):
        """Set custom device mode to specified value."""
        _LOGGER.error("samsungrac: async_set_custom_operation")
        return self.hass.async_add_job(
            ft.partial(self.set_custom_operation, **kwargs))

    async def async_added_to_hass(self):
        if SAMSUNGRAC_DATA not in self.hass.data:
            self.hass.data[SAMSUNGRAC_DATA] = {}
            self.hass.data[SAMSUNGRAC_DATA][ENTITIES] = []
        self.hass.data[SAMSUNGRAC_DATA][ENTITIES].append(self)

    async def async_will_remove_from_hass(self):
        if SAMSUNGRAC_DATA  in self.hass.data:
            self.hass.data[SAMSUNGRAC_DATA].remove(self)
