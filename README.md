# ARP Handling in SDN Networks using Ryu Controller

## Student Details
- Name: Darshan S Govekar  
- SRN: PES1UG24AM355  

---

## Project Overview
This project demonstrates ARP (Address Resolution Protocol) handling in a Software Defined Network (SDN) using the Ryu controller and Mininet emulator.

In traditional networks, ARP requests are broadcast and handled locally. In this project, a centralized SDN controller intercepts ARP packets and applies custom logic to control communication between hosts.

---

## Objective
- Understand ARP in SDN
- Implement packet interception using Ryu
- Apply match-action rules
- Demonstrate policy-based blocking

---

## Tools Used
- Mininet
- Ryu Controller
- OpenFlow
- Ubuntu Linux

---

## Network Topology
- 1 Switch (s1)
- 3 Hosts:
  - h1 → 10.0.0.1  
  - h2 → 10.0.0.2  
  - h3 → 10.0.0.3  

---

## Working
1. Host sends ARP request
2. Switch forwards packet to controller
3. Controller intercepts ARP
4. Applies rule:
   - Allow OR
   - Block

---

## Scenarios

### Scenario 1: Normal
- No blocking
- Result: 0% packet loss

### Scenario 2: Blocking
- Block: 10.0.0.1 → 10.0.0.2
- Result: Partial packet loss (~33%)

---

## How to Run

### Start Controller
```bash
source ryu-env/bin/activate
ryu-manager arp_controller.py
