import os
import termcolor as T
def log(s, col="green"):
    print (T.colored(s, col))
def main():
    log("copy test code from github")
    python3 = "sudo python3"
    log("run test code")
    os.system("mkdir data")
    os.system(python3 + " test_spine_leaf_convergence.py")
    os.system(python3 + " test_spine_leaf_reconnected.py")
    os.system(python3 + " test_spine_leaf_tcp_1Gbps.py")
    os.system(python3 + " test_spine_leaf_tcp_200Mbps.py")
    os.system(python3 + " test_spine_leaf_tcp_send_h1self.py")
    os.system(python3 + " test_spine_leaf_udp_send_h1self.py")
    os.system(python3 + " test_spine_leaf_udp_1Gbps.py")
    os.system(python3 + " test_spine_leaf_udp_300Mbps.py")
    os.system(python3 + " test_spine_leaf_udp_100Mbps.py")
    os.system("mv ./data ../data")
if __name__ == "__main__":
    main()