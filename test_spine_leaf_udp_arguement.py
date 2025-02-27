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
from mininet.link import TCLink
import argparse
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
#这个脚本是用来测试spine-leaf网络的udp性能，h1发送udp包给h4，h4接收udp包，链路带宽为BW(输入参数为-B），按iperf配置运行udp，以带宽速率bw（输入参数为-b）发送udp包10s
global_bw = 1000
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
                self.addLink("r%d" % (i+1), "r%d" % (j+1),bw=global_bw)
        h1 = self.addHost('h1',ip = '10.1.1.100/24', defaultRoute='via 10.1.1.10')
        h2 = self.addHost('h2',ip = '10.2.2.100/24', defaultRoute='via 10.2.2.20')
        h3 = self.addHost('h3',ip = '10.3.3.100/24', defaultRoute='via 10.3.3.30')
        h4 = self.addHost('h4',ip = '10.4.4.100/24', defaultRoute='via 10.4.4.40')
        self.addLink('r3','h1',bw = global_bw)
        self.addLink('r4','h1',intfName2='h1-eth2',params2={ 'ip' :'10.1.2.100/24'},bw = global_bw)
        self.addLink('r4','h2',bw = global_bw)
        self.addLink('r5','h2',intfName2='h2-eth2',params2={ 'ip' :'10.2.3.100/24'},bw = global_bw)
        self.addLink('r5','h3',bw = global_bw)
        self.addLink('r6','h3',intfName2='h3-eth2',params2={ 'ip' :'10.3.4.100/24'},bw = global_bw)
        self.addLink('r6','h4',bw = global_bw)
        self.addLink('r3','h4',intfName2='h4-eth2',params2={ 'ip' :'10.4.1.100/24'},bw = global_bw)
        return;
def startRouting(router):
    router.cmd('zebra -f spine-leaf-5/%szebra.conf -d -z /tmp/%szebra.api -i /tmp/%szebra.interface' % (router.name, router.name, router.name))
    router.waitOutput()
    router.cmd('bgpd -f spine-leaf-5/%sbgpd.conf -d -z /tmp/%szebra.api -i /tmp/%sbgpd.interface' % (router.name, router.name, router.name))
    router.waitOutput()
def main():
    "Create and test a spine-leaf network"
    parser = argparse.ArgumentParser(description="Run a spine-leaf network test")
    parser.add_argument('--BW', '-B',type=int, help='Bandwidth of the links in Mbps', default=1000)
    parser.add_argument('--bw', '-b',type=int, help='Bandwidth of the iperf', default=1000)
    args = parser.parse_args()
    global global_bw
    global_bw = args.BW
    filename = "data/udp_arguement.log"
    os.system("rm -f /tmp/r*.api")
    os.system("rm -f /tmp/r*.interface")
    os.system("rm -f /tmp/r*.log")
    os.system("mn -c >/dev/null 2>&1")
    os.system("killall -9 zebra bgpd  > /dev/null 2>&1")
    topo = SpineLeafTopo()
    net = Mininet(controller = None, topo=topo, switch=Router,link=TCLink) 
    net.start()
    for router in net.switches:
        router.cmd('sysctl -w net.ipv4.ip_forward=1')
        startRouting(router)
    time.sleep(15)
    h1 = net.getNodeByName('h1')
    h4 = net.getNodeByName('h4')
    # 启动iperf服务器,tcp
    info("*** Starting iperf server on h4\n")
    h4.cmd('iperf -u -s &')
    # 启动iperf客户端,tcp
    info("*** Running iperf client on h1\n")
    information = "Bandwidth of iperf: %dMbps    Bandwidth of links: %dMbps\n" % (args.bw, args.BW)
    result = h1.cmd('iperf -u -c 10.4.4.100 -b %dM -t 10' % args.bw)
    info(result)
    with open(filename,'a') as f:
        f.write(information)
        f.write(result)
    net.stop()
    os.system("killall -9 zebra bgpd")
if __name__ == '__main__':
    setLogLevel( 'info' )
    main()