echo 'Enabling Configuration Snapshots...'
aws configservice stop-configuration-recorder --configuration-recorder-name default
aws configservice put-delivery-channel --delivery-channel file://config_delivery_channel.json
aws configservice start-configuration-recorder --configuration-recorder-name default
echo 'Done!'