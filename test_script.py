import os
import termcolor as T
def log(s, col="green"):
    print (T.colored(s, col))
def main():
    log("copy test code from github")
    os.system("git clone https://github.com/zhaodangxue/mininetLab.git")
    os.system("cd mininetLab")
    python3 = "sudo python3"
    os.system(python3 + "test_spine_leaf_convergence.py")
    os.system(python3 + "test_spine_leaf_reconnected.py")
    os.system(python3 + "test_spine_leaf_tcp_1Gbps.py")
    os.system(python3 + "test_spine_leaf_tcp_200Mbps.py")
    os.system(python3 + "test_spine_leaf_tcp_send_h1self.py")
    os.system(python3 + "test_spine_leaf_udp_send_h1self.py")
    os.system(python3 + "test_spine_leaf_udp_1Gbps.py")
    os.system(python3 + "test_spine_leaf_udp_300Mbps.py")
    os.system(python3 + "test_spine_leaf_udp_100Mbps.py")
    os.system("cd ..")
    os.system("mv miniletLab/data ./data")
    os.system("rm -rf mininetLab")