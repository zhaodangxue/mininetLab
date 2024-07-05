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
#这个mininet实验的简单拓扑图,两个spine，四个leaf，以及四个用于连接的host节点
#                spine1(r1)         spine2(r2)
#                /    \              /    \
#           leaf1(r3) leaf2(r4)  leaf3(r5) leaf4(r6)
#                |      |            |      |
#               h1     h2            h3     h4
#除此之外,h1还与leaf2连接，h2还与leaf3连接，h3还与leaf4连接，h4还与leaf1连接,spine层应该与leaf层全连接，这里展示不了。
#这个脚本是为了测试spine-leaf网络在某些链路断开后，再次连接后的路由收敛时间，经过测试，最终收敛后每个router的路由表大小为21
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

class SpineLeafTopo(Topo):
    def __init__(self):
        # Add default members to class.
        super(SpineLeafTopo, self ).__init__()
        routers = []
        hosts = []
        num_routers = 6
        for i in range(num_routers):
            routers.append(self.addSwitch('r%d' % (i+1)))
        # 其中r1与r2为spine，它们与r3,r4,r5,r6这四个leaf全连接
        # r1与r2之间没有连接
        # r3，r4,r5,r6两两没有连接
        for i in range(2):
            for j in range(2, 6):
                self.addLink("r%d" % (i+1), "r%d" % (j+1))
        h1 = self.addHost('h1',ip = '10.1.1.100/24', defaultRoute='via 10.1.1.10')
        h2 = self.addHost('h2',ip = '10.2.2.100/24', defaultRoute='via 10.2.2.20')
        h3 = self.addHost('h3',ip = '10.3.3.100/24', defaultRoute='via 10.3.3.30')
        h4 = self.addHost('h4',ip = '10.4.4.100/24', defaultRoute='via 10.4.4.40')
        self.addLink('r3','h1')
        self.addLink('r4','h1',intfName2='h1-eth2',params2={ 'ip' :'10.1.2.100/24'})
        self.addLink('r4','h2')
        self.addLink('r5','h2',intfName2='h2-eth2',params2={ 'ip' :'10.2.3.100/24'})
        self.addLink('r5','h3')
        self.addLink('r6','h3',intfName2='h3-eth2',params2={ 'ip' :'10.3.4.100/24'})
        self.addLink('r6','h4')
        self.addLink('r3','h4',intfName2='h4-eth2',params2={ 'ip' :'10.4.1.100/24'})
        return;
def startRouting(router):
    router.cmd('zebra -f spine-leaf/%szebra.conf -d -z /tmp/%szebra.api -i /tmp/%szebra.interface' % (router.name, router.name, router.name))
    router.waitOutput()
    router.cmd('bgpd -f spine-leaf/%sbgpd.conf -d -z /tmp/%szebra.api -i /tmp/%sbgpd.interface' % (router.name, router.name, router.name))
    router.waitOutput()
def measure_route_table_size(net):
     r1 = net.switches[0]
     r2 = net.switches[1]
     r3 = net.switches[2]
     r4 = net.switches[3]
     r5 = net.switches[4]
     r6 = net.switches[5]
     r1_route_table_size = len(r1.cmd('ip route').strip().split('\n'))
     r2_route_table_size = len(r2.cmd('ip route').strip().split('\n'))
     r3_route_table_size = len(r3.cmd('ip route').strip().split('\n'))
     r4_route_table_size = len(r4.cmd('ip route').strip().split('\n'))
     r5_route_table_size = len(r5.cmd('ip route').strip().split('\n'))
     r6_route_table_size = len(r6.cmd('ip route').strip().split('\n'))
     #log("r1 route table size: %d" % r1_route_table_size)
     #log("r2 route table size: %d" % r2_route_table_size)
     #log("r3 route table size: %d" % r3_route_table_size)
     #log("r4 route table size: %d" % r4_route_table_size)
     #log("r5 route table size: %d" % r5_route_table_size)
     #log("r6 route table size: %d" % r6_route_table_size)
     return r1_route_table_size, r2_route_table_size, r3_route_table_size, r4_route_table_size, r5_route_table_size, r6_route_table_size
def main():
    "Create and test a spine-leaf network"
    os.system("rm -f /tmp/r*.api")
    os.system("rm -f /tmp/r*.interface")
    os.system("rm -f /tmp/r*.log")
    os.system("mn -c >/dev/null 2>&1")
    os.system("killall -9 zebra bgpd  > /dev/null 2>&1")
    topo = SpineLeafTopo()
    net = Mininet(controller = None, topo=topo, switch=Router ) 
    net.start()
    for router in net.switches:
        router.cmd('sysctl -w net.ipv4.ip_forward=1')
        startRouting(router)
    time.sleep(15)
    measure_route_table_size(net)
    # 我们这里选择断开和重新连接spine2和leaf1之间的链路
    log("delink leaf1 and spine2")
    net.delLinkBetween(net.switches[1], net.switches[2])
    time.sleep(15)
    log("relink leaf1 and spine2")
    net.addLink('r3','r2',intfName1='r3-eth2',params1={ 'ip' :'100.2.1.2/30'},intfName2='r2-eth1',params2={ 'ip' :'100.2.1.1/30'})
    log("Waiting for routing protocols to converge")
    time_total = 0
    while True :
        r1_size, r2_size, r3_size, r4_size, r5_size, r6_size = measure_route_table_size(net)
        time.sleep(1)
        time_total += 1
        if r1_size == 21 and r2_size == 21 and r3_size == 21 and r4_size == 21 and r5_size == 21 and r6_size == 21:
            break
    log("Routing protocols converged in %d seconds" % time_total)
    CLI( net )
    net.stop()
    os.system("killall -9 zebra bgpd")
if __name__ == '__main__':
    setLogLevel( 'info' )
    main()