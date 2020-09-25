DOMAIN = "climate_ip"

from .connection_request import ConnectionRequest, ConnectionRequestPrint
from .controller_yaml import YamlController
from .properties import (
    GetJsonStatus,
    ModeOperation,
    NumericOperation,
    SwitchOperation,
    TemperatureOperation,
)
from .samsung_2878 import ConnectionSamsung2878
