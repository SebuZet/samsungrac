[![](https://img.shields.io/github/release/atxbyea/samsungrac/all.svg?style=for-the-badge)](https://github.com/atxbyea/samsungrac/releases)
[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg?style=for-the-badge)](https://github.com/custom-components/hacs)
[![](https://img.shields.io/badge/MAINTAINER-%40atxbyea?style=for-the-badge)](https://github.com/atxbyea)
[![](https://img.shields.io/badge/COMMUNITY-FORUM-success?style=for-the-badge)](https://community.home-assistant.io)


# Installation (There are two methods, with HACS or manual)

### 1. Easy Mode

We support [HACS](https://hacs.xyz/). Go to "HACS", then "Integrations" search "samsungrac" and install.

### 2. Manual

Install it as you would do with any homeassistant custom component:

1. Download `custom_components` folder.
2. Copy the `climate_ip` direcotry within the `custom_components` directory of your homeassistant installation. 
The `custom_components` directory resides within your homeassistant configuration directory.
**Note**: if the custom_components directory does not exist, you need to create it.
After a correct installation, your configuration directory should look like the following.

    ```
    └── ...
    └── configuration.yaml
    └── custom_components
        └── climate_ip


See GitHub for additional instructions and release notes
