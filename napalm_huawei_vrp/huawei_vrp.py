import re
from collections import defaultdict
from napalm.base import NetworkDriver

class VRPDriver(NetworkDriver):
    def __init__(self, hostname, username, password, timeout=60, optional_args=None):
        super().__init__(hostname, username, password, timeout, optional_args)

    def open(self):
        # Logic to open a connection to the device
        pass

    def close(self):
        # Logic to close the connection to the device
        pass

    def get_bgp_neighbors(self):
        bgp_neighbors = defaultdict(lambda: dict(peers={}))

        # Fetch command outputs
        output = self.cli(["display bgp peer"])["display bgp peer"]
        verbose_output = self.cli(["display bgp peer verbose"])["display bgp peer verbose"]

        # Regular expressions for parsing
        peer_regex = r"(?P<peer>[\d.:]+)\s+\d+\s+(?P<remote_as>\d+).*?Established.*?(?P<prefixes>\d+)"
        verbose_regex = (
        r"BGP Peer is (?P<peer>[\d.:]+),\s+remote AS (?P<remote_as>\d+).*?"
        r'Peer\'s description: "(?P<description>[^"]*)".*?'
        r"Remote router ID (?P<remote_id>[\d.]+).*?"
        r"BGP current state: Established, Up for (?P<uptime>[\dhms]+).*?"
        r"Received total routes: (?P<accepted_prefixes>\d+).*?"
        r"Advertised total routes: (?P<sent_prefixes>\d+)"
        )

        # Parse verbose output for additional details
        verbose_details = {}
        for match in re.finditer(verbose_regex, verbose_output, re.DOTALL):
            peer = match.group("peer")
            verbose_details[peer] = {
                "description": match.group("description"),
                "remote_id": match.group("remote_id"),
                "uptime": self.convert_uptime(match.group("uptime")),
            }

        # Parse BGP peers
        for match in re.finditer(peer_regex, output):
            peer = match.group("peer")
            remote_as = int(match.group("remote_as"))
            received_prefixes = int(match.group("prefixes"))

            # Enrich with verbose details if available
            verbose_data = verbose_details.get(peer, {})
            description = verbose_data.get("description", "")
            remote_id = verbose_data.get("remote_id", "")
            uptime = verbose_data.get("uptime", 0)

            bgp_neighbors["global"]["peers"][peer] = {
                "remote_as": remote_as,
                "remote_id": remote_id,
                "is_up": True,
                "is_enabled": True,
                "description": description,
                "uptime": uptime,
                "address_family": {
                    "ipv4": {
                        "sent_prefixes": 0,
                        "accepted_prefixes": received_prefixes,
                        "received_prefixes": received_prefixes,
                    }
                },
            }

        return dict(bgp_neighbors)

    def get_bgp_neighbors_detail(self):
        bgp_neighbors_detail = []
        output = self.cli(["display bgp peer verbose"])["display bgp peer verbose"]

        # Regular expression for parsing verbose BGP details
        verbose_regex = (
            r"BGP Peer is (?P<peer>[\d.:]+),\s+remote AS (?P<remote_as>\d+).*?"
            r"Peer's description: \"(?P<description>[^"]*)\".*?"
            r"Remote router ID (?P<remote_id>[\d.]+).*?"
            r"BGP current state: Established, Up for (?P<uptime>[\dhms]+).*?"
            r"Received total routes: (?P<accepted_prefixes>\d+).*?"
            r"Advertised total routes: (?P<sent_prefixes>\d+)"
        )

        # Parse verbose output
        for match in re.finditer(verbose_regex, output, re.DOTALL):
            bgp_neighbors_detail.append({
                "remote_as": int(match.group("remote_as")),
                "remote_id": match.group("remote_id"),
                "description": match.group("description"),
                "is_up": True,
                "uptime": self.convert_uptime(match.group("uptime")),
                "address_family": {
                    "ipv4": {
                        "sent_prefixes": int(match.group("sent_prefixes")),
                        "accepted_prefixes": int(match.group("accepted_prefixes")),
                        "received_prefixes": int(match.group("accepted_prefixes")),
                    }
                },
            })

        return bgp_neighbors_detail

    def get_ipv6_neighbors_table(self):
        ipv6_neighbors_table = []
        output = self.cli(["display ipv6 neighbors"])["display ipv6 neighbors"]

        # Regular expression for parsing IPv6 neighbors
        ipv6_regex = (
            r"(?P<ip>[a-fA-F0-9:]+)\s+(?P<mac>[a-fA-F0-9-]+)\s+"
            r"(?P<interface>\S+)\s+(?P<state>\S+)"
        )

        # Parse IPv6 neighbors
        for match in re.finditer(ipv6_regex, output):
            ipv6_neighbors_table.append({
                "interface": match.group("interface"),
                "mac": match.group("mac"),
                "ip": match.group("ip"),
                "age": -1.0,  # Age is not provided in Huawei's command output
                "state": match.group("state"),
            })

        return ipv6_neighbors_table

    def convert_uptime(self, uptime_str):
        match = re.match(r"(?:(\d+)d)?(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?", uptime_str)
        if not match:
            return 0
        days, hours, minutes, seconds = match.groups(default="0")
        return int(days) * 86400 + int(hours) * 3600 + int(minutes) * 60 + int(seconds)
