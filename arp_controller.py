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
        self.mac_table = {}

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        dp = ev.msg.datapath
        ofp = dp.ofproto
        parser = dp.ofproto_parser

        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofp.OFPP_CONTROLLER)]
        self.add_flow(dp, 0, match, actions)

    def add_flow(self, dp, priority, match, actions):
        parser = dp.ofproto_parser
        ofp = dp.ofproto

        inst = [parser.OFPInstructionActions(ofp.OFPIT_APPLY_ACTIONS, actions)]
        mod = parser.OFPFlowMod(datapath=dp, priority=priority,
                               match=match, instructions=inst)
        dp.send_msg(mod)

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

        dst = eth.dst
        src = eth.src
        dpid = dp.id

        self.mac_table.setdefault(dpid, {})
        self.mac_table[dpid][src] = in_port

        arp_pkt = pkt.get_protocol(arp.arp)
        if arp_pkt:
            print(f"\nARP: {arp_pkt.src_ip} → {arp_pkt.dst_ip}")

          
            if arp_pkt.src_ip == "10.0.0.1" and arp_pkt.dst_ip == "10.0.0.2":
              print("BLOCKED: 10.0.0.1 → 10.0.0.2")
              return 

        if dst in self.mac_table[dpid]:
            out_port = self.mac_table[dpid][dst]
        else:
            out_port = ofp.OFPP_FLOOD

        actions = [parser.OFPActionOutput(out_port)]

        if out_port != ofp.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst)
            self.add_flow(dp, 1, match, actions)

        out = parser.OFPPacketOut(datapath=dp,
                                 buffer_id=msg.buffer_id,
                                 in_port=in_port,
                                 actions=actions,
                                 data=msg.data)
        dp.send_msg(out)
