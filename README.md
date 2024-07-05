## Mininet的简单ospf结合bgp协议实验

本实验是一个简单的利用mininet和quagga完成的一个网络实验。bgp文件夹下存储了相应的路由配置。testBGP.py则是真正构建了网络拓扑图并测试了host节点之间的连通性。运行实验时可以在本文件夹下执行

实验1

```bash
sudo python3 testBGP.py
```

实验2

```bash
sudo python3 test_spine_leaf.py
```

具体的网络拓扑图以及对应的配置和环境安装解释写在pdf文件之中。

除此之外，还针对spine-leaf的数据中心框架的网络拓扑做了一系列的测试，包括通过iperf的打流方式测试网络拓扑的udp和tcp性能和保真率，以及建立拓扑后路由的收敛速度以及重建拓扑路由的收敛速度，每一个测试脚本中都已作出详实说明，运行对应脚本即可观察测试效果。
