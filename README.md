# Climate_IP - IP based climate device for Home Assistant
Implementation of ClimateDevice for controlling IP based AC units.
This component is able to work with any AC unit which can be controlled with REST API.
At this moment it is configured to work with:
* Samsung AC units available at port 8888 (new generation, REST API)
* Samsung AC units available at port 2878 (old generation, socket communication)

Support for any unit working with REST API can be easily added via YAML configuration file.

## Installation
1. Create folder <ha_configuration_folder>/custom_components/__climate_ip__
2. Download all files from repo to newly created folder
3. In __configuration.yaml__ file add section:
    1. For new generation units (REST API, port 8888)
        >     climate:
        >     - platform: climate_ip
        >       config_file: '<ha_configuration_folder>/custom_components/climate_ip/samsungrac.yaml'
    2. For old generation units:
        >     climate:
        >     - platform: climate_ip
        >       config_file: '<ha_configuration_folder>/custom_components/climate_ip/samsung_2878.yaml'
## Configuration
You need to have your device __token__. Please use google to find a way to get it :-) 
1. For new generation units (REST API, port 8888) edit __samsungrac.yaml__ configuration file to meet your settings:
    1. Replace "__ TOKEN__" string with your device __token__
    2. Replace "__ IP__ADDRESS__" string with your device IP address
2. For old generation units edit __samsung_2878.yaml__ configuration to meet your settings:
    1. Set IP address of your device using __host__ parameter
    2. Set device token using __token__ parameter
    3. Set device MAC address using __mac__ parameter
    4. Set path to certificate file using __cert__ parameter -  remove this parameter to connect with device without certificate validation
3. YAML configuration
You can easily add, remove or modify any device paramter to meet device capabilities.
I hope that more detailed specification will be created *soon* :-D

## YAML configuration file syntax
TO DO
## Functionality
Functionality depends on yaml configuration file and can be easily changed by editing those files. Currently configuration provides:
1. For new generation units (REST API, port 8888)
    * turn device on and off
    * sets and reads target/min/max temperatures
    * sets and reads swing direction
    * sets and reads fan level
    * sets and reads fan maximum level
    * sets and reads special mode (2Step, Comfort, Quiet etc)
    * sets and reads good sleep mode
    * turn purify mode on and off
    * turn auto clean mode on and off
    * turn beep mode on and off
    * read current indoor temperature
    * read device configuration
1. For old generation units 
    * turn device on and off
    * sets and reads target temperature
    * sets and reads swing direction (if supported)
    * sets and reads fan level (if supported)
    * sets and reads special mode (Comfort, Quiet etc)
    * turn purify mode on and off (if supported)
    * turn auto clean mode on and off (if supported)
    * read current indoor temperature
    * read device configuration
## Using
### Default functionality
This component implements Home Assistant ClimateDevice class. Functionality enabled in HA by default:
* turn device on/off
* select fan mode
* select swing mode
* select target temperatures (min, max and target)
### Device specific functions
Device specific functionality is added as extra service called **climate.climate_ip_samsungrac_set_property**.
Every device attribute can be set using this service with proper params.

```
{
  "entity_id" : "climate.salon_ac",
  "power" : "on",
  "purify" : "on",
  "special_mode" : "comfort"
}
```
### Switches for special functions
To make controllig device as easy as possible user can create template switches for operations defined as __Switch__ (please see configuration file). 
Below is an example of template switch for Purify option
```
switch:
  - platform: template
    switches:
      purify:
        friendly_name: "AC Purifier"
        value_template: "{{ is_state_attr('climate.salon_ac', 'purify', 'on') }}"
        turn_on:
          service: climate.climate_ip_samsungrac_set_property
          data:
            entity_id: climate.salon_ac
            purify: 'on'
        turn_off:
          service: climate.climate_ip_samsungrac_set_property
          data:
            entity_id: climate.salon_ac
            purify: 'off'
```
# References
 * [Samsung protocol description](https://community.openhab.org/t/newgen-samsung-ac-protocol/33805)
 * [HA forum](https://community.home-assistant.io/t/samsung-ac/11747/11)
 
## TODO
Documentation...
