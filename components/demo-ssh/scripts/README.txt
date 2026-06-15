

scan PNET devices

sudo python3 pnet_scan.py eth1


DCP RESET 
sudo python3 pnet_set.py eth1  factory-reset

Set IP 
sudo python3 pnet_set.py eth1 fa:e4:a8:7e:c4:b6 set-ip 192.168.0.50 255.255.255.0 192.168.101.30

Set name
sudo python3 pnet_set.py eth1 fa:e4:a8:7e:c4:b6 set-name not-working

blink
sudo python3 pnet_set.py eth1 fa:e4:a8:7e:c4:b6 blink


ArpSpoofing