from mininet.topo import Topo
from mininet.net import Mininet
from mininet.log import lg, info, setLogLevel
from mininet.util import dumpNodeConnections, quietRun, moveIntf
from mininet.cli import CLI
from mininet.node import Switch, OVSKernelSwitch

from subprocess import Popen, PIPE, check_output
from time import sleep, time
from multiprocessing import Process
from argparse import ArgumentParser

import sys
import os
import termcolor as T
import time

#这个mininet实验的简单拓扑图,四个交换机以及四个挂载在交换机上的host节点，同时划分两个区域，每个区内的交换机通过ospf连接。
#    s1---------s2————————————s3----------s4
#    |   ospf    |     bgp     |    ospf   |
#    |   as10     |             |    as100    |
#    h1          h2            h3         h4  

def log(s, col="green"):
    print (T.colored(s, col))

#Router类这里作为Mininet中switch类的继承类
class Router(Switch):
    """Defines a new router that is inside a network namespace so that the
    individual routing entries don't collide.

    """
    ID = 0
    def __init__(self, name, **kwargs):
        kwargs['inNamespace'] = True
        Switch.__init__(self, name, **kwargs)
        Router.ID += 1
        self.switch_id = Router.ID

    @staticmethod
    def setup():
        return

    def start(self, controllers):
        pass

    def stop(self):
        self.deleteIntfs()

    def log(self, s, col="magenta"):
        print (T.colored(s, col))
#一个简单的拓扑图类，继承自mininet自己的topo类
class SimpleTopo(Topo):
    def __init__(self):
        # Add default members to class.
        super(SimpleTopo, self ).__init__()
        num_hosts_per_router = 1 # 我们这里每一个交换机下都有一个host节点挂载
        routers = []
        hosts = []
        # AS10
        num_routers = 2 #AS1中有两个路由r1和r2
        for i in range(num_routers):
            router = self.addSwitch('r%d'%(i+1))
            routers.append(router)
        self.addLink('r1','r2')
        #为这两个router创建他们的host节点
        h1 = self.addHost( 'h1', ip='10.1.0.100/24', defaultRoute='via 10.1.0.10') 
        h2 = self.addHost( 'h2', ip='10.2.0.100/24', defaultRoute='via 10.2.0.20')
        self.addLink('r1', 'h1')
        self.addLink('r2', 'h2')
        hosts.append(h1)
        hosts.append(h2)
        # AS100
        num_routers = 2
        for i in range(num_routers):
            router = self.addSwitch('r%d'%(i+3))
            routers.append(router)
        self.addLink('r3','r4')
        #为这两个router创建他们的host节点
        h3 = self.addHost( 'h3', ip='100.3.0.100/24', defaultRoute='via 100.3.0.30')
        h4 = self.addHost( 'h4', ip='100.4.0.100/24', defaultRoute='via 100.4.0.40')
        self.addLink('r3', 'h3')
        self.addLink('r4', 'h4')
        hosts.append(h3)
        hosts.append(h4)
        # Add links between routers，AS1和AS2之间的连接是通过bgp协议
        self.addLink('r2', 'r3')
        return
#为每一个router节点启动zebra, ospf和bgp服务
def startRouting(router):
    if router.name == 'r1':
        router.cmd('zebra -f bgp/r1zebra.conf -d -z /tmp/r1zebra.api -i /tmp/r1zebra.interface')
        router.waitOutput()
        router.cmd('ospfd -f bgp/r1ospfd.conf -d -z /tmp/r1zebra.api -i /tmp/r1ospfd.interface')
        router.waitOutput()
        log("Starting zebra and ospf on r1")
    elif router.name == 'r2':
        router.cmd('zebra -f bgp/r2zebra.conf -d -z /tmp/r2zebra.api -i /tmp/r2zebra.interface')
        router.waitOutput()
        router.cmd('ospfd -f bgp/r2ospfd.conf -d -z /tmp/r2zebra.api -i /tmp/r2ospfd.interface')
        router.waitOutput()
        router.cmd('bgpd -f bgp/bgpd1.conf -d -z /tmp/r2zebra.api -i /tmp/r2bgpd.interface')
        router.waitOutput()
        log("Starting zebra, ospf and bgp on r2")
    elif router.name == 'r3':
        router.cmd('zebra -f bgp/r3zebra.conf -d -z /tmp/r3zebra.api -i /tmp/r3zebra.interface')
        router.waitOutput()
        router.cmd('ospfd -f bgp/r3ospfd.conf -d -z /tmp/r3zebra.api -i /tmp/r3ospfd.interface')
        router.waitOutput()
        router.cmd('bgpd -f bgp/bgpd2.conf -d -z /tmp/r3zebra.api -i /tmp/r3bgpd.interface')
        router.waitOutput()
        log("Starting zebra, ospf and bgp on r3")
    elif router.name == 'r4':
        router.cmd('zebra -f bgp/r4zebra.conf -d -z /tmp/r4zebra.api -i /tmp/r4zebra.interface')
        router.waitOutput()
        router.cmd('ospfd -f bgp/r4ospfd.conf -d -z /tmp/r4zebra.api -i /tmp/r4ospfd.interface')
        router.waitOutput()
        log("Starting zebra and ospf on r4")
    else:
        log("Unknown router %s" % router.name)
#为每一个host节点设置默认的ip地址
def getIP(hostname):
    if hostname == 'h1':
        ip = '10.1.0.100'
    elif hostname == 'h2':
        ip = '10.2.0.100'
    elif hostname == 'h3':
        ip = '100.3.0.100'
    elif hostname == 'h4':
        ip = '100.4.0.100'
    else:
        log("Unknown host %s" % hostname)
        ip = ''
    return ip
#为每一个host节点设置默认的网关
def getGateway(hostname):
    if hostname == 'h1':
        gw = '10.1.0.10'
    elif hostname == 'h2':
        gw = '10.2.0.20'
    elif hostname == 'h3':
        gw = '100.3.0.30'
    elif hostname == 'h4':
        gw = '100.4.0.40'
    else:
        log("Unknown host %s" % hostname)
        gw = ''
    return gw
def main():
    #清除之前的实验环境
    os.system("rm -f /tmp/r*.api")
    os.system("rm -f /tmp/r*.interface")
    os.system("rm -f /tmp/r*.log")
    os.system("rm -f /tmp/bgpd1.log")
    os.system("rm -f /tmp/bgpd2.log")
    os.system("rm -f /tmp/r1ospfd.log")
    os.system("rm -f /tmp/r2ospfd.log")
    os.system("rm -f /tmp/r3ospfd.log")
    os.system("rm -f /tmp/r4ospfd.log")
    os.system("mn -c >/dev/null 2>&1")
    os.system("killall -9 zebra bgpd ospfd > /dev/null 2>&1")
    net = Mininet(topo=SimpleTopo(), switch=Router, controller=None)
    net.start()
    for router in net.switches:
        router.cmd('sysctl -w net.ipv4.ip_forward=1')
        startRouting(router)
    log("Network started")
    time.sleep(2)
    for router in net.switches:
        startRouting(router)
    CLI(net)
    net.stop()
    os.system("killall -9 zebra bgpd ospfd")
if __name__ == '__main__':
    setLogLevel('info')
    main()

