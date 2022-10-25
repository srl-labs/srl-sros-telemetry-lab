# SR Linux/SROS Streaming Telemetry Lab
SR Linux has first-class Streaming Telemetry support thanks to 100% YANG coverage of state and config data. The wholistic coverage enables SR Linux users to stream **any** data off of the NOS with on-change, sample, or target-defined support. A discrepancy in visibility across APIs is not about SR Linux.

The Nokia Service Router Operating System (SR OS) is robust and scalable OS and provides the foundation of Nokia's comprehensive portfolio of physical and virtualized routers. Provides Streaming Telemetry based on the OpenConfig gnmi.proto and the proprietary NOKIA SR OS YANG data models suporting sample, target-defined, on-change telemetry based on dial-in or dial-out calls.

This lab is a small augmentation of the original srl-telemetry-lab https://github.com/srl-labs/srl-telemetry-lab wich basically represents a small Clos fabric with [Nokia SR Linux](https://learn.srlinux.dev/) switches running as containers and a DC gateways layer composed by [Nokia SROS](https://www.nokia.com/networks/technologies/service-router-operating-system/) DC Gateways on a containerized vSIM image connected through an ovs-bridge. The lab topology consists of a Clos/DCI, plus a Streaming Telemetry stack comprised of gnmic, prometheus and grafana applications.


Goals of this lab:

1. Demonstrate how a telemetry stack can be incorporated into the same clab topology file.
2. Explain SR Linux wholistic telemetry support.
3. Demonstrate SR Linux and SROS interoperability in the DC Fabric.
4. Explain what a SROS based telemetry subscription is. 
5. Provide practical configuration examples for the gnmic collector to subscribe to fabric nodes and export metrics to Prometheus TSDB.
6. Introduce advanced Grafana dashboarding with FlowChart plugin rendering port speeds and statuses.

## Deploying the lab
The lab is deployed with [containerlab](https://containerlab.dev) project where [`st.clab.yml`](st.clab.yml) file declaratively describes the lab topology.

```bash
# deploy a lab
containerlab deploy -t st.clab.yml
```

Once the lab is completed, it can be removed with the destroy command.

```bash
# destroy a lab
containerlab destroy -t st.clab.yml
```

## Accessing the network elements
Once the lab has been deployed, the different SR Linux/SROS nodes can be accessed via SSH through their management IP address, given in the summary displayed after the execution of the deploy command. It is also possible to reach those nodes directly via their hostname, defined in the topology file. Linux clients cannot be reached via SSH, as it is not enabled, but it is possible to connect to them with a docker exec command.

```bash
# reach a SR Linux leaf or a spine via SSH
ssh admin@leaf1
ssh admin@spine1

# reach a Linux client via Docker
docker exec -it client1 bash
```

## Fabric configuration
The DC fabric used in this lab consists of three leaves, two spines and two DC gateways interconnected with each other as shown in the diagram.

![pic2](https://gitlabe2.ext.net.nokia.com/mpaz/srl-sros-telemetry-lab/-/wikis/uploads/c9fd0d4f61d9e99fb77f1ec97f64888f/Topology.JPG)

Leaves and spines use Nokia SR Linux IXR-D2 and IXR-D3L chassis respectively, DC gateways uses SR-1 chassis. Each network element of this topology is equipped with a [startup configuration file](configs/fabric/) that is applied at the node's startup.

Once booted, network nodes will come up with interfaces, underlay protocols and overlay service configured. The fabric is configured with Layer 2 EVPN service between the leaves and DC gateways.

### Verifying the underlay and overlay status
The underlay network is provided by eBGP, and the overlay network, by iBGP. By connecting via SSH to one of the leaves, it is possible to verify the status of those BGP sessions.

```
A:leaf1# show network-instance default protocols bgp neighbor
------------------------------------------------------------------------------------------------------------------
BGP neighbor summary for network-instance "default"
Flags: S static, D dynamic, L discovered by LLDP, B BFD enabled, - disabled, * slow

+-----------+---------------+---------------+-------+----------+-------------+--------------+--------------+---------------+
| Net-Inst  |     Peer      |     Group     | Flags | Peer-AS  |   State     |    Uptime    |   AFI/SAFI   | Rx/Active/Tx] |
+===========+===============+===============+=======+==========+=============+==============+==============+===============+
| default   | 10.0.2.1      | iBGP-overlay  | S     | 100      | established | 0d:0h:0m:27s | evpn         | [4/4/2]       |
| default   | 10.0.2.2      | iBGP-overlay  | S     | 100      | established | 0d:0h:0m:28s | evpn         | [4/0/2]       |
| default   | 192.168.11.1  | eBGP          | S     | 201      | established | 0d:0h:0m:34s | ipv4-unicast | [3/3/2]       |
| default   | 192.168.12.1  | eBGP          | S     | 202      | established | 0d:0h:0m:33s | ipv4-unicast | [3/3/4]       |
+-----------+---------------+---------------+-------+----------+-------------+--------------+--------------+---------------+
```

By connecting via SSH is also possible to one of the DC gateways verify the stats of those BGP sesions from the SROS perspective.

```
A:admin@dcgw1# show router bgp summary | match Summary post-lines 20
BGP Summary
===============================================================================
Legend : D - Dynamic Neighbor
===============================================================================
Neighbor
Description
                   AS PktRcvd InQ  Up/Down   State|Rcv/Act/Sent (Addr Family)
                      PktSent OutQ
-------------------------------------------------------------------------------
10.0.2.1
               100         28    0 00h00m51s 9/7/2 (Evpn)
                           22    0           
10.0.2.2
               100         27    0 00h00m42s 9/0/2 (Evpn)
                           22    0           
192.168.41.0
               201         29    0 00h00m45s 6/4/1 (IPv4)
                           25    0           
192.168.41.2
               202         30    0 00h00m30s 6/1/1 (IPv4)
                           24    0           
```

## Running traffic
To run traffic between the nodes, leverage `traffic.sh` control script.

To start the traffic:

* `bash traffic.sh start all` - start traffic between all nodes
* `bash traffic.sh start 1-2` - start traffic between client1 and client2
* `bash traffic.sh start 1-3` - start traffic between client1 and client3
* `bash traffic.sh start 4-6` - start traffic between client4 and client6
* `bash traffic.sh start 5-6` - start traffic between client5 and client6

To stop the traffic:

* `bash traffic.sh stop` - stop traffic generation between all nodes
* `bash traffic.sh stop 1-2` - stop traffic generation between client1 and client2
* `bash traffic.sh stop 1-3` - stop traffic generation between client1 and client3
* `bash traffic.sh stop 4-6` - stop traffic generation between client4 and client6
* `bash traffic.sh stop 5-6` - stop traffic generation between client5 and client6

## Telemetry stack
As the lab name suggests, telemetry is at its core. The following stack of software solutions has been chosen for this lab:

| Role                | Software                            |
| ------------------- | ----------------------------------- |
| Telemetry collector | [gnmic](https://gnmic.kmrd.dev)     |
| Time-Series DB      | [prometheus](https://prometheus.io) |
| Visualization       | [grafana](https://grafana.com)      |

## Grafana
Grafana is a key component of this lab. Lab's topology file includes grafana node along with its configuration parameters such as dashboards, datasources and required plugins.

Grafana dashboard provided by this repository provides multiple views on the collected real-time data. Powered by [flowchart plugin](https://grafana.com/grafana/plugins/agenty-flowcharting-panel/) it overlays telemetry sourced data over graphics such as topology and front panel views:

![pic3](https://gitlabe2.ext.net.nokia.com/mpaz/srl-sros-telemetry-lab/-/wikis/uploads/b3fe760389b8a6cb4fe77e58ccf795ce/srl-sros-pannel-2.JPG)

Using the flowchart plugin and real telemetry data users can create interactive topology maps (aka weathermap) with a visual indication of link rate/utilization.

![pic2](https://gitlabe2.ext.net.nokia.com/mpaz/srl-sros-telemetry-lab/-/wikis/uploads/041ef2fd87ed8a8244b4222652d49b21/topology_with_traffic.JPG)

## Access details

* Grafana: http://localhost:3000
* Prometheus: http://localhost:9090/graph