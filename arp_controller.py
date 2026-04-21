from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, CONFIG_DISPATCHER, set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet, ethernet, arp
from ryu.lib.packet import ether_types


class ARPController(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(ARPController, self).__init__(*args, **kwargs)
        self.mac_table = {}   # dpid → {mac: port}
        self.arp_table = {}   # ip → mac

    # 🔹 Install default rule
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        dp = ev.msg.datapath
        ofp = dp.ofproto
        parser = dp.ofproto_parser

        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofp.OFPP_CONTROLLER, ofp.OFPCML_NO_BUFFER)]

        self.add_flow(dp, 0, match, actions)
        self.logger.info("Switch connected")

    # 🔹 Add flow rule
    def add_flow(self, dp, priority, match, actions):
        parser = dp.ofproto_parser
        ofp = dp.ofproto

        inst = [parser.OFPInstructionActions(ofp.OFPIT_APPLY_ACTIONS, actions)]

        mod = parser.OFPFlowMod(
            datapath=dp,
            priority=priority,
            match=match,
            instructions=inst,
            idle_timeout=30,
            hard_timeout=60
        )

        dp.send_msg(mod)

    # 🔹 Packet handler
    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):

        msg = ev.msg
        dp = msg.datapath
        ofp = dp.ofproto
        parser = dp.ofproto_parser
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)

        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            return

        src = eth.src
        dst = eth.dst
        dpid = dp.id

        # 🔹 MAC learning
        self.mac_table.setdefault(dpid, {})
        self.mac_table[dpid][src] = in_port

        # 🔹 ARP handling
        arp_pkt = pkt.get_protocol(arp.arp)

        if arp_pkt:
            src_ip = arp_pkt.src_ip
            dst_ip = arp_pkt.dst_ip

            self.logger.info(f"ARP: {src_ip} → {dst_ip}")

            # Learn mapping
            self.arp_table[src_ip] = src
            self.logger.info(f"Learned: {src_ip} → {src}")

            # 🔥 Proxy ARP
            if arp_pkt.opcode == arp.ARP_REQUEST:
                if dst_ip in self.arp_table:

                    self.logger.info(f"Proxy ARP reply for {dst_ip}")

                    reply = packet.Packet()

                    reply.add_protocol(ethernet.ethernet(
                        ethertype=ether_types.ETH_TYPE_ARP,
                        src=self.arp_table[dst_ip],
                        dst=src
                    ))

                    reply.add_protocol(arp.arp(
                        opcode=arp.ARP_REPLY,
                        src_mac=self.arp_table[dst_ip],
                        src_ip=dst_ip,
                        dst_mac=src,
                        dst_ip=src_ip
                    ))

                    reply.serialize()

                    out = parser.OFPPacketOut(
                        datapath=dp,
                        buffer_id=ofp.OFP_NO_BUFFER,
                        in_port=ofp.OFPP_CONTROLLER,
                        actions=[parser.OFPActionOutput(in_port)],
                        data=reply.data
                    )

                    dp.send_msg(out)
                    return

        # 🔹 Forwarding logic
        if dst in self.mac_table[dpid]:
            out_port = self.mac_table[dpid][dst]

            # ✅ ALWAYS install flow when destination known
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst)
            actions = [parser.OFPActionOutput(out_port)]
            self.add_flow(dp, 1, match, actions)

        else:
            out_port = ofp.OFPP_FLOOD
            actions = [parser.OFPActionOutput(out_port)]

        # 🔹 Send packet
        out = parser.OFPPacketOut(
            datapath=dp,
            buffer_id=msg.buffer_id,
            in_port=in_port,
            actions=actions,
            data=msg.data
        )

        dp.send_msg(out)
