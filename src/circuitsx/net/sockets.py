'''


.. codeauthor:: mnl
'''
from circuits.net.sockets import UDPServer
import socket
import struct

class UDPMCastServer(UDPServer):
    '''
    classdocs
    '''

    def _create_socket(self):
        # Look up multicast group address in name server and find out IP version
        self._addrinfo = addrinfo = socket.getaddrinfo(self._bind[0], None)[0]

        # Create a socket
        sock = socket.socket(addrinfo[0], socket.SOCK_DGRAM)

        # Allow multiple copies of this program on one machine
        # (not strictly needed)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # Bind it to the port
        sock.bind(('', self._bind[1]))

        group_bin = socket.inet_pton(addrinfo[0], addrinfo[4][0])
        # Join group
        if addrinfo[0] == socket.AF_INET: # IPv4
            mreq = group_bin + struct.pack('=I', socket.INADDR_ANY)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        else:
            mreq = group_bin + struct.pack('@I', 0)
            sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_JOIN_GROUP, mreq)

        return sock

    def setTTL(self, ttl):
        # Set Time-to-live (optional)
        ttl_bin = struct.pack('@i', ttl)
        # Look up multicast group address in name server and find out IP version
        if self._addrinfo[0] == socket.AF_INET: # IPv4
            self._sock.setsockopt(socket.IPPROTO_IP, 
                                 socket.IP_MULTICAST_TTL, ttl_bin)
        else:
            self._sock.setsockopt(socket.IPPROTO_IPV6,
                                  socket.IPV6_MULTICAST_HOPS, ttl_bin)
    