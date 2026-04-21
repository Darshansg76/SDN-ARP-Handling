# SDN ARP Controller using Ryu

## Overview

This project implements an ARP handling mechanism using Software Defined Networking (SDN) with the Ryu controller.
The controller centrally manages ARP resolution using proxy ARP, reducing broadcast overhead and improving efficiency.

---

## Architecture

Hosts (h1, h2, h3) → OpenFlow Switch (s1) → Ryu Controller

---

## Features

* Proxy ARP (controller-generated ARP replies)
* IP to MAC learning (ARP table)
* MAC to Port learning (learning switch behavior)
* Dynamic flow rule installation
* Reduced broadcast traffic
* Flow timeout handling

---

## Technologies Used

Python, Ryu SDN Controller, Mininet, OpenFlow Protocol

---

## How to Run

```bash
source ryu_env/bin/activate
ryu-manager --ofp-tcp-listen-port 6653 arp_controller.py

# open new terminal
sudo mn -c
sudo mn --topo single,3 --controller remote

# inside mininet
pingall
dpctl dump-flows
```

---

## Expected Output

* 0% packet loss in pingall
* ARP learning logs in controller
* Proxy ARP replies
* Flow rules installed dynamically

---

## Performance Insight

The first packet is processed by the controller, after which flow rules are installed in the switch.
Subsequent packets are forwarded directly, reducing latency and controller load.

---

## Project Structure

arp-project/
├── arp_controller.py
├── README.md
└── screenshot-sdn/

---

## Author

Darshan Govekar
