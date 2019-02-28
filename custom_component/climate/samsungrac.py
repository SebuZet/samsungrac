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
from homeassistant.helpers.config_validation import PLATFORM_SCHEMA
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
CONF_DISABLE_BEEP = 'enable_beep'
CONF_ENABLE_OFF_MODE = 'extra_off_mode'

LIST_OPERATION = 'op_list'
LIST_COMMANDS = 'op_cmds_list'
LIST_COMMANDS_REMAP = 'op_user_cmds_list'

SUPPORTED_FEATURES = 'features'
SUPPORTED_CUSTOM_FEATURES = 'custom_features'
TEMPERATURE_UNIT = 'temperature_unit'

OP_SPECIAL_MODE = 'special_mode'
OP_PURIFY = 'purify_mode'
OP_BEEP = 'beep_mode'
OP_CLEAN = 'clean_mode'
OP_MODE = 'mode'
OP_TARGET_TEMP = 'temp'
OP_TEMP_MIN = 'min_temp'
OP_TEMP_MAX = 'max_temp'
OP_FAN_MODE = 'fan_mode'
OP_FAN_MODE_MAX = 'fan_mode_max'
OP_SWING = 'swing'
OP_POWER = 'power'
OP_GOOD_SLEEP = 'good_sleep_mode'
OP_GET_STATE = 'get_state'
OP_GET_CONFIG = 'get_config'
OP_GET_INFO = 'get_info'

SUPPORT_CUSTOM_MODES = 1
SUPPORT_TEMPERATURES = 2
SUPPORT_WIND = 4
SUPPORT_OP_SPECIAL_MODE = 8
SUPPORT_OP_PURIFY = 16
SUPPORT_OP_CLEAN = 32
SUPPORT_OP_FAN_MODE_MAX = 64
SUPPORT_OP_GOOD_SLEEP = 128
SUPPORT_OP_BEEP = 256
SUPPORT_EXTRA_MODE_OFF = 512

ATTR_OP_SPECIAL_MODE = 'special_mode'
ATTR_OP_SPECIAL_MODE_LIST = 'special_list'
ATTR_OP_PURIFY = 'purify'
ATTR_OP_PURIFY_LIST = 'purify_list'
ATTR_OP_BEEP = 'beep'
ATTR_OP_BEEP_LIST_LIST = 'beep_list'
ATTR_OP_CLEAN = 'auto_clean'
ATTR_OP_CLEAN_LIST = 'auto_clean_list'
ATTR_OP_GOOD_SLEEP = 'good_sleep'
ATTR_OP_GOOD_SLEEP_LIST = 'good_sleep_list'
ATTR_OP_FAN_MODE_MAX = 'fan_mode_max'
ATTR_OP_FAN_MODE_MAX_LIST = 'fan_mode_max_list'

ATTR_OPTIONS = 'options'
ATTR_POWER = 'power'
ATTR_FAN_MODE_MAX = 'fan_mode_max'
ATTR_DESCRIPTION = 'description'
ATTR_CUSTOM_FEATURES = 'supported_custom_features'

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
RAC_STATE_PURIFY_ON = 'Spi_On'
RAC_STATE_PURIFY_OFF = 'Spi_Off'
RAC_STATE_BEEP_ON = 'Volume_100'
RAC_STATE_BEEP_OFF = 'Volume_Mute'
RAC_STATE_CLEAN_ON = 'Autoclean_On'
RAC_STATE_CLEAN_OFF = 'Autoclean_Off'
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
    OP_BEEP : [STATE_OFF, STATE_ON],
}

DEVICE_STATE_TO_HA = {
    OP_SPECIAL_MODE : { RAC_STATE_SPECIAL_MODE_OFF : STATE_OFF, RAC_STATE_SLEEP : STATE_SLEEP, RAC_STATE_SPEED : STATE_SPEED, RAC_STATE_2STEP : STATE_2STEP, RAC_STATE_COMFORT : STATE_COMFORT, RAC_STATE_QUIET : STATE_QUIET, RAC_STATE_SMART : STATE_SMART },
    OP_PURIFY : { RAC_STATE_PURIFY_OFF : STATE_OFF, RAC_STATE_PURIFY_ON : STATE_ON },
    OP_CLEAN : { RAC_STATE_CLEAN_OFF : STATE_OFF, RAC_STATE_CLEAN_ON : STATE_ON },
    OP_MODE : { RAC_STATE_OFF : STATE_OFF, RAC_STATE_HEAT : STATE_HEAT, RAC_STATE_COOL : STATE_COOL, RAC_STATE_DRY : STATE_DRY, RAC_STATE_WIND : STATE_FAN_ONLY, RAC_STATE_AUTO : STATE_AUTO },
    OP_FAN_MODE : { 0 : STATE_AUTO, 1 : STATE_LOW, 2 : STATE_MEDIUM, 3 : STATE_HIGH, 4 : STATE_TURBO },
    OP_FAN_MODE_MAX : { 0 : STATE_AUTO, 1 : STATE_LOW, 2 : STATE_MEDIUM, 3 : STATE_HIGH, 4 : STATE_TURBO },
    OP_SWING : { RAC_STATE_ALL : STATE_ALL, RAC_STATE_UP_DOWN : STATE_UP_DOWN, RAC_STATE_LEFT_RIGHT : STATE_LEFT_RIGHT, RAC_STATE_FIX : STATE_FIX },
    OP_POWER : { RAC_STATE_OFF : STATE_OFF, RAC_STATE_ON : STATE_ON },
    OP_BEEP : { RAC_STATE_BEEP_ON : STATE_ON, RAC_STATE_BEEP_OFF : STATE_OFF },
}

HA_STATE_TO_DEVICE = {
    OP_SPECIAL_MODE : { STATE_OFF : RAC_STATE_SPECIAL_MODE_OFF, STATE_SLEEP : RAC_STATE_SLEEP, STATE_SPEED : RAC_STATE_SPEED, STATE_2STEP : RAC_STATE_2STEP, STATE_COMFORT : RAC_STATE_COMFORT, STATE_QUIET : RAC_STATE_QUIET, STATE_SMART : RAC_STATE_SMART },
    OP_PURIFY : { STATE_OFF : RAC_STATE_PURIFY_OFF, STATE_ON : RAC_STATE_PURIFY_ON, False : RAC_STATE_OFF, True : RAC_STATE_ON },
    OP_CLEAN : { STATE_OFF : RAC_STATE_CLEAN_OFF, STATE_ON : RAC_STATE_CLEAN_ON, False : RAC_STATE_OFF, True : RAC_STATE_ON },
    OP_MODE : { STATE_OFF : RAC_STATE_OFF, STATE_HEAT : RAC_STATE_HEAT, STATE_COOL : RAC_STATE_COOL, STATE_DRY : RAC_STATE_DRY, STATE_FAN_ONLY : RAC_STATE_WIND, STATE_AUTO : RAC_STATE_AUTO },
    OP_FAN_MODE : { STATE_AUTO : 0, STATE_LOW : 1, STATE_MEDIUM : 2, STATE_HIGH : 3, STATE_TURBO : 4 },
    OP_FAN_MODE_MAX : { STATE_AUTO : 0, STATE_LOW : 1, STATE_MEDIUM : 2, STATE_HIGH : 3, STATE_TURBO : 4 },
    OP_SWING : { STATE_ALL : RAC_STATE_ALL, STATE_UP_DOWN : RAC_STATE_UP_DOWN, STATE_LEFT_RIGHT : RAC_STATE_LEFT_RIGHT, STATE_FIX : RAC_STATE_FIX },
    OP_POWER : { STATE_OFF : RAC_STATE_OFF, STATE_ON : RAC_STATE_ON, False : RAC_STATE_OFF, True : RAC_STATE_ON },
    OP_BEEP : { STATE_OFF : RAC_STATE_BEEP_OFF, STATE_ON : RAC_STATE_BEEP_ON, False : RAC_STATE_OFF, True : RAC_STATE_ON },
}

AVAILABLE_COMMANDS_MAP = {
    OP_SPECIAL_MODE : ['/devices/0/mode', '{left_bracket}"options": ["{value}"]{right_bracket}'],
    OP_PURIFY : ['/devices/0/mode', '{left_bracket}"options": ["{value}"]{right_bracket}'],
    OP_CLEAN : ['/devices/0/mode', '{left_bracket}"options": ["{value}"]{right_bracket}'],
    OP_GOOD_SLEEP : ['/devices/0/mode', '{left_bracket}"options": ["Sleep_{value}"]{right_bracket}'],
    OP_BEEP : ['/devices/0/mode', '{left_bracket}"options": ["{value}"]{right_bracket}'],
    OP_MODE : ['/devices/0/mode', '{left_bracket}"modes": ["{value}"]{right_bracket}'],
    OP_TARGET_TEMP : ['/devices/0/temperatures/0', '{left_bracket}"desired": {value}{right_bracket}'],
    OP_TEMP_MIN : ['/devices/0/temperatures/0', '{left_bracket}"minimum": {value}{right_bracket}'],
    OP_TEMP_MAX : ['/devices/0/temperatures/0', '{left_bracket}"maximum": {value}{right_bracket}'],    
    OP_FAN_MODE : ['/devices/0/wind', '{left_bracket}"speedLevel": {value}{right_bracket}'],
    OP_FAN_MODE_MAX : ['/devices/0/wind', '{left_bracket}"maxSpeedLevel": {value}{right_bracket}'],
    OP_SWING : ['/devices/0/wind', '{left_bracket}"direction": "{value}"{right_bracket}'],
    OP_POWER : ['/devices/0', '{left_bracket}"Operation": {left_bracket}"power":"{value}"{right_bracket}{right_bracket}'],
    OP_GET_STATE : ['/devices'],
    OP_GET_CONFIG : ['/devices/0/configuration'],
    OP_GET_INFO : ['/devices/0/information']
}

EXTRA_MODE_OFF_COMMAND_REMAP = {
    OP_MODE : {
        STATE_OFF : OP_POWER, # :-D
    }
}

OP_TO_ATTR_MAP = {
    OP_SPECIAL_MODE : ATTR_OP_SPECIAL_MODE,
    OP_PURIFY : ATTR_OP_PURIFY,
    OP_CLEAN : ATTR_OP_CLEAN,
    OP_GOOD_SLEEP : ATTR_OP_GOOD_SLEEP,
    OP_MODE : ATTR_FAN_MODE,
    OP_TARGET_TEMP : ATTR_TEMPERATURE,
    OP_TEMP_MIN : ATTR_TARGET_TEMP_LOW,
    OP_TEMP_MAX : ATTR_TARGET_TEMP_HIGH,
    OP_FAN_MODE : ATTR_OP_FAN_MODE_MAX,
    OP_FAN_MODE_MAX : ATTR_FAN_MODE_MAX,
    OP_SWING : ATTR_SWING_MODE,
    OP_POWER : ATTR_POWER,
    OP_BEEP : ATTR_OP_BEEP,
}

ATTR_TO_OP_MAP = {
    ATTR_OP_SPECIAL_MODE : OP_SPECIAL_MODE,
    ATTR_OP_PURIFY : OP_PURIFY,
    ATTR_OP_CLEAN : OP_CLEAN,
    ATTR_OP_GOOD_SLEEP : OP_GOOD_SLEEP,
    ATTR_FAN_MODE : OP_MODE,
    ATTR_TEMPERATURE : OP_TARGET_TEMP,
    ATTR_TARGET_TEMP_LOW : OP_TEMP_MIN,
    ATTR_TARGET_TEMP_HIGH : OP_TEMP_MAX,
    ATTR_OP_FAN_MODE_MAX : OP_FAN_MODE,
    ATTR_FAN_MODE_MAX : OP_FAN_MODE_MAX,
    ATTR_SWING_MODE : OP_SWING,
    ATTR_POWER : OP_POWER,
    ATTR_OP_BEEP : OP_BEEP,
}

JATTR_DEVS = 'Devices'
JATTR_DEV_IDX = 0
JATTR_DEV_MODE = 'Mode'
JATTR_DEV_MODE_MODES = 'modes'
JATTR_DEV_MODE_OPTIONS = 'options'
JATTR_DEV_OPERATION = 'Operation'
JATTR_DEV_OPERATION_POWER = 'power'
JATTR_DEV_TEMPERATURES = 'Temperatures'
JATTR_TEMP_MAX = 'maximum'
JATTR_TEMP_MIN = 'minimum'
JATTR_TEMP_CURRENT = 'current'
JATTR_TEMP_DESIRED = 'desired'
JATTR_TEMP_UNIT = 'unit'
JATTR_MODE_IDX_SPECIAL = 0
JATTR_MODE_IDX_GOOD_SLEEP = 1
JATTR_MODE_IDX_CLEAN = 2
JATTR_MODE_IDX_PURIFY = 3
JATTR_MODE_IDX_BEEP = 14
JATTR_DEV_WIND = 'Wind'
JATTR_WIND_DIRECTION = 'direction'
JATTR_WIND_SPEEDLEVEL = 'speedLevel'
JATTR_WIND_MAX_SPEEDLEVEL = 'maxSpeedLevel'

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
    vol.Optional(CONF_DISABLE_BEEP, default=False): cv.boolean,
    vol.Optional(CONF_ENABLE_OFF_MODE, default=False) : cv.boolean,
})

ATTR_CUSTOM_ATTRIBUTE = 'mode'
ATTR_CUSTOM_ATTRIBUTE_VALUE = 'value'
SERVICE_SET_CUSTOM_OPERATION = 'set_custom_mode'

SET_CUSTOM_OPERATION_SCHEMA = vol.Schema({
    vol.Optional(ATTR_ENTITY_ID): cv.comp_entity_ids,
    vol.Optional(ATTR_OP_SPECIAL_MODE): cv.string,
    vol.Optional(ATTR_OP_PURIFY): cv.string,
    vol.Optional(ATTR_OP_CLEAN): cv.string,
    vol.Optional(ATTR_OP_GOOD_SLEEP): cv.string,
    vol.Optional(ATTR_FAN_MODE): cv.string,
    vol.Optional(ATTR_OP_FAN_MODE_MAX): cv.string,
    vol.Optional(ATTR_FAN_MODE_MAX): cv.string,
    vol.Optional(ATTR_SWING_MODE): cv.string,
    vol.Optional(ATTR_POWER): cv.string,
    vol.Optional(ATTR_OP_BEEP) : cv.string,
    vol.Optional('debug') : cv.boolean,
})

_LOGGER = logging.getLogger(__name__)

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    _LOGGER.info("samsungrac: async setup platform")
    host = config.get(CONF_HOST)
    token = config.get(CONF_ACCESS_TOKEN)
    cert_file = config.get(CONF_CERT_FILE)
    temp_unit = config.get(CONF_TEMPERATURE_UNIT)
    debug = config.get(CONF_DEBUG)
    disabled_flags = 0
    force_flags = 0
    if config.get(CONF_DISABLE_BEEP):
        disabled_flags |= SUPPORT_OP_BEEP
    if config.get(CONF_ENABLE_OFF_MODE):
        force_flags |= SUPPORT_EXTRA_MODE_OFF
    logging.getLogger('urllib3.connectionpool').setLevel(logging.ERROR)
    _LOGGER.setLevel(logging.INFO if debug else logging.ERROR)
    _LOGGER.info("samsungrac: configuration, host: " + host)
    _LOGGER.info("samsungrac: configuration, token: " + token)
    _LOGGER.info("samsungrac: configuration, cert: " + cert_file)
    _LOGGER.info("samsungrac: configuration, unit: " + temp_unit)
    _LOGGER.info("samsungrac: init controller")
    rac = SamsungRacController(host, token, cert_file, temp_unit, debug, disabled_flags, force_flags)
    rac.initialize()
    if not rac.connected:
        _LOGGER.error("samsungrac: platform not ready")
        return PlatformNotReady

    async_add_entities([SamsungRAC(rac)], True)

    async def async_service_handler(service):
        params = {key: value for key, value in service.data.items()
                  if key != ATTR_ENTITY_ID}

        devices = []
        entity_ids = service.data.get(ATTR_ENTITY_ID)
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
    def __init__(self, host, token, cert_file, temp_unit, debug, disabled_flags, force_flags):
        import requests
        _LOGGER.info("samsungrac: create controller")
        self.host = host
        self.token = token
        self.cert = cert_file
        self.set_debug(debug)
        self.connected = False
        self.config = {}
        self.state = {}
        self.disabled_flags = disabled_flags
        self.force_flags = force_flags
        self.extra_headers = { 'Authorization': 'Bearer ' + self.token, 'Content-Type': 'application/json' }
        self.config[TEMPERATURE_UNIT] = temp_unit if temp_unit in UNIT_MAP else DEFAULT_CONF_TEMP_UNIT
        self.config[ATTR_NAME] = DEFAULT_CONF_NAME

    def set_debug(self, val):
        self.debug = val
        _LOGGER.setLevel(logging.INFO if val else logging.ERROR)
    
    def convert_state_rac_to_ha(self, op, state):
        if op in DEVICE_STATE_TO_HA and state in DEVICE_STATE_TO_HA[op]:
            return DEVICE_STATE_TO_HA[op][state]

        if op == OP_GOOD_SLEEP:
            return int(state[6::])
        
        if op == OP_BEEP:
            return STATE_UNKNOWN

        return state

    def convert_ha_state_to_device_state(self, op, state):
        if op in HA_STATE_TO_DEVICE and state in HA_STATE_TO_DEVICE[op]:
            return HA_STATE_TO_DEVICE[op][state]
        
        return state

    def get_device_json(self):
        import requests, warnings
        from requests.packages.urllib3.exceptions import InsecureRequestWarning

        self.connected = False
        cmds = self.get_command_for_operation(OP_GET_STATE, None)
        url  =  cmds[COMMAND_URL] if cmds and len(cmds) > COMMAND_URL else ''
        _LOGGER.info("samsungrac: get_device_json: url: " + self.host + url)
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=InsecureRequestWarning)
            with requests.sessions.Session() as session:
                resp = session.request('GET', url=self.host + url, headers=self.extra_headers, verify=False, cert=self.cert, data=json.dumps({ 'sebu' : 'zet' }))
        if resp is not None and resp.ok:
            _LOGGER.info("samsungrac: get_device_json: parsing response")
            js = resp.json() 
            j = js if js else json.loads(resp.text)
            _LOGGER.info("samsungrac: get_device_json: json parsed: " + json.dumps(j))
            self.connected = True
            return j
        else:
            _LOGGER.error("samsungrac: get_device_json: response error: {}".format(resp.status_code))
            _LOGGER.error("samsungrac: get_device_json: response text: {}".format(resp.text))

        return None

    def initialize(self):
        _LOGGER.info("samsungrac: initialize")

        self.config[LIST_COMMANDS] = AVAILABLE_COMMANDS_MAP
        self.config[LIST_COMMANDS_REMAP] = {}

        j = self.get_device_json()
        if j is not None:
            _LOGGER.info("samsungrac: initialize: updating device configuration")
            # check device capabilities
            custom_flags = 0;
            flags = 0
            operations_map = {}
            # ['Devices'][0]
            if JATTR_DEVS in j and len(j[JATTR_DEVS]) > JATTR_DEV_IDX:
                device = j[JATTR_DEVS][JATTR_DEV_IDX]
                if ATTR_NAME in device:
                    self.config[ATTR_NAME] = DEFAULT_CONF_NAME + "_" + device[ATTR_NAME].lower()
                if ATTR_DESCRIPTION in device:
                    self.config[ATTR_DESCRIPTION] = device[ATTR_DESCRIPTION]

                # ['Devices'][0]['Mode']
                if JATTR_DEV_MODE in device:
                    mode = device[JATTR_DEV_MODE]
                    # ['Devices'][0]['Mode']['options']
                    if JATTR_DEV_MODE_OPTIONS in mode:
                        custom_flags |= SUPPORT_CUSTOM_MODES
                        options = mode[JATTR_DEV_MODE_OPTIONS]
                        if len(options) > JATTR_MODE_IDX_SPECIAL:
                            custom_flags |= SUPPORT_OP_SPECIAL_MODE
                            operations_map[OP_SPECIAL_MODE] = AVAILABLE_OPERATIONS_MAP[OP_SPECIAL_MODE]
                        if len(options) > JATTR_MODE_IDX_GOOD_SLEEP:
                            custom_flags |= SUPPORT_OP_GOOD_SLEEP
                        if len(options) > JATTR_MODE_IDX_CLEAN:
                            custom_flags |= SUPPORT_OP_CLEAN
                            operations_map[OP_CLEAN] = AVAILABLE_OPERATIONS_MAP[OP_CLEAN]
                        if len(options) > JATTR_MODE_IDX_PURIFY:
                            custom_flags |= SUPPORT_OP_PURIFY
                            operations_map[OP_PURIFY] = AVAILABLE_OPERATIONS_MAP[OP_PURIFY]
                        if len(options) > JATTR_MODE_IDX_BEEP and not self.disabled_flags & SUPPORT_OP_BEEP:
                            custom_flags |= SUPPORT_OP_BEEP
                            operations_map[OP_BEEP] = AVAILABLE_OPERATIONS_MAP[OP_BEEP]

                    # ['Devices'][0]['Mode']['modes']
                    if JATTR_DEV_MODE_MODES in mode:
                        if (self.force_flags & SUPPORT_EXTRA_MODE_OFF) and not STATE_OFF in AVAILABLE_OPERATIONS_MAP[OP_MODE]:
                            operations_map[OP_MODE] = [STATE_OFF]
                            operations_map[OP_MODE].append(AVAILABLE_OPERATIONS_MAP[OP_MODE])
                            self.config[LIST_COMMANDS_REMAP].append(EXTRA_MODE_OFF_COMMAND_REMAP)
                        else:
                            operations_map[OP_MODE] = AVAILABLE_OPERATIONS_MAP[OP_MODE]
                        flags |= SUPPORT_OPERATION_MODE

                #['Devices'][0]['Operation']
                if JATTR_DEV_OPERATION in device:
                    operation = device[JATTR_DEV_OPERATION]
                    if JATTR_DEV_OPERATION_POWER in operation:
                        flags |= SUPPORT_ON_OFF
                        operations_map[OP_POWER] = AVAILABLE_OPERATIONS_MAP[OP_POWER]
            
                #['Devices'][0]['Temperatures'][0]
                if JATTR_DEV_TEMPERATURES in device and len(device[JATTR_DEV_TEMPERATURES]) > JATTR_DEV_IDX:
                    custom_flags |= SUPPORT_TEMPERATURES
                    temperatures = device[JATTR_DEV_TEMPERATURES][JATTR_DEV_IDX]
                    if JATTR_TEMP_MAX in temperatures:
                        flags |= SUPPORT_TARGET_TEMPERATURE_HIGH
                    if JATTR_TEMP_MIN in temperatures:
                        flags |= SUPPORT_TARGET_TEMPERATURE_LOW
                    if JATTR_TEMP_DESIRED in temperatures:
                        flags |= SUPPORT_TARGET_TEMPERATURE
                    if JATTR_TEMP_UNIT in temperatures:
                        temp_unit = temperatures[JATTR_TEMP_UNIT]
                        if temp_unit in UNIT_MAP[temp_unit]:
                            self.config[TEMPERATURE_UNIT] = temp_unit

                #['Devices'][0]['Wind']
                if JATTR_DEV_WIND in device:
                    custom_flags |= SUPPORT_WIND
                    wind = device[JATTR_DEV_WIND]
                    if JATTR_WIND_DIRECTION in wind:
                        flags |= SUPPORT_SWING_MODE
                        operations_map[OP_SWING] = AVAILABLE_OPERATIONS_MAP[OP_SWING]
                    if JATTR_WIND_SPEEDLEVEL in wind:
                        operations_map[OP_FAN_MODE] = AVAILABLE_OPERATIONS_MAP[OP_FAN_MODE]
                        flags |= SUPPORT_FAN_MODE
                    if JATTR_WIND_MAX_SPEEDLEVEL in wind:
                        custom_flags |= SUPPORT_OP_FAN_MODE_MAX
                        operations_map[OP_FAN_MODE_MAX] = AVAILABLE_OPERATIONS_MAP[OP_FAN_MODE_MAX]

            self.config[LIST_OPERATION] = operations_map
            
            # values read from device
            self.config[SUPPORTED_FEATURES] = flags
            self.config[SUPPORTED_CUSTOM_FEATURES] = custom_flags
            
            # read device state
            _LOGGER.info("samsungrac: initialize: read device configuration, flags: {}, custom flags: {}".format(flags, custom_flags))
            self.update_state_from_json(j)

        _LOGGER.info("samsungrac: initialize: finished")

    def update_state_from_json(self, j):
        _LOGGER.info("samsungrac: update_state_from_json: " + json.dumps(j))
        custom_flags = self.config[SUPPORTED_CUSTOM_FEATURES]
        flags = self.config[SUPPORTED_FEATURES]
        
        # ['Devices'][0]
        device = j[JATTR_DEVS][JATTR_DEV_IDX]
        if custom_flags & SUPPORT_CUSTOM_MODES:
            # ['Devices'][0]['Mode']
            mode = device[JATTR_DEV_MODE]
            # ['Devices'][0]['Mode']['options']
            options = mode[JATTR_DEV_MODE_OPTIONS]
            self.state[ATTR_OPTIONS] = options
            if custom_flags & SUPPORT_OP_SPECIAL_MODE:
                self.state[ATTR_OP_SPECIAL_MODE] = self.convert_state_rac_to_ha(OP_SPECIAL_MODE, options[JATTR_MODE_IDX_SPECIAL])
            if custom_flags & SUPPORT_OP_GOOD_SLEEP:
                self.state[ATTR_OP_GOOD_SLEEP] = self.convert_state_rac_to_ha(OP_GOOD_SLEEP, options[JATTR_MODE_IDX_GOOD_SLEEP])
            if custom_flags & SUPPORT_OP_CLEAN:
                self.state[ATTR_OP_CLEAN] = self.convert_state_rac_to_ha(OP_CLEAN, options[JATTR_MODE_IDX_CLEAN])
            if custom_flags & SUPPORT_OP_PURIFY:
                self.state[ATTR_OP_PURIFY] = self.convert_state_rac_to_ha(OP_PURIFY, options[JATTR_MODE_IDX_PURIFY])
            if custom_flags & SUPPORT_OP_BEEP:
                self.state[ATTR_OP_BEEP] = self.convert_state_rac_to_ha(OP_BEEP, options[JATTR_MODE_IDX_BEEP])

            # ['Devices'][0]['Mode']['modes']
            if flags & SUPPORT_OPERATION_MODE:
                self.state[ATTR_OPERATION_MODE] = self.convert_state_rac_to_ha(OP_MODE, mode[JATTR_DEV_MODE_MODES][JATTR_DEV_IDX])

        #['Devices'][0]['Operation']
        if flags & SUPPORT_ON_OFF:
            self.state[ATTR_POWER] = self.convert_state_rac_to_ha(OP_POWER, device[JATTR_DEV_OPERATION][JATTR_DEV_OPERATION_POWER])

        #['Devices'][0]['Temperatures'][0]
        if custom_flags & SUPPORT_TEMPERATURES:
            temperatures = device[JATTR_DEV_TEMPERATURES][JATTR_DEV_IDX]
            self.state[ATTR_CURRENT_TEMPERATURE] = self.convert_state_rac_to_ha(OP_TARGET_TEMP, temperatures[JATTR_TEMP_CURRENT])
            if flags & SUPPORT_TARGET_TEMPERATURE_HIGH:
                self.state[ATTR_TARGET_TEMP_HIGH] = self.convert_state_rac_to_ha(OP_TEMP_MAX, temperatures[JATTR_TEMP_MAX])
            if flags & SUPPORT_TARGET_TEMPERATURE_LOW:
                self.state[ATTR_TARGET_TEMP_LOW] = self.convert_state_rac_to_ha(OP_TEMP_MIN, temperatures[JATTR_TEMP_MIN])
            if flags & SUPPORT_TARGET_TEMPERATURE:
                self.state[ATTR_TEMPERATURE] = self.convert_state_rac_to_ha(OP_TARGET_TEMP, temperatures[JATTR_TEMP_DESIRED])

        #['Devices'][0]['Wind']
        if custom_flags & SUPPORT_WIND:
            wind = device[JATTR_DEV_WIND]
            if flags & SUPPORT_SWING_MODE:
                self.state[ATTR_SWING_MODE] = self.convert_state_rac_to_ha(OP_SWING, wind[JATTR_WIND_DIRECTION])                    
            if flags & SUPPORT_FAN_MODE:
                self.state[ATTR_FAN_MODE] = self.convert_state_rac_to_ha(OP_FAN_MODE, wind[JATTR_WIND_SPEEDLEVEL])
            if custom_flags & SUPPORT_OP_FAN_MODE_MAX:
                self.state[ATTR_FAN_MODE_MAX] = self.convert_state_rac_to_ha(OP_FAN_MODE_MAX, wind[JATTR_WIND_MAX_SPEEDLEVEL])

    def update_state(self):
        _LOGGER.info("samsungrac: update_state")
        j = self.get_device_json()
        if j is not None:
            self.update_state_from_json(j)

    def get_command_for_operation(self, op, value):
        config = self.config
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

        _LOGGER.error("samsungrac: get_command_for_operation, NOT FOUND")
        return None

    def execute_operation_command(self, op, val):
        import requests, warnings
        from requests.packages.urllib3.exceptions import InsecureRequestWarning

        _LOGGER.info("samsungrac: execute_operation_command({}, {})".format(op, val))
        org_op = op
        cmd = self.get_command_for_operation(op, val)
        if cmd and len(cmd) > COMMAND_DATA:
            command = cmd[COMMAND_DATA]
        if cmd and len(cmd) > COMMAND_URL:
            url = cmd[COMMAND_URL]
        if command is not None:        
            command = command.format(left_bracket="{", right_bracket="}", value=self.convert_ha_state_to_device_state(op, val))
            url = self.host + (url if url else '')
            _LOGGER.info("samsungrac: execute_operation_command, exe {}, at {}".format(command, url))
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=InsecureRequestWarning)
                with requests.sessions.Session() as session:
                    resp = session.request('PUT', url=url, headers = self.extra_headers, verify=False, cert=self.cert, data=command)
            #resp = requests.put(url, headers = self.extra_headers, verify=False, cert=self.cert, data=command)
            if resp is not None and resp.ok:
                _LOGGER.info("samsungrac: execute_operation_command complited: status code: {}".format(resp.status_code))
                if org_op in OP_TO_ATTR_MAP:
                    self.state[org_op] = val
                return True
            else:
                _LOGGER.error("samsungrac: execute_operation_command FAILED: status code: {}".format(resp.status_code))
                _LOGGER.error("samsungrac: execute_operation_command FAILED: msg: {}".format(resp.text))
                return False
            
        _LOGGER.error("samsungrac: execute_operation_command: Command not found: ({}, {})".format(op, val))
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
        return self.rac.get_config(SUPPORTED_FEATURES)

    @property
    def min_temp(self):
        return convert_temperature(DEFAULT_SAMSUNG_TEMP_MIN, TEMP_CELSIUS, self.temperature_unit)

    @property
    def max_temp(self):
        return convert_temperature(DEFAULT_SAMSUNG_TEMP_MAX, TEMP_CELSIUS, self.temperature_unit)

    @property
    def should_poll(self):
        return False

    @property
    def name(self):
        return self.rac.get_config(ATTR_NAME)

    @property
    def state_attributes(self):
        _LOGGER.info("samsungrac: state_attributes")
        data = super(SamsungRAC, self).state_attributes
        supported_features = self.rac.get_config(SUPPORTED_CUSTOM_FEATURES)
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
            if OP_PURIFY in self.rac.get_config(LIST_OPERATION) and self.rac.debug:
                data[ATTR_OP_PURIFY_LIST] = self.rac.get_config(LIST_OPERATION)[OP_PURIFY]

        if supported_features & SUPPORT_OP_CLEAN:
            data[ATTR_OP_CLEAN] = self.rac.get_state(ATTR_OP_CLEAN)
            if OP_CLEAN in self.rac.get_config(LIST_OPERATION) and self.rac.debug:
                data[ATTR_OP_CLEAN_LIST] = self.rac.get_config(LIST_OPERATION)[OP_CLEAN]

        if supported_features & SUPPORT_OP_GOOD_SLEEP:
            data[ATTR_OP_GOOD_SLEEP] = self.rac.get_state(ATTR_OP_GOOD_SLEEP)
            
        if supported_features & SUPPORT_OP_BEEP:
            data[ATTR_OP_BEEP] = self.rac.get_state(ATTR_OP_BEEP)
            if OP_BEEP in self.rac.get_config(LIST_OPERATION) and self.rac.debug:
                data[ATTR_OP_BEEP_LIST_LIST] = self.rac.get_config(LIST_OPERATION)[OP_BEEP]

        if self.rac.debug:
            data[ATTR_OPTIONS] = self.rac.get_state(ATTR_OPTIONS)
            if self.rac.get_config(ATTR_DESCRIPTION) is not None:
                data[ATTR_DESCRIPTION] = self.rac.get_config(ATTR_DESCRIPTION)

        data[ATTR_CUSTOM_FEATURES] = self.rac.get_config(SUPPORTED_CUSTOM_FEATURES)
        return data

    async def async_update(self):
        time.sleep(1.5)
        self.rac.update_state()

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
        
        if (self.rac.force_flags & SUPPORT_EXTRA_MODE_OFF) and not self.is_on:
            return STATE_OFF
        return self.rac.get_state(ATTR_OPERATION_MODE)

    @property
    def operation_list(self):
        return self.rac.get_config(LIST_OPERATION)[OP_MODE]

    @property
    def is_on(self):
        return self.rac.get_state(ATTR_POWER) == STATE_ON

    @property
    def current_fan_mode(self):
        return self.rac.get_state(ATTR_FAN_MODE)

    @property
    def fan_list(self):
        return self.rac.get_config(LIST_OPERATION)[OP_FAN_MODE]

    def set_temperature(self, **kwargs):
        if kwargs.get(ATTR_TEMPERATURE) is not None:
            self.rac.execute_operation_command(OP_TARGET_TEMP, int(kwargs.get(ATTR_TEMPERATURE)))
        if kwargs.get(ATTR_TARGET_TEMP_HIGH) is not None:
            self.rac.execute_operation_command(OP_TEMP_MAX, int(kwargs.get(ATTR_TARGET_TEMP_HIGH)))
        if kwargs.get(ATTR_TARGET_TEMP_LOW) is not None:
            self.rac.execute_operation_command(OP_TEMP_MIN, int(kwargs.get(ATTR_TARGET_TEMP_LOW)))
        self.schedule_update_ha_state(True)

    def set_swing_mode(self, swing_mode):
        self.rac.execute_operation_command(OP_SWING, swing_mode)
        self.schedule_update_ha_state(True)

    def set_fan_mode(self, fan_mode):
        self.rac.execute_operation_command(OP_FAN_MODE, fan_mode)
        self.schedule_update_ha_state(True)

    def set_operation_mode(self, operation_mode):
        # self.rac.execute_operation_command(OP_POWER, STATE_ON)
        self.rac.execute_operation_command(OP_MODE, operation_mode)
        self.schedule_update_ha_state(True)

    @property
    def current_swing_mode(self):
        return self.rac.get_state(ATTR_SWING_MODE)

    @property
    def swing_list(self):
        return self.rac.get_config(LIST_OPERATION)[OP_SWING]

    def turn_on(self):
        self.rac.execute_operation_command(OP_POWER, STATE_ON)
        self.schedule_update_ha_state(True)

    def turn_off(self):
        self.rac.execute_operation_command(OP_POWER, STATE_OFF)
        self.schedule_update_ha_state(True)

    def set_custom_operation(self, **kwargs):
        """Set custom device mode to specified value."""
        # first, turn device on if requested
        for key, value in kwargs.items():
            if key == 'debug':
                self.rac.set_debug(value)

        for key, value in kwargs.items():
            _LOGGER.info("samsungrac: set_custom_operation: {}, {}".format(key, value))
            if key in ATTR_TO_OP_MAP:
                op = ATTR_TO_OP_MAP[key]
                if op == OP_POWER and value == STATE_ON:
                    self.rac.execute_operation_command(op, value)

        for key, value in kwargs.items():
            if key in ATTR_TO_OP_MAP:
                op = ATTR_TO_OP_MAP[key]
                if op != OP_POWER:
                    self.rac.execute_operation_command(op, value)

        # at the end turn device off if requested
        for key, value in kwargs.items():
            if key in ATTR_TO_OP_MAP:
                op = ATTR_TO_OP_MAP[key]
                if op == OP_POWER and value == STATE_OFF:
                    self.rac.execute_operation_command(op, value)

        self.schedule_update_ha_state(True)

    def async_set_custom_operation(self, **kwargs):
        """Set custom device mode to specified value."""
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
