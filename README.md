# SR Linux/SROS Streaming Telemetry Lab

SR Linux has first-class Streaming Telemetry support thanks to 100% YANG coverage of state and config data. The wholistic coverage enables SR Linux users to stream **any** data off of the NOS with on-change, sample, or target-defined support. A discrepancy in visibility across APIs is not about SR Linux.

The Nokia Service Router Operating System (SR OS) is robust and scalable OS and provides the foundation of Nokia's comprehensive portfolio of physical and virtualized routers. Provides Streaming Telemetry based on the OpenConfig gnmi.proto and the proprietary NOKIA SR OS YANG data models suporting sample, target-defined, on-change telemetry based on dial-in or dial-out calls.

This lab is a small augmentation of the original srl-telemetry-lab <https://github.com/srl-labs/srl-telemetry-lab> wich basically represents a small Clos fabric with [Nokia SR Linux](https://learn.srlinux.dev/) switches running as containers and a DC gateways layer composed by [Nokia SROS](https://www.nokia.com/networks/technologies/service-router-operating-system/) DC Gateways on a containerized vSIM image connected through a "tc mirred function" that is very well described in the @hellt forum (https://netdevops.me/2021/transparently-redirecting-packetsframes-between-interfaces/). The lab topology consists of a Clos/DCI, plus a Streaming Telemetry stack comprised of gnmic, prometheus and grafana applications.

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
clab deploy
```

Once the lab is completed, it can be removed with the destroy command.

```bash
# destroy a lab
clab destroy
```

## Accessing the network elements

Once the lab has been deployed, the different SR Linux/SROS nodes can be accessed via SSH through their management IP address, given in the summary displayed after the execution of the deploy command. It is also possible to reach those nodes directly via their hostname, defined in the topology file. Linux clients cannot be reached via SSH, as it is not enabled, but it is possible to connect to them with a docker exec command.

```bash
# reach a SR Linux leaf, spine or a dcgw via SSH
ssh admin@leaf1
ssh admin@spine1
ssh admin@dcgw1

# reach a Linux client via Docker
docker exec -it client1 bash
```

## Fabric configuration

The DC fabric used in this lab consists of three leaves, two spines and two DC gateways interconnected with each other as shown in the diagram.

![pic1](https://user-images.githubusercontent.com/86619221/205601635-609eb772-833b-4ac9-b2ab-dc3ed661c4a1.JPG)

Leaves and spines use Nokia SR Linux IXR-D2 and IXR-D3L chassis respectively, DC gateways uses SR-1 chassis. Each network element of this topology is equipped with a [Fabric startup configuration file](configs/fabric) and [DCI startup configuration file](configs/dci) that is applied at the node's startup.

Once booted, network nodes will come up with interfaces, underlay protocols and overlay service configured. The fabric is configured with Layer 2 EVPN service between the leaves and DC gateways.

### Verifying the underlay and overlay status

The underlay network is provided by eBGP, and the overlay network, by iBGP. By connecting via SSH to one of the leaves, it is possible to verify the status of those BGP sessions.

```
A:leaf1# show network-instance protocols bgp neighbor  
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
BGP neighbor summary for network-instance "default"
Flags: S static, D dynamic, L discovered by LLDP, B BFD enabled, - disabled, * slow
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
+-----------------------+----------------------------------+-----------------------+--------+------------+-------------------+-------------------+-----------------+----------------------------------+
|       Net-Inst        |               Peer               |         Group         | Flags  |  Peer-AS   |       State       |      Uptime       |    AFI/SAFI     |          [Rx/Active/Tx]          |
+=======================+==================================+=======================+========+============+===================+===================+=================+==================================+
| default               | 10.0.2.1                         | iBGP-overlay          | S      | 100        | established       | 0d:0h:53m:57s     | evpn            | [4/4/1]                          |
| default               | 10.0.2.2                         | iBGP-overlay          | S      | 100        | established       | 0d:0h:53m:57s     | evpn            | [4/0/1]                          |
| default               | 192.168.11.1                     | eBGP                  | S      | 201        | established       | 0d:0h:54m:2s      | ipv4-unicast    | [5/5/2]                          |
| default               | 192.168.12.1                     | eBGP                  | S      | 201        | established       | 0d:0h:54m:2s      | ipv4-unicast    | [5/5/6]                          |
+-----------------------+----------------------------------+-----------------------+--------+------------+-------------------+-------------------+-----------------+----------------------------------+
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
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
               100        136    0 00h52m38s 4/3/1 (Evpn)
                          115    0           
10.0.2.2
               100        137    0 00h53m02s 4/0/1 (Evpn)
                          116    0           
192.168.41.0
               201        116    0 00h53m45s 5/4/1 (IPv4)
                          114    0           
192.168.41.2
               201        116    0 00h53m55s 5/4/1 (IPv4)
                          113    0           
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

* `bash traffic.sh stop all` - stop traffic generation between all nodes
* `bash traffic.sh stop 1-2` - stop traffic generation between client1 and client2
* `bash traffic.sh stop 1-3` - stop traffic generation between client1 and client3
* `bash traffic.sh stop 4-6` - stop traffic generation between client4 and client6
* `bash traffic.sh stop 5-6` - stop traffic generation between client5 and client6

## Telemetry stack

As the lab name suggests, telemetry is at its core. The following stack of software solutions has been chosen for this lab:

| Role                | Software                              |
| ------------------- | ------------------------------------- |
| Telemetry collector | [gnmic](https://gnmic.openconfig.net) |
| Time-Series DB      | [prometheus](https://prometheus.io)   |
| Visualization       | [grafana](https://grafana.com)        |

## Grafana

Grafana is a key component of this lab. Lab's topology file includes grafana node along with its configuration parameters such as dashboards, datasources and required plugins.

Grafana dashboard provided by this repository provides multiple views on the collected real-time data. Powered by [flowchart plugin](https://grafana.com/grafana/plugins/agenty-flowcharting-panel/) it overlays telemetry sourced data over graphics such as topology and front panel views:

![pic3](https://user-images.githubusercontent.com/86619221/205601697-bd5b68f0-e2c6-49d3-a1f3-1cb5b67b34d9.JPG)

Using the flowchart plugin and real telemetry data users can create interactive topology maps (aka weathermap) with a visual indication of link rate/utilization.

![pic2](https://user-images.githubusercontent.com/86619221/205601728-f3b254d1-2b03-4e75-b0e4-eb89cf54789a.JPG)

## Access details

* Grafana: <http://localhost:3000>. Built-in user credentials: `admin/admin`
* Prometheus: <http://localhost:9090/graph>
