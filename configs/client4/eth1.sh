ip link add link eth1 name eth1.10 type vlan id 10 
ifconfig eth1 down
ifconfig eth1 up
