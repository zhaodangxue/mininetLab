from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import Node
from mininet.log import setLogLevel, info
from mininet.cli import CLI
import time
import os
 
class LinuxRouter( Node ):
    "A Node with IP forwarding enabled."
    def config( self, **params ):
        super( LinuxRouter, self).config( **params )
        # Enable forwarding on the router
        self.cmd( 'sysctl net.ipv4.ip_forward=1' )
 
    def terminate( self ):
        self.cmd( 'sysctl net.ipv4.ip_forward=0' )
        super( LinuxRouter, self ).terminate()
 
class NetworkTopo( Topo ):
    "A LinuxRouter connecting three IP subnets"
    def build( self, **_opts ):
        defaultIP1 = '10.0.3.10/24'  # IP address for r0-eth1
        defaultIP2 = '10.0.3.20/24' 
        defaultIP3 = '10.0.6.10/24'
        defaultIP4 = '10.0.6.20/24'
        router1 = self.addNode( 'r1', cls=LinuxRouter, ip=defaultIP1 )
        router2 = self.addNode( 'r2', cls=LinuxRouter, ip=defaultIP2 )
        router3 = self.addNode( 'r3', cls=LinuxRouter, ip=defaultIP3 )
        router4 = self.addNode( 'r4', cls=LinuxRouter, ip=defaultIP4 )
 
        h1 = self.addHost( 'h1', ip='10.0.1.100/24', defaultRoute='via 10.0.1.10') #define gateway
        h2 = self.addHost( 'h2', ip='10.0.2.100/24', defaultRoute='via 10.0.2.20')
        h3 = self.addHost( 'h3', ip='10.0.5.100/24', defaultRoute='via 10.0.5.50')
        h4 = self.addHost( 'h4', ip='10.0.7.100/24', defaultRoute='via 10.0.7.70')
 
        self.addLink(router1,router2,intfName1='r1-eth1',intfName2='r2-eth1',bw=1)
        self.addLink(h1,router1,intfName2='r1-eth2',params2={ 'ip' : '10.0.1.10/24' },bw=1)#params2 define the eth2 ip address
        self.addLink(h2,router2,intfName2='r2-eth2',params2={ 'ip' : '10.0.2.20/24' },bw=1)
        self.addLink(router3,router4,intfName1='r3-eth1',intfName2='r4-eth1',bw=1)
        self.addLink(h3,router3,intfName2='r3-eth2',params2={ 'ip' : '10.0.5.50/24' },bw=5)
        self.addLink(h4,router4,intfName2='r4-eth2',params2={ 'ip' : '10.0.7.70/24' },bw=5)
        self.addLink(router2,router3,intfName1='r2-eth3',params1={'ip' : '10.0.4.10/24'},intfName2='r3-eth3',params2={ 'ip' : '10.0.4.20/24' },bw=5)
        self.addLink(router4,router1,intfName1='r4-eth3',params1={'ip' : '10.0.8.10/24'},intfName2='r1-eth3',params2={ 'ip' : '10.0.8.20/24' },bw=5)
 
def run():
    "Test linux router"
    topo = NetworkTopo()
    net = Mininet(controller = None, topo=topo )  # controller is used by s1-s3
    net.start()
    info( '*** Routing Table on Router:\n' )
 
    r1=net.getNodeByName('r1')
    r2=net.getNodeByName('r2')
    r3=net.getNodeByName('r3')
    r4=net.getNodeByName('r4')
    info('starting zebra and ospfd service:\n')
 
    r1.cmd('zebra -f /etc/quagga/r1zebra.conf -d -z /tmp/r1zebra.api -i /tmp/r1zebra.interface')
    r2.cmd('zebra -f /etc/quagga/r2zebra.conf -d -z /tmp/r2zebra.api -i /tmp/r2zebra.interface')
    r3.cmd('zebra -f /etc/quagga/r3zebra.conf -d -z /tmp/r3zebra.api -i /tmp/r3zebra.interface')
    r4.cmd('zebra -f /etc/quagga/r4zebra.conf -d -z /tmp/r4zebra.api -i /tmp/r4zebra.interface')

    time.sleep(2)#time for zebra to create api socket
    r1.cmd('ospfd -f /etc/quagga/r1ospfd.conf -d -z /tmp/r1zebra.api -i /tmp/r1ospfd.interface')
    r2.cmd('ospfd -f /etc/quagga/r2ospfd.conf -d -z /tmp/r2zebra.api -i /tmp/r2ospfd.interface')
    r3.cmd('ospfd -f /etc/quagga/r3ospfd.conf -d -z /tmp/r3zebra.api -i /tmp/r3ospfd.interface')
    r4.cmd('ospfd -f /etc/quagga/r4ospfd.conf -d -z /tmp/r4zebra.api -i /tmp/r4ospfd.interface')
    CLI( net )
    net.stop()
    os.system("killall -9 ospfd zebra")
    os.system("rm -f /tmp/*.api")
    os.system("rm -f /tmp/*.interface")
 
if __name__ == '__main__':
    setLogLevel( 'info' )
    run()