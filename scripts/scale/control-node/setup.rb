#!/usr/bin/env ruby

require 'pp'

def sh(cmd, ignore = false)
    puts cmd
    output = `#{cmd}`
    exit -1 if !ignore and $?.to_i != 0
    puts output
    return output
end

def rsh(ip, cmds, ignore = false)
    cmds.each { |cmd|
        sh("sshpass -p c0ntrail123 ssh -q root@#{ip} #{cmd}", ignore)
    }
end

def rcp(ip, src, dst = ".", ignore = false)
    cmds.each { |cmd|
        sh("sshpass -p c0ntrail123 scp -q #{src} root@#{ip}:#{dst}", ignore)
    }
end

def create_nodes
    cmds = <<EOF
launch_vms.rb -n anantha-bgp-scale-node-config1 1
launch_vms.rb -n anantha-bgp-scale-node-control1 1
launch_vms.rb -n anantha-bgp-scale-node-control2 1
launch_vms.rb -n anantha-bgp-scale-node-test-server1 1
launch_vms.rb -n anantha-bgp-scale-node-test-server2 1
EOF
    rsh("10.84.26.23", cmds.split(/\n/))
end

def fix_nodes
    find_nodes = <<EOF
sshpass -p c0ntrail123 ssh -q root@10.84.26.23 CI_ADMIN/ci-openstack.sh nova list --fields name | \grep bgp-scale | \grep -v ID | awk '{print $4}'
EOF

    @nodes = { }
        sh(find_nodes).split(/\n/).each { |node|
        next if node !~ /bgp-scale-node-(.*?)-(\d+)-(\d+)-(\d+)-(\d+)$/
        type = $1
        ip = "#{$2}.#{$3}.#{$4}.#{$5}"
        @nodes[type] = { :host => node, :ip => ip }
        cmds = <<EOF
apt-get -y remove python-iso8601
apt-get -y autoremove
EOF
        rsh(ip, cmds.split(/\n/))
    }
    pp @nodes
end

def setup_topo
    topo = <<EOF
from fabric.api import env

host1 = 'root@#{@nodes["config1"]}'
host2 = 'root@#{@nodes["control1"]}'
host3 = 'root@#{@nodes["control2"]}'

ext_routers = []
router_asn = 64512
public_vn_rtgt = 10000
public_vn_subnet = '22.2.1.1/24'

host_build = 'root@#{@nodes["config1"]}'

env.roledefs = {
    'all': [host1, host2, host3],
    'cfgm': [host1],
    'control': [host2, host3],
    'collector': [host1],
    'webui': [host1],
    'database': [host1],
    'build': [host_build],
    #'compute': [],
}

env.hostnames = {
    'all': ['#{@nodes["config1"]}', '#{@nodes["control1"]}', '#{@nodes["control2"]}']
}

env.passwords = {
    host1: 'c0ntrail123',
    host2: 'c0ntrail123',
    host3: 'c0ntrail123',

    host_build: 'c0ntrail123',
}

env.ostypes = {
    host1:'ubuntu',
    host2:'ubuntu',
    host3:'ubuntu',
}

env.ntp_server = 'ntp.juniper.net'
env.openstack_admin_password = 'c0ntrail123'
env.webui_config = True
env.webui = 'firefox'
env.devstack = False
minimum_diskGB = 32

EOF
    File.open("/tmp/testbed.py", "w") { |fp| fp.puts topo }
end

def copy_and_install_contrail_image (image = "/github-build/mainline/2616/ubuntu-12-04/icehouse/contrail-install-packages_3.0-2616~icehouse_all.deb")
    @nods.each { |node|
        rcp(node[:ip], "#{image} /tmp/testbed.py")
        rsh(node[:ip], "dpkg -i #{File.basename image}")
        rsh(node[:ip], "/opt/contrail/utils/setup.sh")
        rsh(node[:ip], "mv testbed.py /opt/contrail/utils/fabfile/testbeds/")
    }
end

def main
    # create_nodes
    # fix_nodes    
    setup_topo
    copy_and_install_contrail_image
end

main
