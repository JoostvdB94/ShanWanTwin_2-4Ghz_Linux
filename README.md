# ShanWanTwin_2-4Ghz_Linux
Userspace script to split controller input for the Shanwan Wireless Twin controllers (2563:0555)


## Requirements
- Python (2.7)
- python-uinput module
  - Install using [pip](https://pip.pypa.io/en/stable/installing/#id7): `pip install python-uinput`
- Supported controller. Find using `dmesg` and applying a grep pattern `'(?<=2563:0555\.\d{4}: input,)\w{6}\d'`
   - Example (flags may differ on your grep install): `dmesg | grep -oP '(?<=2563:0555\.\d{4}: input,)\w{6}\d'`
