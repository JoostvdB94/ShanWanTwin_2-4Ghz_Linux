#!/bin/bash
HIDRAW_DEVICE=($(dmesg | grep -oP '(?<=2563:0555\.\d{4}: input,)\w{6}\d'))
SCRIPT_PATH=/opt/ShanWanTwin_2-4Ghz_Linux/shanwan-joystick.py

if [ -n "$HIDRAW_DEVICE" ]
        then
                for ((i=0; i<${#HIDRAW_DEVICE[*]}; i++));
                        do
                        echo "Found joystick on /dev/${HIDRAW_DEVICE[$i]}"
                        exec "sudo" "python" "$SCRIPT_PATH" "/dev/${HIDRAW_DEVICE[$i]}" &
                done
fi
