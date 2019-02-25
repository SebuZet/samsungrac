# Samsung AC device for HASS
My implementation of ClimateDevice for controlling Samsung AC unit

## Configuration
1. get your device token ([this](https://community.home-assistant.io/t/samsung-ac/11747/5) is a good place to start)
1. download file samsungrac.py to \<HASS configuration folder\>/custom_component/climate/
2. download cert file to \<HASS configuration folder\>/custom_component/climate/
3. add configuration section to you configuration.yaml file:
```
climate:
  - platform: samsungrac
    host: host
    access_token: device_token
    cert_file: path/to/cert/file
```
eg:
```
climate:
  - platform: samsungrac
    host: https://192.178.1.200:8888
    access_token: axdbYtrsdf
    cert_file: /config/ac14k_m.pem
```
## Functionality
* power on/off
* set/get target/min/max temperatures
* set/get swing direction
* set/get fan level
* set/get fan maximum level
* set/get special mode (2Step, Comfort, Quiet etc)
* set/get purify mode
* set/get auto clean mode
* set/get good sleep mode
* set/get beep mode
* read current indoor temperature
* read device configuration
## Using
This device implemets HA ClimateDevice.
### Functionality enabled in HA by default:
* turn device on/off
* select fan mode
* select swing mode
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

Service can be called with any parameter subset. For example:

```
{
"entity_id" : "climate.samsung_rac",
"power" : "on",
"purify" : "on",
"special_mode" : "comfort"
}
```

# References
 * [Samsung protocol description](https://community.openhab.org/t/newgen-samsung-ac-protocol/33805)
 * [HA forum](https://community.home-assistant.io/t/samsung-ac/11747/11)
 
## TODO
* Read sw/fw version
* Implement device_info node
