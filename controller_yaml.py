import yaml
import logging
import os

from .yaml_const import (
    CONFIG_DEVICE, CONFIG_DEVICE_CONNECTION, CONFIG_DEVICE_STATUS,
    CONFIG_DEVICE_OPERATIONS, CONFIG_DEVICE_ATTRIBUTES, CONFIG_DEVICE_FRIENDLY_NAME,
    CONF_CONFIG_FILE, CONFIG_DEVICE_NAME, CONFIG_DEVICE_VALIDATE_PROPS,
    CONFIG_DEVICE_CONNECTION_PARAMS,
)

from .controller import (
    ATTR_POWER, ClimateController, register_controller
)

from .properties import (
    create_status_getter, 
    create_property
)

from .connection import (
    create_connection
)

from homeassistant.components.climate import (
    ATTR_TARGET_TEMP_HIGH, ATTR_TARGET_TEMP_LOW, ATTR_SWING_MODE, ATTR_FAN_MODE, ATTR_OPERATION_MODE
    )
from homeassistant.components.climate.const import (
    SUPPORT_TARGET_TEMPERATURE, SUPPORT_TARGET_TEMPERATURE_LOW, SUPPORT_TARGET_TEMPERATURE_HIGH,
    SUPPORT_FAN_MODE, SUPPORT_OPERATION_MODE, SUPPORT_SWING_MODE, SUPPORT_ON_OFF, SUPPORT_ON_OFF
    )
from homeassistant.const import (
    TEMP_CELSIUS, TEMP_FAHRENHEIT, ATTR_NAME, ATTR_TEMPERATURE,
    CONF_IP_ADDRESS, CONF_TEMPERATURE_UNIT, CONF_TOKEN,
    STATE_ON, ATTR_ENTITY_ID,
)

from homeassistant.helpers.config_validation import PLATFORM_SCHEMA
import homeassistant.helpers.config_validation as cv
import homeassistant.helpers.entity_component
import voluptuous as vol

SUPPORTED_FEATURES_MAP = {
    ATTR_TEMPERATURE : SUPPORT_TARGET_TEMPERATURE,
    ATTR_TARGET_TEMP_HIGH : SUPPORT_TARGET_TEMPERATURE_HIGH,
    ATTR_TARGET_TEMP_LOW : SUPPORT_TARGET_TEMPERATURE_LOW,
    ATTR_FAN_MODE : SUPPORT_FAN_MODE,
    ATTR_OPERATION_MODE : SUPPORT_OPERATION_MODE,
    ATTR_SWING_MODE : SUPPORT_SWING_MODE,
    ATTR_POWER : SUPPORT_ON_OFF,
}

CONST_CONTROLLER_TYPE = 'yaml'

UNIT_MAP = {
    'C': TEMP_CELSIUS, 'c': TEMP_CELSIUS, 'Celsius': TEMP_CELSIUS, TEMP_CELSIUS : TEMP_CELSIUS,
    'F': TEMP_FAHRENHEIT, 'f': TEMP_FAHRENHEIT, 'Fahrenheit': TEMP_FAHRENHEIT, TEMP_FAHRENHEIT : TEMP_FAHRENHEIT,
}

class StreamWrapper(object):
    def __init__(self, stream, token, ip_address):
        self.stream = stream
        self.leftover = ''
        self.token = token
        self.ip_address = ip_address

    def read(self, size):
        data = self.leftover
        count = len(self.leftover)

        if count < size:
            chunk = self.stream.read(size)

            if self.token is not None:
                chunk = chunk.replace('__CLIMATE_IP_TOKEN__', self.token)
            if self.ip_address is not None:
                chunk = chunk.replace('__CLIMATE_IP_HOST__', self.ip_address)

            data += chunk
            count += len(chunk)

        self.leftover = data[size:]
        return data[:size]

@register_controller
class YamlController(ClimateController):
    def __init__(self, config, logger):
        super(YamlController, self).__init__(config, logger)
        self._logger = logger
        self._operations = {}
        self._properties = {}
        self._name = CONST_CONTROLLER_TYPE
        self._friendly_name = None
        self._attributes = { 'controller' : self.id }
        self._state_getter = None
        self._debug = config.get('debug', False)
        self._supported_features = 0
        self._temp_unit = TEMP_CELSIUS
        self._service_schema_map = { vol.Optional(ATTR_ENTITY_ID) : cv.comp_entity_ids }
        self._logger.setLevel(logging.INFO if self._debug else logging.ERROR)
        self._yaml = config.get(CONF_CONFIG_FILE)
        self._ip_address = config.get(CONF_IP_ADDRESS, None)
        self._token = config.get(CONF_TOKEN, None)
        self._config = config
        
    @property
    def id(self):
        return CONST_CONTROLLER_TYPE

    def initialize(self):
        connection_params = { CONFIG_DEVICE_CONNECTION_PARAMS : { } }
        
        file = self._yaml
        if file is not None and file.find('\\') == -1 and file.find('/') == -1:
            file = os.path.join(os.path.dirname(__file__), file)
        self._logger.info("Loading configuration file: {}".format(file))

        if self._ip_address is not None:
            self._logger.info("ip_address: {}".format(self._ip_address))
        if self._token is not None:
            self._logger.info("token: {}".format(self._token))

        with open(file, 'r') as stream:
            try:
                yaml_device = yaml.safe_load(StreamWrapper(stream, self._token, self._ip_address))
            except yaml.YAMLError as exc:
                if self._logger is not None:
                    self._logger.error("YAML error: {}".format(exc))
                return False
            except FileNotFoundError:
                if self._logger is not None:
                    self._logger.error("Cannot open YAML configuration file '{}'".format(self._yaml))
                return False
    
        validate_props = False
        if CONFIG_DEVICE in yaml_device:
            ac = yaml_device.get(CONFIG_DEVICE, {})
            validate_props = ac.get(CONFIG_DEVICE_VALIDATE_PROPS, False)
            self._logger.info("Validate properties: {} ({})".format(validate_props, ac.get(CONFIG_DEVICE_VALIDATE_PROPS, False)))
            connection_node = ac.get(CONFIG_DEVICE_CONNECTION, {})
            connection = create_connection(connection_node, self._config, self._logger)
            
            if connection is None:
                self._logger.error("Cannot create connection object!")
                return False

            self._state_getter = create_status_getter('state', ac.get(CONFIG_DEVICE_STATUS, {}), connection)
            if self._state_getter == None:
                self._logger.error("Missing 'state' configuration node")
                return False

            nodes = ac.get(CONFIG_DEVICE_OPERATIONS, {})
            for op_key in nodes.keys():
                op = create_property(op_key, nodes[op_key], connection)
                if op is not None:
                    self._operations[op.id] = op
                    self._service_schema_map[vol.Optional(op.id)] = op.config_validation_type

            nodes = ac.get(CONFIG_DEVICE_ATTRIBUTES, {})
            for key in nodes.keys():
                prop = create_property(key, nodes[key], connection)
                if prop is not None:
                    self._properties[prop.id] = prop

            self._name = ac.get(ATTR_NAME, CONST_CONTROLLER_TYPE)
            self._friendly_name = ac.get(CONFIG_DEVICE_FRIENDLY_NAME, None)

        self.update_state()

        if validate_props:
            ops = {}
            device_state = self._state_getter.value
            for op in self._operations.values():
                if op.is_valid(device_state):
                    ops[op.id] = op
                else:
                    self._logger.info("Removing invalid operation '{}'".format(op.id))
                self._operations = ops
            ops = {}

        for f in SUPPORTED_FEATURES_MAP.keys():
            self._supported_features |= (SUPPORTED_FEATURES_MAP[f] if self.get_property(f) is not None else 0)
        
        return ((len(self._operations) + len(self._properties)) > 0)

    @staticmethod
    def match_type(type):
        return str(type).lower() == CONST_CONTROLLER_TYPE

    @property
    def name(self):
        device_name = self.get_property(ATTR_NAME)
        return device_name if device_name is not None else self._name

    @property
    def friendly_name(self):
        return self._friendly_name
        
    @property
    def debug(self):
        return self._debug
        
    def update_state(self):
        debug = self._debug
        if self._state_getter is not None:
            self._state_getter.update_state(self._state_getter.value, debug)
            device_state = self._state_getter.value
            self._attributes = { ATTR_NAME : self.name }
            if debug:
                self._attributes.update(self._state_getter.state_attributes)
            for op in self._operations.values():
                op.update_state(device_state, debug)
                self._attributes.update(op.state_attributes)
            for prop in self._properties.values():
                prop.update_state(device_state, debug)
                self._attributes.update(prop.state_attributes)

    def set_property(self, property_name, new_value):
        print("SETTING UP property {} to {}".format(property_name, new_value))
        op = self._operations.get(property_name, None)
        if op is not None:
            result = op.set_value(new_value)
            print("SETTING UP property {} to {} -> FINISHED with result {}".format(property_name, new_value, result))
            return result
        print("SETTING UP property {} to {} -> FAILED - wrong property".format(property_name, new_value))
        return False

    def get_property(self, property_name):
        if property_name in self._operations:
            return self._operations[property_name].value
        if property_name in self._properties:
            return self._properties[property_name].value
        return None

    @property
    def state_attributes(self):
        return self._attributes

    @property
    def temperature_unit(self):
        unit = UNIT_MAP.get(self.get_property(CONF_TEMPERATURE_UNIT), None)
        return unit if unit is not None else self._temp_unit

    @property
    def is_on(self):
        state = self.get_property(ATTR_POWER)
        return state == STATE_ON if state is not None else None

    @property
    def supported_features(self):
        return self._supported_features

    @property
    def service_schema_map(self):
        return self._service_schema_map
