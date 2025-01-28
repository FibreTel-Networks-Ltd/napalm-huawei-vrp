from napalm.base.base import NetworkDriver
from collections import defaultdict
import re

class VRPDriver(NetworkDriver):
    def __init__(self, hostname, username, password, timeout=60, optional_args=None):
        if optional_args is None:
            optional_args = {}
        self.hostname = hostname
        self.username = username
        self.password = password
        self.timeout = timeout
        self.optional_args = optional_args
        self.device = None  # Placeholder for the device connection

    def open(self):
        # Implement connection to the device
        print(f"Connecting to {self.hostname}...")
        pass

    def close(self):
        # Implement closing the connection to the device
        print("Closing connection...")
        pass

    def run_command(self, command):
        # Mock the output of running a command on the device
        print(f"Running command: {command}")
        # Replace this with actual device command execution
        return ""

    def get_bgp_neighbors(self):
        """
        Fetch and return BGP neighbor information, including IPv4, IPv6, and VRF-specific peers.
        """
        bgp_neighbors = defaultdict(lambda: dict(peers={}))

        # Commands to fetch data
        commands = {
            "ipv4": "display bgp peer",
            "ipv6": "display bgp ipv6 peer",
            "vpnv4": "display bgp vpnv4 all peer",
            "vpnv6": "display bgp vpnv6 all peer",
        }

        # Fetch and parse data for each AFI
        for afi, command in commands.items():
            output = self.run_command(command)
            if not output:
                continue

            # Parse the output
            for line in output.splitlines():
                match = re.search(
                    r"(?P<peer_ip>[\d.:]+)\s+\d+\s+(?P<remote_as>\d+).*?"
                    r"(?P<state>Established).*?(?P<prefixes>\d+)",
                    line,
                )
                if match:
                    peer_ip = match.group("peer_ip")
                    remote_as = int(match.group("remote_as"))
                    state = match.group("state") == "Established"
                    prefixes = int(match.group("prefixes"))

                    # Enrich with verbose data if available
                    verbose_output = self.run_command(f"display bgp peer {peer_ip} verbose")
                    description = re.search(r'Peer\'s description: \"(.*)\"', verbose_output)
                    remote_id = re.search(r"Remote router ID\s+([\d.]+)", verbose_output)
                    uptime = re.search(r"Up for (?P<uptime>[\dhms]+)", verbose_output)

                    bgp_neighbors["global"]["peers"][peer_ip] = {
                        "remote_as": remote_as,
                        "remote_id": remote_id.group(1) if remote_id else "",
                        "is_up": state,
                        "is_enabled": True,  # Assume peers are enabled unless Admin down is found
                        "description": description.group(1) if description else "",
                        "uptime": self.convert_uptime(uptime.group("uptime")) if uptime else 0,
                        "address_family": {
                            afi: {
                                "received_prefixes": prefixes,
                                "accepted_prefixes": prefixes,
                                "sent_prefixes": 0,  # Default to 0 for sent prefixes
                            }
                        },
                    }

        return dict(bgp_neighbors)

    def convert_uptime(self, uptime_str):
        match = re.match(r"(?:(\d+)d)?(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?", uptime_str)
        if not match:
            return 0
        days, hours, minutes, seconds = match.groups(default="0")
        return int(days) * 86400 + int(hours) * 3600 + int(minutes) * 60 + int(seconds)

    def get_bgp_neighbors_detail(self, neighbor_address=""):
        """
        Return detailed BGP neighbor information.
        If neighbor_address is specified, only return details for that neighbor.
        """
        verbose_output = self.run_command("display bgp peer verbose")

        verbose_regex = (
            r"BGP Peer is (?P<peer>[\d.:]+),\s+remote AS (?P<remote_as>\d+).*?"
            r"Peer's description: \"(?P<description>[^\"]*)\".*?"
            r"Remote router ID (?P<remote_id>[\d.]+).*?"
            r"BGP current state: Established, Up for (?P<uptime>[\dhms]+).*?"
            r"Received total routes: (?P<accepted_prefixes>\d+).*?"
            r"Advertised total routes: (?P<sent_prefixes>\d+)"
        )

        bgp_neighbors_detail = defaultdict(list)

        for match in re.finditer(verbose_regex, verbose_output, re.DOTALL):
            peer = match.group("peer")
            remote_as = int(match.group("remote_as"))
            description = match.group("description")
            remote_id = match.group("remote_id")
            uptime = self.convert_uptime(match.group("uptime"))
            sent_prefixes = int(match.group("sent_prefixes"))
            accepted_prefixes = int(match.group("accepted_prefixes"))

            if neighbor_address and peer != neighbor_address:
                continue

            bgp_neighbors_detail["global"].append({
                "remote_as": remote_as,
                "remote_id": remote_id,
                "description": description,
                "is_up": True,
                "uptime": uptime,
                "address_family": {
                    "ipv4": {
                        "sent_prefixes": sent_prefixes,
                        "accepted_prefixes": accepted_prefixes,
                        "received_prefixes": accepted_prefixes,
                    }
                }
            })

        return dict(bgp_neighbors_detail)
