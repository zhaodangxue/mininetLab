## Mininet的简单ospf结合bgp协议实验

### 实验介绍

本实验是一个简单的利用mininet和quagga完成的一个网络实验。bgp文件夹下存储了相应的路由配置。testBGP.py则是真正构建了网络拓扑图并测试了host节点之间的连通性。运行实验时可以在本文件夹下执行。

### 实验环境

强烈建议使用Ubuntu 20.04操作系统，这个版本的Ubuntu操作系统安装Quagga的方式最为简单

下面是两个示例实验的运行案例:

实验1

```bash
sudo python3 testBGP.py
```

实验2

```bash
sudo python3 test_spine_leaf.py
```

具体实验的网络拓扑图以及对应的配置和环境安装解释写在pdf文件之中。

除此之外，还针对spine-leaf的数据中心框架的网络拓扑做了一系列的测试，包括通过iperf的打流方式测试网络拓扑的udp和tcp性能和保真率，以及建立拓扑后路由的收敛速度以及重建拓扑路由的收敛速度，每一个测试脚本中的注释都对测试目的和对象作出详实说明，运行对应脚本即可观察测试效果。

这里给出实验介绍中一个统一安装quagga的方法：

```sh
echo "deb http://cn.archive.ubuntu.com/ubuntu/ focal-updates main restricted"  | tee -a /etc/apt/sources.list.d/quagga.list
apt update
apt-cache policy quagga # 如果执行了上面的操作，这一部应该可以看到列表中有quagga
apt install quagga=1.2.4-4ubuntu0.4
```

经测试上面安装quagga的方法不适用于Ubuntu 22.04 。所以还是建议实验环境为版本为20.04的Ubuntu操作系统，此时只需要执行

```bash
sudo apt install quagga=1.2.4-4ubuntu0.4
```

即可安装Quagga
