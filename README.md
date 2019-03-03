# Samsung AC device for Home Assistant
My implementation of ClimateDevice for controlling Samsung AC unit

## WARNING
Home Assistant (v. 0.89) introduced many changes in components file structure. Since version 1.1.0 this component requires HA in version >= 0.89.

## Configuration
1. get your device token ([this](https://community.home-assistant.io/t/samsung-ac/11747/5) is a good place to start)
2. download all files to folder \<HASS configuration folder\>/custom_components/samsungrac/
3. add configuration section to you configuration.yaml file:

Configuration params:

| Param name        | description           |
| ------------- |-------------|
| host      | Device address including schema and port (e.g. https://192.178.1.200:8888) |
| access_token           | Access token to the device        |
| cert_file   | Path to certificate file   |
| temperature_unit      | Temperature unit ("C"/"F"). Used only if device doesn't report this value. Default: "C" |
| extra_off_mode    | True if user wants to add 'virtual' OFF mode. Default: False WORK IN PORGRESS   |
| debug      | Enable/disable more debugs. Default: False |

Configuration example:
```
climate:
  - platform: samsungrac
    host: https://192.178.1.200:8888
    access_token: axdbYtrsdf
    cert_file: /config/custom_components/samsungrac/ac14k_m.pem
```
## Functionality
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
## Using
This component implements Home Assistant ClimateDevice class. Samsung device specific functionality is added as extra service called '**set_custom_mode**'.
### Functionality enabled in HA by default:
* turn device on/off
* select fan mode
* select swing mode
* select target temperatures (min, max and target)
### Functionality available through set_custom_mode service
All modes (except temperatures) can be changed through **set_custom_mode** service.
To change mode **set_custom_mode** service must be called with dedicated params.

List of available params:

| Param name        | Values           | example   |
| ------------- |:-------------:| -----:|
| entity_id      | device id to work on | climate.samsung_rac |
| mode           | heat/cool/dry/fan_only/auto | auto        |
| special_mode   | off/sleep/speed/2step/comfort/quiet/smart      | comfort   |
| purify      | on/off      |   on |
| auto_clean    | on/off      |    off |
| good_sleep   | 1 to 24 (increments of 30 mins)      |    2 |
| fan_mode    | auto/low/medium/high/turbo      |    auto |
| fan_mode_max   | auto/low/medium/high/turbo      |    auto |
| swing_mode   | all/vertical/horizontal/fix      |    all |
| power   | on/off      |    off |
| beep      | on/off      |   on |
| debug      | 0/1      |   0 |

Service can be called with any parameter subset. For example:

```
{
"entity_id" : "climate.samsung_rac",
"power" : "on",
"purify" : "on",
"special_mode" : "comfort"
}
```
### Switches for special functionalities
To make controllig device as easy as possible user can create template switches for options like Purify, Power, Beep, Auto Clean. 
Below is an example of template switch for Purify option
```
switch:
  - platform: template
    switches:
      purify:
        friendly_name: "AC Purifier"
        value_template: "{{ is_state_attr('climate.samsung_rac', 'purify', 'on') }}"
        turn_on:
          service: climate.set_custom_mode
          data:
            entity_id: climate.samsung_rac
            purify: 'on'
        turn_off:
          service: climate.set_custom_mode
          data:
            entity_id: climate.samsung_rac
            purify: 'off'
```
# References
 * [Samsung protocol description](https://community.openhab.org/t/newgen-samsung-ac-protocol/33805)
 * [HA forum](https://community.home-assistant.io/t/samsung-ac/11747/11)
 
## TODO
* Read sw/fw version
* Implement device_info node
