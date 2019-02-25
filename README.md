# Samsung AC device for HASS
My implementation of ClimateDevice for controlling Samsung AC unit

## Configuration
1. Get your device token ([This](https://community.home-assistant.io/t/samsung-ac/11747/5) is a good place to start)
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
* Power on/off
* Set/get target/min/max temperatures
* Set/get swing direction
* Set/get fan level
* Set/get fan maximum level
* Read current indoor temperature
* Read device configuration
## TO DO
* Implement service for
   * Select special operation mode
   * Turn on/off Purify mode
   * Turn on/off Clean mode
   * Turn on Good Sleep mode
* Read sw/fw version
* Implement device_info node
