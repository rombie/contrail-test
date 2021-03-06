from time import sleep
import fixtures
import testtools
import os
import random
from connections import ContrailConnections
from contrail_test_init import *
from vn_test import *
from vm_test import *
from quantum_test import *
from vnc_api_test import *
from nova_test import *
from testresources import OptimisingTestSuite, TestResource
from encap_tests import *


class VerifyEvpnCases(TestEncapsulation):

    def verify_ipv6_ping_for_non_ip_communication(self, encap):

        # Setting up default encapsulation
        self.logger.info('Setting new Encap before continuing')
        if (encap == 'gre'):
            config_id = self.connections.update_vrouter_config_encap(
                'MPLSoGRE', 'MPLSoUDP', 'VXLAN')
            self.logger.info(
                'Created.UUID is %s. MPLSoGRE is the highest priority encap' % (config_id))
        elif (encap == 'udp'):
            config_id = self.connections.update_vrouter_config_encap(
                'MPLSoUDP', 'MPLSoGRE', 'VXLAN')
            self.logger.info(
                'Created.UUID is %s. MPLSoUDP is the highest priority encap' % (config_id))
        elif (encap == 'vxlan'):
            config_id = self.connections.update_vrouter_config_encap(
                'VXLAN', 'MPLSoUDP', 'MPLSoGRE')
            self.logger.info(
                'Created.UUID is %s. VXLAN is the highest priority encap' % (config_id))
        host_list = []
        for host in self.inputs.compute_ips:
            host_list.append(self.inputs.host_data[host]['name'])
        compute_1 = host_list[0]
        compute_2 = host_list[0]
        if len(host_list) > 1:
            compute_1 = host_list[0]
            compute_2 = host_list[1]

        vn1_fixture = self.res.vn1_fixture
        vn2_fixture = self.res.vn2_fixture
        vm1_name = self.res.vn1_vm1_name
        vm2_name = self.res.vn1_vm2_name
        vn1_name = self.res.vn1_name
        vn1_subnets = self.res.vn1_subnets
        vn1_vm1_fixture = self.useFixture(
            VMFixture(
                project_name=self.inputs.project_name, connections=self.connections,
                vn_obj=vn1_fixture.obj, image_name='ubuntu', vm_name=vm1_name, node_name=compute_1))
        vn1_vm2_fixture = self.useFixture(
            VMFixture(
                project_name=self.inputs.project_name, connections=self.connections,
                vn_obj=vn1_fixture.obj, image_name='ubuntu', vm_name=vm2_name, node_name=compute_2))

        assert vn1_fixture.verify_on_setup()
        assert vn2_fixture.verify_on_setup()
        assert vn1_vm1_fixture.verify_on_setup()
        assert vn1_vm2_fixture.verify_on_setup()
        for i in range(0, 20):
            sleep(5)
            vm2_ipv6 = vn1_vm2_fixture.get_vm_ipv6_addr_from_vm()
            if vm2_ipv6 is not None:
                break
        if vm2_ipv6 is None:
            self.logger.error('Not able to get VM link local address')
            return False
        self.tcpdump_start_on_all_compute()
        assert vn1_vm1_fixture.ping_to_ipv6(
            vm2_ipv6.split("/")[0], count='15')
        comp_vm2_ip = vn1_vm2_fixture.vm_node_ip
        self.tcpdump_analyze_on_compute(comp_vm2_ip, encap.upper())
        return True
    # End verify_ipv6_ping_for_non_ip_communication

    def verify_ping_to_configured_ipv6_address(self, encap):
        '''Configure IPV6 address to VM. Test IPv6 ping to that address.
        '''
        result = True
        # Setting up default encapsulation
        self.logger.info('Setting new Encap before continuing')
        if (encap == 'gre'):
            config_id = self.connections.update_vrouter_config_encap(
                'MPLSoGRE', 'MPLSoUDP', 'VXLAN')
            self.logger.info(
                'Created.UUID is %s. MPLSoGRE is the highest priority encap' % (config_id))
        elif (encap == 'udp'):
            config_id = self.connections.update_vrouter_config_encap(
                'MPLSoUDP', 'MPLSoGRE', 'VXLAN')
            self.logger.info(
                'Created.UUID is %s. MPLSoUDP is the highest priority encap' % (config_id))
        elif (encap == 'vxlan'):
            config_id = self.connections.update_vrouter_config_encap(
                'VXLAN', 'MPLSoUDP', 'MPLSoGRE')
            self.logger.info(
                'Created.UUID is %s. VXLAN is the highest priority encap' % (config_id))
        host_list = []
        for host in self.inputs.compute_ips:
            host_list.append(self.inputs.host_data[host]['name'])
        compute_1 = host_list[0]
        compute_2 = host_list[0]
        if len(host_list) > 1:
            compute_1 = host_list[0]
            compute_2 = host_list[1]

        vn1_vm1 = '1001::1/64'
        vn1_vm2 = '1001::2/64'
        vn1_fixture = self.res.vn1_fixture
        vn2_fixture = self.res.vn2_fixture
        vm1_name = self.res.vn1_vm1_name
        vm2_name = self.res.vn1_vm2_name
        vn1_name = self.res.vn1_name
        vn1_subnets = self.res.vn1_subnets
        vn1_vm1_fixture = self.useFixture(
            VMFixture(
                project_name=self.inputs.project_name, connections=self.connections,
                vn_obj=vn1_fixture.obj, image_name='ubuntu', vm_name=vm1_name, node_name=compute_1))
        vn1_vm2_fixture = self.useFixture(
            VMFixture(
                project_name=self.inputs.project_name, connections=self.connections,
                vn_obj=vn1_fixture.obj, image_name='ubuntu', vm_name=vm2_name, node_name=compute_2))
        assert vn1_fixture.verify_on_setup()
        assert vn2_fixture.verify_on_setup()
        assert vn1_vm1_fixture.verify_on_setup()
        assert vn1_vm2_fixture.verify_on_setup()
        # Waiting for VM to boots up
        sleep(60)
        cmd_to_pass1 = ['sudo ifconfig eth0 inet6 add %s' % (vn1_vm1)]
        vn1_vm1_fixture.run_cmd_on_vm(cmds=cmd_to_pass1)
        cmd_to_pass2 = ['sudo ifconfig eth0 inet6 add %s' % (vn1_vm2)]
        vn1_vm2_fixture.run_cmd_on_vm(cmds=cmd_to_pass2)
        vm1_ipv6 = vn1_vm1_fixture.get_vm_ipv6_addr_from_vm(addr_type='global')
        vm2_ipv6 = vn1_vm2_fixture.get_vm_ipv6_addr_from_vm(addr_type='global')
        self.tcpdump_start_on_all_compute()
        assert vn1_vm1_fixture.ping_to_ipv6(
            vm2_ipv6.split("/")[0], count='15')
        comp_vm2_ip = vn1_vm2_fixture.vm_node_ip
        self.tcpdump_analyze_on_compute(comp_vm2_ip, encap.upper())
        return True
    # End verify_ping_to_configured_ipv6_address

    def verify_l2_ipv6_multicast_traffic(self, encap):
        '''Test ping to all hosts
        '''
        # Setting up default encapsulation
        self.logger.info('Setting new Encap before continuing')
        if (encap == 'gre'):
            config_id = self.connections.update_vrouter_config_encap(
                'MPLSoGRE', 'MPLSoUDP', 'VXLAN')
            self.logger.info(
                'Created.UUID is %s. MPLSoGRE is the highest priority encap' % (config_id))
        elif (encap == 'udp'):
            config_id = self.connections.update_vrouter_config_encap(
                'MPLSoUDP', 'MPLSoGRE', 'VXLAN')
            self.logger.info(
                'Created.UUID is %s. MPLSoUDP is the highest priority encap' % (config_id))
        elif (encap == 'vxlan'):
            config_id = self.connections.update_vrouter_config_encap(
                'VXLAN', 'MPLSoUDP', 'MPLSoGRE')
            self.logger.info(
                'Created.UUID is %s. VXLAN is the highest priority encap' % (config_id))
        result = True
        host_list = []
        for host in self.inputs.compute_ips:
            host_list.append(self.inputs.host_data[host]['name'])
        compute_1 = host_list[0]
        compute_2 = host_list[0]
        compute_3 = host_list[0]
        if len(host_list) > 2:
            compute_1 = host_list[0]
            compute_2 = host_list[1]
            compute_3 = host_list[2]
        elif len(host_list) > 1:
            compute_1 = host_list[0]
            compute_2 = host_list[1]
            compute_3 = host_list[1]
        vn1_vm1 = '1001::1/64'
        vn1_vm2 = '1001::2/64'
        vn1_vm3 = '1001::3/64'
        vn3_fixture = self.res.vn3_fixture
        vn4_fixture = self.res.vn4_fixture
        vn_l2_vm1_name = self.res.vn_l2_vm1_name
        vn_l2_vm2_name = self.res.vn_l2_vm2_name
        vn_l2_vm3_name = 'EVPN_VN_L2_VM3'

        vn_l2_vm1_fixture = self.useFixture(VMFixture(project_name=self.inputs.project_name, connections=self.connections, vn_objs=[
                                            vn3_fixture.obj, vn4_fixture.obj], image_name='ubuntu', vm_name=vn_l2_vm1_name, node_name=compute_1))
        vn_l2_vm2_fixture = self.useFixture(VMFixture(project_name=self.inputs.project_name, connections=self.connections, vn_objs=[
                                            vn3_fixture.obj, vn4_fixture.obj], image_name='ubuntu', vm_name=vn_l2_vm2_name, node_name=compute_2))
        vn_l2_vm3_fixture = self.useFixture(VMFixture(project_name=self.inputs.project_name, connections=self.connections, vn_objs=[
                                            vn3_fixture.obj, vn4_fixture.obj], image_name='ubuntu', vm_name=vn_l2_vm3_name, node_name=compute_3))

        assert vn3_fixture.verify_on_setup()
        assert vn4_fixture.verify_on_setup()
        assert vn_l2_vm1_fixture.verify_on_setup()
        assert vn_l2_vm2_fixture.verify_on_setup()
        assert vn_l2_vm3_fixture.verify_on_setup()

        # Wait till vm is up
        assert vn_l2_vm1_fixture.wait_till_vm_is_up()
        assert vn_l2_vm2_fixture.wait_till_vm_is_up()
        assert vn_l2_vm3_fixture.wait_till_vm_is_up()
        # Configured IPV6 address
        cmd_to_pass1 = ['ifconfig eth1 inet6 add %s' % (vn1_vm1)]
        vn_l2_vm1_fixture.run_cmd_on_vm(cmds=cmd_to_pass1, as_sudo=True)
        cmd_to_pass2 = ['ifconfig eth1 inet6 add %s' % (vn1_vm2)]
        vn_l2_vm2_fixture.run_cmd_on_vm(cmds=cmd_to_pass2, as_sudo=True)
        cmd_to_pass3 = ['ifconfig eth1 inet6 add %s' % (vn1_vm3)]
        vn_l2_vm3_fixture.run_cmd_on_vm(cmds=cmd_to_pass3, as_sudo=True)

        # Bring the intreface up forcefully
        cmd_to_pass4 = ['ifconfig eth1 1']
        vn_l2_vm1_fixture.run_cmd_on_vm(cmds=cmd_to_pass4, as_sudo=True)
        cmd_to_pass5 = ['ifconfig eth1 1']
        vn_l2_vm2_fixture.run_cmd_on_vm(cmds=cmd_to_pass5, as_sudo=True)
        cmd_to_pass6 = ['ifconfig eth1 1']
        vn_l2_vm3_fixture.run_cmd_on_vm(cmds=cmd_to_pass6, as_sudo=True)
        sleep(30)
        ping_count = '10'
        if encap != 'vxlan':
            self.tcpdump_start_on_all_compute()
        ping_output = vn_l2_vm1_fixture.ping_to_ipv6(
            'ff02::1', return_output=True, count=ping_count, intf='eth1')
        self.logger.info("ping output : \n %s" % (ping_output))
        expected_result = ' 0% packet loss'
        assert (expected_result in ping_output)
        vm1_ipv6 = vn_l2_vm1_fixture.get_vm_ipv6_addr_from_vm(
            intf='eth1', addr_type='link').split('/')[0]
        vm2_ipv6 = vn_l2_vm2_fixture.get_vm_ipv6_addr_from_vm(
            intf='eth1', addr_type='link').split('/')[0]
        vm3_ipv6 = vn_l2_vm3_fixture.get_vm_ipv6_addr_from_vm(
            intf='eth1', addr_type='link').split('/')[0]
        ip_list = [vm1_ipv6, vm2_ipv6, vm3_ipv6]
        # getting count of ping response from each vm
        string_count_dict = {}
        string_count_dict = get_string_match_count(ip_list, ping_output)
        self.logger.info("output %s" % (string_count_dict))
        self.logger.info("There should be atleast 9 echo reply from each ip")
        for k in ip_list:
            # this is a workaround : ping utility exist as soon as it gets one
            # response'''
            assert (string_count_dict[k] >= (int(ping_count) - 1))
        if encap != 'vxlan':
            comp_vm2_ip = vn_l2_vm2_fixture.vm_node_ip
            self.tcpdump_analyze_on_compute(comp_vm2_ip, encap.upper())
        return result
    # End verify_l2_ipv6_multicast_traffic

    def verify_l2l3_ipv6_multicast_traffic(self, encap):
        '''Test ping to all hosts
        '''
        # Setting up default encapsulation
        self.logger.info('Setting new Encap before continuing')
        if (encap == 'gre'):
            config_id = self.connections.update_vrouter_config_encap(
                'MPLSoGRE', 'MPLSoUDP', 'VXLAN')
            self.logger.info(
                'Created.UUID is %s. MPLSoGRE is the highest priority encap' % (config_id))
        elif (encap == 'udp'):
            config_id = self.connections.update_vrouter_config_encap(
                'MPLSoUDP', 'MPLSoGRE', 'VXLAN')
            self.logger.info(
                'Created.UUID is %s. MPLSoUDP is the highest priority encap' % (config_id))
        elif (encap == 'vxlan'):
            config_id = self.connections.update_vrouter_config_encap(
                'VXLAN', 'MPLSoUDP', 'MPLSoGRE')
            self.logger.info(
                'Created.UUID is %s. VXLAN is the highest priority encap' % (config_id))
        result = True
        host_list = []
        for host in self.inputs.compute_ips:
            host_list.append(self.inputs.host_data[host]['name'])
        compute_1 = host_list[0]
        compute_2 = host_list[0]
        compute_3 = host_list[0]
        if len(host_list) > 2:
            compute_1 = host_list[0]
            compute_2 = host_list[1]
            compute_3 = host_list[2]
        elif len(host_list) > 1:
            compute_1 = host_list[0]
            compute_2 = host_list[1]
            compute_3 = host_list[1]

        vn1_vm1 = '1001::1/64'
        vn1_vm2 = '1001::2/64'
        vn1_vm3 = '1001::3/64'
        vn3_fixture = self.res.vn3_fixture
        vn_l2_vm1_name = self.res.vn_l2_vm1_name
        vn_l2_vm2_name = self.res.vn_l2_vm2_name
        vn_l2_vm3_name = 'EVPN_VN_L2_VM3'

        vn_l2_vm1_fixture = self.useFixture(
            VMFixture(
                project_name=self.inputs.project_name, connections=self.connections,
                vn_obj=vn3_fixture.obj, image_name='ubuntu', vm_name=vn_l2_vm1_name, node_name=compute_1))
        vn_l2_vm2_fixture = self.useFixture(
            VMFixture(
                project_name=self.inputs.project_name, connections=self.connections,
                vn_obj=vn3_fixture.obj, image_name='ubuntu', vm_name=vn_l2_vm2_name, node_name=compute_2))
        vn_l2_vm3_fixture = self.useFixture(
            VMFixture(
                project_name=self.inputs.project_name, connections=self.connections,
                vn_obj=vn3_fixture.obj, image_name='ubuntu', vm_name=vn_l2_vm3_name, node_name=compute_3))

        assert vn3_fixture.verify_on_setup()
        assert vn_l2_vm1_fixture.verify_on_setup()
        assert vn_l2_vm2_fixture.verify_on_setup()
        assert vn_l2_vm3_fixture.verify_on_setup()

        # Wait till vm is up
        assert vn_l2_vm1_fixture.wait_till_vm_is_up()
        assert vn_l2_vm2_fixture.wait_till_vm_is_up()
        assert vn_l2_vm3_fixture.wait_till_vm_is_up()
        # Configured IPV6 address
        cmd_to_pass1 = ['ifconfig eth0 inet6 add %s' % (vn1_vm1)]
        vn_l2_vm1_fixture.run_cmd_on_vm(cmds=cmd_to_pass1, as_sudo=True)
        cmd_to_pass2 = ['ifconfig eth0 inet6 add %s' % (vn1_vm2)]
        vn_l2_vm2_fixture.run_cmd_on_vm(cmds=cmd_to_pass2, as_sudo=True)
        cmd_to_pass3 = ['ifconfig eth0 inet6 add %s' % (vn1_vm3)]
        vn_l2_vm3_fixture.run_cmd_on_vm(cmds=cmd_to_pass3, as_sudo=True)
        # ping with multicast ipv6 ip on eth0
        ping_count = '10'
        if encap != 'vxlan':
            self.tcpdump_start_on_all_compute()
        ping_output = vn_l2_vm1_fixture.ping_to_ipv6(
            'ff02::1', return_output=True, count=ping_count)
        self.logger.info("ping output : \n %s" % (ping_output))
        expected_result = ' 0% packet loss'
        assert (expected_result in ping_output)
        vm1_ipv6 = vn_l2_vm1_fixture.get_vm_ipv6_addr_from_vm(
            addr_type='link').split('/')[0]
        vm2_ipv6 = vn_l2_vm2_fixture.get_vm_ipv6_addr_from_vm(
            addr_type='link').split('/')[0]
        vm3_ipv6 = vn_l2_vm3_fixture.get_vm_ipv6_addr_from_vm(
            addr_type='link').split('/')[0]
        ip_list = [vm1_ipv6, vm2_ipv6, vm3_ipv6]
        # getting count of ping response from each vm
        string_count_dict = {}
        string_count_dict = get_string_match_count(ip_list, ping_output)
        self.logger.info("output %s" % (string_count_dict))
        self.logger.info("There should be atleast 9 echo reply from each ip")
        for k in ip_list:
            # this is a workaround : ping utility exist as soon as it gets one
            # response'''
            assert (string_count_dict[k] >= (int(ping_count) - 1))
        if encap != 'vxlan':
            comp_vm2_ip = vn_l2_vm2_fixture.vm_node_ip
            self.tcpdump_analyze_on_compute(comp_vm2_ip, encap.upper())

        return result
    # End verify_l2l3_ipv6_multicast_traffic

    def verify_change_of_l2_vn_forwarding_mode(self, encap):
        '''Change the vn forwarding mode from l2 only to l2l3 and verify l3 routes get updated
        '''
        # Setting up default encapsulation
        self.logger.info('Setting new Encap before continuing')
        if (encap == 'gre'):
            config_id = self.connections.update_vrouter_config_encap(
                'MPLSoGRE', 'MPLSoUDP', 'VXLAN')
            self.logger.info(
                'Created.UUID is %s. MPLSoGRE is the highest priority encap' % (config_id))
        elif (encap == 'udp'):
            config_id = self.connections.update_vrouter_config_encap(
                'MPLSoUDP', 'MPLSoGRE', 'VXLAN')
            self.logger.info(
                'Created.UUID is %s. MPLSoUDP is the highest priority encap' % (config_id))
        elif (encap == 'vxlan'):
            config_id = self.connections.update_vrouter_config_encap(
                'VXLAN', 'MPLSoUDP', 'MPLSoGRE')
            self.logger.info(
                'Created.UUID is %s. VXLAN is the highest priority encap' % (config_id))
        result = True
        host_list = []
        for host in self.inputs.compute_ips:
            host_list.append(self.inputs.host_data[host]['name'])
        compute_1 = host_list[0]
        compute_2 = host_list[0]
        if len(host_list) > 1:
            compute_1 = host_list[0]
            compute_2 = host_list[1]
        vm1_ip6 = '1001::1/64'
        vm2_ip6 = '1001::2/64'

        vn3_fixture = self.res.vn3_fixture
        vn_l2_vm1_name = self.res.vn_l2_vm1_name
        vn_l2_vm2_name = self.res.vn_l2_vm2_name
        (self.vn1_name, self.vn1_subnets) = ("EVPN-Test-VN1", ["55.1.1.0/24"])

        self.vn1_fixture = self.useFixture(
            VNFixture(
                project_name=self.inputs.project_name, connections=self.connections,
                inputs=self.inputs, vn_name=self.vn1_name, subnets=self.vn1_subnets, forwarding_mode='l2'))
        assert self.vn1_fixture.verify_on_setup()
        vn_l2_vm1_fixture = self.useFixture(VMFixture(project_name=self.inputs.project_name, connections=self.connections, vn_objs=[
                                            vn3_fixture.obj, self.vn1_fixture.obj], image_name='ubuntu', vm_name=vn_l2_vm1_name, node_name=compute_1))
        vn_l2_vm2_fixture = self.useFixture(VMFixture(project_name=self.inputs.project_name, connections=self.connections, vn_objs=[
                                            vn3_fixture.obj, self.vn1_fixture.obj], image_name='ubuntu', vm_name=vn_l2_vm2_name, node_name=compute_2))

        assert vn_l2_vm1_fixture.verify_on_setup()
        assert vn_l2_vm2_fixture.verify_on_setup()

        # Wait till vm is up
        assert vn_l2_vm1_fixture.wait_till_vm_is_up()
        assert vn_l2_vm2_fixture.wait_till_vm_is_up()
        self.logger.info(
            "Changing vn1 forwarding mode from l2 only to l2l3 followed by calling verify_on_setup for vms which checks if l3 routes are there or not ")
        self.vn1_fixture.add_forwarding_mode(
            project_fq_name=self.inputs.project_fq_name, vn_name=self.vn1_name, forwarding_mode='l2_l3')
        assert self.vn1_fixture.verify_on_setup()
        assert vn_l2_vm1_fixture.verify_on_setup()
        assert vn_l2_vm2_fixture.verify_on_setup()

        # Configure IPV6 address
        cmd_to_pass1 = ['ifconfig eth1 inet6 add %s' % (vm1_ip6)]
        vn_l2_vm1_fixture.run_cmd_on_vm(cmds=cmd_to_pass1, as_sudo=True)
        cmd_to_pass2 = ['ifconfig eth1 inet6 add %s' % (vm2_ip6)]
        vn_l2_vm2_fixture.run_cmd_on_vm(cmds=cmd_to_pass2, as_sudo=True)

        # Bring the intreface up forcefully
        cmd_to_pass3 = ['ifconfig eth1 1']
        vn_l2_vm1_fixture.run_cmd_on_vm(cmds=cmd_to_pass3, as_sudo=True)
        cmd_to_pass4 = ['ifconfig eth1 1']
        vn_l2_vm2_fixture.run_cmd_on_vm(cmds=cmd_to_pass4, as_sudo=True)
        sleep(30)
        vm1_ipv6 = vn_l2_vm1_fixture.get_vm_ipv6_addr_from_vm(
            intf='eth1', addr_type='global').split('/')[0]
        vm2_ipv6 = vn_l2_vm2_fixture.get_vm_ipv6_addr_from_vm(
            intf='eth1', addr_type='global').split('/')[0]

        self.tcpdump_start_on_all_compute()
        assert vn_l2_vm1_fixture.ping_to_ipv6(vm2_ipv6, intf='eth1')
        assert vn_l2_vm2_fixture.ping_to_ipv6(vm1_ipv6, intf='eth1')
        comp_vm1_ip = vn_l2_vm1_fixture.vm_node_ip
        comp_vm2_ip = vn_l2_vm2_fixture.vm_node_ip
        self.tcpdump_analyze_on_compute(comp_vm1_ip, encap.upper())
        self.tcpdump_analyze_on_compute(comp_vm2_ip, encap.upper())

        return result
    # End verify_change_of_l2_vn_forwarding_mode

    def verify_change_of_l2l3_vn_forwarding_mode(self, encap):
        '''Change the vn forwarding mode from l2l3 only to l2 and verify l3 routes gets deleted
        '''
        # Setting up default encapsulation
        self.logger.info('Setting new Encap before continuing')
        if (encap == 'gre'):
            config_id = self.connections.update_vrouter_config_encap(
                'MPLSoGRE', 'MPLSoUDP', 'VXLAN')
            self.logger.info(
                'Created.UUID is %s. MPLSoGRE is the highest priority encap' % (config_id))
        elif (encap == 'udp'):
            config_id = self.connections.update_vrouter_config_encap(
                'MPLSoUDP', 'MPLSoGRE', 'VXLAN')
            self.logger.info(
                'Created.UUID is %s. MPLSoUDP is the highest priority encap' % (config_id))
        elif (encap == 'vxlan'):
            config_id = self.connections.update_vrouter_config_encap(
                'VXLAN', 'MPLSoUDP', 'MPLSoGRE')
            self.logger.info(
                'Created.UUID is %s. VXLAN is the highest priority encap' % (config_id))

        result = True
        host_list = []
        for host in self.inputs.compute_ips:
            host_list.append(self.inputs.host_data[host]['name'])
        compute_1 = host_list[0]
        compute_2 = host_list[0]
        if len(host_list) > 1:
            compute_1 = host_list[0]
            compute_2 = host_list[1]
        vm1_ip6 = '1001::1/64'
        vm2_ip6 = '1001::2/64'

        vn3_fixture = self.res.vn3_fixture
        vn_l2_vm1_name = self.res.vn_l2_vm1_name
        vn_l2_vm2_name = self.res.vn_l2_vm2_name
        (self.vn1_name, self.vn1_subnets) = ("EVPN-Test-VN1", ["55.1.1.0/24"])

        self.vn1_fixture = self.useFixture(
            VNFixture(project_name=self.inputs.project_name,
                      connections=self.connections, inputs=self.inputs, vn_name=self.vn1_name, subnets=self.vn1_subnets))
        assert self.vn1_fixture.verify_on_setup()
        vn_l2_vm1_fixture = self.useFixture(VMFixture(project_name=self.inputs.project_name, connections=self.connections, vn_objs=[
                                            vn3_fixture.obj, self.vn1_fixture.obj], image_name='ubuntu', vm_name=vn_l2_vm1_name, node_name=compute_1))
        vn_l2_vm2_fixture = self.useFixture(VMFixture(project_name=self.inputs.project_name, connections=self.connections, vn_objs=[
                                            vn3_fixture.obj, self.vn1_fixture.obj], image_name='ubuntu', vm_name=vn_l2_vm2_name, node_name=compute_2))

        assert vn_l2_vm1_fixture.verify_on_setup()
        assert vn_l2_vm2_fixture.verify_on_setup()

        # Wait till vm is up
        assert vn_l2_vm1_fixture.wait_till_vm_is_up()
        assert vn_l2_vm2_fixture.wait_till_vm_is_up()
        self.logger.info(
            "Changing vn1 forwarding mode from l2l3 to l2 only  followed by calling verify_on_setup for vms which checks l2 routes and explicity check l3 routes are  removed  ")
        self.vn1_fixture.add_forwarding_mode(
            project_fq_name=self.inputs.project_fq_name, vn_name=self.vn1_name, forwarding_mode='l2')
        assert self.vn1_fixture.verify_on_setup()
        assert vn_l2_vm1_fixture.verify_on_setup()
        assert vn_l2_vm2_fixture.verify_on_setup()

        # Explictly check that l3 routes are removed
        for compute_ip in self.inputs.compute_ips:
            inspect_h = self.agent_inspect[compute_ip]
            vn = inspect_h.get_vna_vn(vn_name=self.vn1_fixture.vn_name)
            if vn is None:
                continue
            agent_vrf_objs = inspect_h.get_vna_vrf_objs(
                vn_name=self.vn1_fixture.vn_name)
            agent_vrf_obj = self.get_matching_vrf(
                agent_vrf_objs['vrf_list'], self.vn1_fixture.vrf_name)
            agent_vrf_id = agent_vrf_obj['ucindex']
            agent_path_vm1 = inspect_h.get_vna_active_route(
                vrf_id=agent_vrf_id, ip=vn_l2_vm1_fixture.vm_ips[1], prefix='32')
            agent_path_vm2 = inspect_h.get_vna_active_route(
                vrf_id=agent_vrf_id, ip=vn_l2_vm2_fixture.vm_ips[1], prefix='32')
            if agent_path_vm1 or agent_path_vm1:
                result = False
                assert result

        # Configure IPV6 address
        cmd_to_pass1 = ['ifconfig eth1 inet6 add %s' % (vm1_ip6)]
        vn_l2_vm1_fixture.run_cmd_on_vm(cmds=cmd_to_pass1, as_sudo=True)
        cmd_to_pass2 = ['ifconfig eth1 inet6 add %s' % (vm2_ip6)]
        vn_l2_vm2_fixture.run_cmd_on_vm(cmds=cmd_to_pass2, as_sudo=True)

        # Bring the intreface up forcefully
        cmd_to_pass3 = ['ifconfig eth1 1']
        vn_l2_vm1_fixture.run_cmd_on_vm(cmds=cmd_to_pass3, as_sudo=True)
        cmd_to_pass4 = ['ifconfig eth1 1']
        vn_l2_vm2_fixture.run_cmd_on_vm(cmds=cmd_to_pass4, as_sudo=True)
        sleep(30)
        vm1_ipv6 = vn_l2_vm1_fixture.get_vm_ipv6_addr_from_vm(
            intf='eth1', addr_type='global').split('/')[0]
        vm2_ipv6 = vn_l2_vm2_fixture.get_vm_ipv6_addr_from_vm(
            intf='eth1', addr_type='global').split('/')[0]

        assert vn_l2_vm1_fixture.ping_to_ipv6(vm2_ipv6, intf='eth1')
        assert vn_l2_vm2_fixture.ping_to_ipv6(vm1_ipv6, intf='eth1')

        return result
    # End verify_change_of_l2l3_vn_forwarding_mode

    def get_matching_vrf(self, vrf_objs, vrf_name):
        return [x for x in vrf_objs if x['name'] == vrf_name][0]

    def verify_vxlan_mode_with_configured_vxlan_id_l2_vn(self):
        ''' Configure vxlan_id explicitly with vn's forwarding mode as l2 and send traffic between vm's using this interface and check traffic is coming with
            configured vxlan_id
        '''
        encap = 'vxlan'
        # Setting up default encapsulation
        config_id = self.connections.update_vrouter_config_encap(
            'VXLAN', 'MPLSoUDP', 'MPLSoGRE')
        self.logger.info(
            'Created.UUID is %s. VXLAN is the highest priority encap' % (config_id))
        result = True
        host_list = []
        for host in self.inputs.compute_ips:
            host_list.append(self.inputs.host_data[host]['name'])
        compute_1 = host_list[0]
        compute_2 = host_list[0]
        if len(host_list) > 1:
            compute_1 = host_list[0]
            compute_2 = host_list[1]

        vm1_ip6 = '1001::1/64'
        vm2_ip6 = '1001::2/64'

        vn3_fixture = self.res.vn3_fixture
        vn_l2_vm1_name = self.res.vn_l2_vm1_name
        vn_l2_vm2_name = self.res.vn_l2_vm2_name
        (self.vn1_name, self.vn1_subnets) = ("EVPN-Test-VN1", ["55.1.1.0/24"])
        # Randomly choose a vxlan_id choosing between 1 and 255 for this test
        # case
        vxlan_random_id = random.randint(1, 255)
        vxlan_hex_id = hex(vxlan_random_id).split('x')[1]
        vxlan_hex_id = vxlan_hex_id + '00'
        self.vxlan_id = str(vxlan_random_id)

        self.vn1_fixture = self.useFixture(
            VNFixture(
                project_name=self.inputs.project_name, connections=self.connections,
                inputs=self.inputs, vn_name=self.vn1_name, subnets=self.vn1_subnets, forwarding_mode='l2', vxlan_id=self.vxlan_id))
        self.addCleanup(
            self.vn1_fixture.set_vxlan_network_identifier_mode, mode='automatic')
        assert self.vn1_fixture.verify_on_setup()

        vn_l2_vm1_fixture = self.useFixture(VMFixture(project_name=self.inputs.project_name, connections=self.connections, vn_objs=[
                                            vn3_fixture.obj, self.vn1_fixture.obj], image_name='ubuntu', vm_name=vn_l2_vm1_name, node_name=compute_1))
        vn_l2_vm2_fixture = self.useFixture(VMFixture(project_name=self.inputs.project_name, connections=self.connections, vn_objs=[
                                            vn3_fixture.obj, self.vn1_fixture.obj], image_name='ubuntu', vm_name=vn_l2_vm2_name, node_name=compute_2))

        assert vn3_fixture.verify_on_setup()
        assert vn_l2_vm1_fixture.verify_on_setup()
        assert vn_l2_vm2_fixture.verify_on_setup()

        # Verify that configured vxlan_id shows up in agent introspect
        for compute_ip in self.inputs.compute_ips:
            inspect_h = self.agent_inspect[compute_ip]
            vn = inspect_h.get_vna_vn(vn_name=self.vn1_fixture.vn_name)
            if vn is None:
                continue
            agent_vrf_objs = inspect_h.get_vna_vrf_objs(
                vn_name=self.vn1_fixture.vn_name)
            agent_vrf_obj = self.get_matching_vrf(
                agent_vrf_objs['vrf_list'], self.vn1_fixture.vrf_name)
            agent_vrf_id = agent_vrf_obj['ucindex']
            agent_path_local_vm = inspect_h.get_vna_layer2_route(
                vrf_id=agent_vrf_id, mac='ff:ff:ff:ff:ff:ff')
            agent_path_vn_l2_vm1 = inspect_h.get_vna_layer2_route(
                vrf_id=agent_vrf_id, mac=vn_l2_vm1_fixture.mac_addr[self.vn1_fixture.vn_fq_name])
            agent_path_vn_l2_vm2 = inspect_h.get_vna_layer2_route(
                vrf_id=agent_vrf_id, mac=vn_l2_vm2_fixture.mac_addr[self.vn1_fixture.vn_fq_name])
            if agent_path_local_vm['routes'][0]['path_list'][0]['vxlan_id'] != self.vxlan_id:
                result = False
                assert result, 'Failed to configure vxlan_id problem with local vm path'
            if agent_path_vn_l2_vm1['routes'][0]['path_list'][0]['vxlan_id'] != self.vxlan_id:
                result = False
                assert result, 'Failed to configure vxlan_id problem with route for %s' + \
                    vn_l2_vm1_name
            if agent_path_vn_l2_vm2['routes'][0]['path_list'][0]['vxlan_id'] != self.vxlan_id:
                result = False
                assert result, 'Failed to configure vxlan_id problem with route for %s' + \
                    vn_l2_vm1_name
            self.logger.info('vxlan_id shown in agent introspect %s ' %
                             (agent_path_local_vm['routes'][0]['path_list'][0]['vxlan_id']))

        # Wait till vm is up
        assert vn_l2_vm1_fixture.wait_till_vm_is_up()
        assert vn_l2_vm2_fixture.wait_till_vm_is_up()

        # Configure IPV6 address
        cmd_to_pass1 = ['ifconfig eth1 inet6 add %s' % (vm1_ip6)]
        vn_l2_vm1_fixture.run_cmd_on_vm(cmds=cmd_to_pass1, as_sudo=True)
        cmd_to_pass2 = ['ifconfig eth1 inet6 add %s' % (vm2_ip6)]
        vn_l2_vm2_fixture.run_cmd_on_vm(cmds=cmd_to_pass2, as_sudo=True)

        # Bring the intreface up forcefully
        cmd_to_pass3 = ['ifconfig eth1 1']
        vn_l2_vm1_fixture.run_cmd_on_vm(cmds=cmd_to_pass3, as_sudo=True)
        cmd_to_pass4 = ['ifconfig eth1 1']
        vn_l2_vm2_fixture.run_cmd_on_vm(cmds=cmd_to_pass4, as_sudo=True)
        sleep(30)
        vm1_ipv6 = vn_l2_vm1_fixture.get_vm_ipv6_addr_from_vm(
            intf='eth1', addr_type='global').split('/')[0]
        vm2_ipv6 = vn_l2_vm2_fixture.get_vm_ipv6_addr_from_vm(
            intf='eth1', addr_type='global').split('/')[0]

        self.tcpdump_start_on_all_compute()
        assert vn_l2_vm1_fixture.ping_to_ipv6(vm2_ipv6, intf='eth1')
        assert vn_l2_vm2_fixture.ping_to_ipv6(vm1_ipv6, intf='eth1')
        comp_vm1_ip = vn_l2_vm1_fixture.vm_node_ip
        comp_vm2_ip = vn_l2_vm2_fixture.vm_node_ip
        # Pad vxlan_hex_id to length of 4 and grep it in tcpdump
        if vxlan_random_id < 15:
            vxlan_hex_id = '0' + vxlan_hex_id

        self.tcpdump_analyze_on_compute(
            comp_vm1_ip, encap.upper(), vxlan_id=vxlan_hex_id)
        self.tcpdump_analyze_on_compute(
            comp_vm2_ip, encap.upper(), vxlan_id=vxlan_hex_id)
        return result
    # End verify_vxlan_mode_with_configured_vxlan_id_l2_vn

    def verify_vxlan_mode_with_configured_vxlan_id_l2l3_vn(self):
        ''' Configure vxlan_id explicitly with vn's forwarding mode as l2l3, send traffic and check if traffic is coming with
            configured vxlan_id
        '''
        encap = 'vxlan'
        # Setting up default encapsulation
        config_id = self.connections.update_vrouter_config_encap(
            'VXLAN', 'MPLSoUDP', 'MPLSoGRE')
        self.logger.info(
            'Created.UUID is %s. VXLAN is the highest priority encap' % (config_id))
        result = True
        host_list = []
        for host in self.inputs.compute_ips:
            host_list.append(self.inputs.host_data[host]['name'])
        compute_1 = host_list[0]
        compute_2 = host_list[0]
        if len(host_list) > 1:
            compute_1 = host_list[0]
            compute_2 = host_list[1]

        vm1_ip6 = '1001::1/64'
        vm2_ip6 = '1001::2/64'

        vn_l2_vm1_name = self.res.vn_l2_vm1_name
        vn_l2_vm2_name = self.res.vn_l2_vm2_name
        (self.vn1_name, self.vn1_subnets) = ("EVPN-Test-VN1", ["55.1.1.0/24"])
        # Randomly choose a vxlan_id choosing between 1 and 255 for this test
        # case
        vxlan_random_id = random.randint(1, 255)
        vxlan_hex_id = hex(vxlan_random_id).split('x')[1]
        vxlan_hex_id = vxlan_hex_id + '00'
        self.vxlan_id = str(vxlan_random_id)

        self.vn1_fixture = self.useFixture(
            VNFixture(
                project_name=self.inputs.project_name, connections=self.connections,
                inputs=self.inputs, vn_name=self.vn1_name, subnets=self.vn1_subnets, vxlan_id=self.vxlan_id))
        self.addCleanup(
            self.vn1_fixture.set_vxlan_network_identifier_mode, mode='automatic')
        assert self.vn1_fixture.verify_on_setup()

        vn_l2_vm1_fixture = self.useFixture(
            VMFixture(
                project_name=self.inputs.project_name, connections=self.connections,
                vn_obj=self.vn1_fixture.obj, image_name='ubuntu', vm_name=vn_l2_vm1_name, node_name=compute_1))
        vn_l2_vm2_fixture = self.useFixture(
            VMFixture(
                project_name=self.inputs.project_name, connections=self.connections,
                vn_obj=self.vn1_fixture.obj, image_name='ubuntu', vm_name=vn_l2_vm2_name, node_name=compute_2))

        assert vn_l2_vm1_fixture.verify_on_setup()
        assert vn_l2_vm2_fixture.verify_on_setup()
        # Verify that configured vxlan_id shows up in agent introspect
        for compute_ip in self.inputs.compute_ips:
            inspect_h = self.agent_inspect[compute_ip]
            vn = inspect_h.get_vna_vn(vn_name=self.vn1_fixture.vn_name)
            if vn is None:
                continue
            agent_vrf_objs = inspect_h.get_vna_vrf_objs(
                vn_name=self.vn1_fixture.vn_name)
            agent_vrf_obj = self.get_matching_vrf(
                agent_vrf_objs['vrf_list'], self.vn1_fixture.vrf_name)
            agent_vrf_id = agent_vrf_obj['ucindex']
            agent_path_local_vm = inspect_h.get_vna_layer2_route(
                vrf_id=agent_vrf_id, mac='ff:ff:ff:ff:ff:ff')
            agent_path_vn_l2_vm1 = inspect_h.get_vna_layer2_route(
                vrf_id=agent_vrf_id, mac=vn_l2_vm1_fixture.mac_addr[self.vn1_fixture.vn_fq_name])
            agent_path_vn_l2_vm2 = inspect_h.get_vna_layer2_route(
                vrf_id=agent_vrf_id, mac=vn_l2_vm2_fixture.mac_addr[self.vn1_fixture.vn_fq_name])
            if agent_path_local_vm['routes'][0]['path_list'][0]['vxlan_id'] != self.vxlan_id:
                result = False
                assert result, 'Failed to configure vxlan_id problem with local vm path'
            if agent_path_vn_l2_vm1['routes'][0]['path_list'][0]['vxlan_id'] != self.vxlan_id:
                result = False
                assert result, 'Failed to configure vxlan_id problem with route for %s' + \
                    vn_l2_vm1_name
            if agent_path_vn_l2_vm2['routes'][0]['path_list'][0]['vxlan_id'] != self.vxlan_id:
                result = False
                assert result, 'Failed to configure vxlan_id problem with route for %s' + \
                    vn_l2_vm1_name
            self.logger.info('vxlan_id shown in agent introspect %s ' %
                             (agent_path_local_vm['routes'][0]['path_list'][0]['vxlan_id']))

        # Wait till vm is up
        assert vn_l2_vm1_fixture.wait_till_vm_is_up()
        assert vn_l2_vm2_fixture.wait_till_vm_is_up()

        # Configure IPV6 address
        cmd_to_pass1 = ['ifconfig eth0 inet6 add %s' % (vm1_ip6)]
        vn_l2_vm1_fixture.run_cmd_on_vm(cmds=cmd_to_pass1, as_sudo=True)
        cmd_to_pass2 = ['ifconfig eth0 inet6 add %s' % (vm2_ip6)]
        vn_l2_vm2_fixture.run_cmd_on_vm(cmds=cmd_to_pass2, as_sudo=True)

        vm1_ipv6 = vn_l2_vm1_fixture.get_vm_ipv6_addr_from_vm(
            addr_type='global').split('/')[0]
        vm2_ipv6 = vn_l2_vm2_fixture.get_vm_ipv6_addr_from_vm(
            addr_type='global').split('/')[0]

        self.tcpdump_start_on_all_compute()
        assert vn_l2_vm1_fixture.ping_to_ipv6(vm2_ipv6)
        assert vn_l2_vm2_fixture.ping_to_ipv6(vm1_ipv6)
        comp_vm1_ip = vn_l2_vm1_fixture.vm_node_ip
        comp_vm2_ip = vn_l2_vm2_fixture.vm_node_ip
        # Pad vxlan_hex_id to length of 4 and grep it in tcpdump
        if vxlan_random_id < 15:
            vxlan_hex_id = '0' + vxlan_hex_id

        self.tcpdump_analyze_on_compute(
            comp_vm1_ip, encap.upper(), vxlan_id=vxlan_hex_id)
        self.tcpdump_analyze_on_compute(
            comp_vm2_ip, encap.upper(), vxlan_id=vxlan_hex_id)
        return result
    # end verify_vxlan_mode_with_configured_vxlan_id_l2l3_vn

    def verify_change_of_l2l3_vn_forwarding_mode(self, encap):
        '''Change the vn forwarding mode from l2l3 only to l2 and verify l3 routes gets deleted
        '''
        # Setting up default encapsulation
        self.logger.info('Setting new Encap before continuing')
        if (encap == 'gre'):
            config_id = self.connections.update_vrouter_config_encap(
                'MPLSoGRE', 'MPLSoUDP', 'VXLAN')
            self.logger.info(
                'Created.UUID is %s. MPLSoGRE is the highest priority encap' % (config_id))
        elif (encap == 'udp'):
            config_id = self.connections.update_vrouter_config_encap(
                'MPLSoUDP', 'MPLSoGRE', 'VXLAN')
            self.logger.info(
                'Created.UUID is %s. MPLSoUDP is the highest priority encap' % (config_id))
        elif (encap == 'vxlan'):
            config_id = self.connections.update_vrouter_config_encap(
                'VXLAN', 'MPLSoUDP', 'MPLSoGRE')
            self.logger.info(
                'Created.UUID is %s. VXLAN is the highest priority encap' % (config_id))
        result = True
        host_list = []
        for host in self.inputs.compute_ips:
            host_list.append(self.inputs.host_data[host]['name'])
        compute_1 = host_list[0]
        compute_2 = host_list[0]
        if len(host_list) > 1:
            compute_1 = host_list[0]
            compute_2 = host_list[1]
        vm1_ip6 = '1001::1/64'
        vm2_ip6 = '1001::2/64'

        vn3_fixture = self.res.vn3_fixture
        vn_l2_vm1_name = self.res.vn_l2_vm1_name
        vn_l2_vm2_name = self.res.vn_l2_vm2_name
        (self.vn1_name, self.vn1_subnets) = ("EVPN-Test-VN1", ["55.1.1.0/24"])

        self.vn1_fixture = self.useFixture(
            VNFixture(project_name=self.inputs.project_name,
                      connections=self.connections, inputs=self.inputs, vn_name=self.vn1_name, subnets=self.vn1_subnets))
        assert self.vn1_fixture.verify_on_setup()
        vn_l2_vm1_fixture = self.useFixture(VMFixture(project_name=self.inputs.project_name, connections=self.connections, vn_objs=[
                                            vn3_fixture.obj, self.vn1_fixture.obj], image_name='ubuntu', vm_name=vn_l2_vm1_name, node_name=compute_1))
        vn_l2_vm2_fixture = self.useFixture(VMFixture(project_name=self.inputs.project_name, connections=self.connections, vn_objs=[
                                            vn3_fixture.obj, self.vn1_fixture.obj], image_name='ubuntu', vm_name=vn_l2_vm2_name, node_name=compute_2))

        assert vn_l2_vm1_fixture.verify_on_setup()
        assert vn_l2_vm2_fixture.verify_on_setup()

        # Wait till vm is up
        self.nova_fixture.wait_till_vm_is_up(vn_l2_vm1_fixture.vm_obj)
        self.nova_fixture.wait_till_vm_is_up(vn_l2_vm2_fixture.vm_obj)
        self.logger.info(
            "Changing vn1 forwarding mode from l2l3 to l2 only  followed by calling verify_on_setup for vms which checks l2 routes and explicity check l3 routes are  removed  ")
        self.vn1_fixture.add_forwarding_mode(
            project_fq_name=self.inputs.project_fq_name, vn_name=self.vn1_name, forwarding_mode='l2')
        assert self.vn1_fixture.verify_on_setup()
        assert vn_l2_vm1_fixture.verify_on_setup()
        assert vn_l2_vm2_fixture.verify_on_setup()

        # Explictly check that l3 routes are removed
        for compute_ip in self.inputs.compute_ips:
            inspect_h = self.agent_inspect[compute_ip]
            vn = inspect_h.get_vna_vn(vn_name=self.vn1_fixture.vn_name)
            if vn is None:
                continue
            agent_vrf_objs = inspect_h.get_vna_vrf_objs(
                vn_name=self.vn1_fixture.vn_name)
            agent_vrf_obj = self.get_matching_vrf(
                agent_vrf_objs['vrf_list'], self.vn1_fixture.vrf_name)
            agent_vrf_id = agent_vrf_obj['ucindex']
            agent_path_vm1 = inspect_h.get_vna_active_route(
                vrf_id=agent_vrf_id, ip=vn_l2_vm1_fixture.vm_ips[1], prefix='32')
            agent_path_vm2 = inspect_h.get_vna_active_route(
                vrf_id=agent_vrf_id, ip=vn_l2_vm2_fixture.vm_ips[1], prefix='32')
            if agent_path_vm1 or agent_path_vm1:
                result = False
                assert result

        # Configure IPV6 address
        cmd_to_pass1 = ['ifconfig eth1 inet6 add %s' % (vm1_ip6)]
        vn_l2_vm1_fixture.run_cmd_on_vm(cmds=cmd_to_pass1, as_sudo=True)
        cmd_to_pass2 = ['ifconfig eth1 inet6 add %s' % (vm2_ip6)]
        vn_l2_vm2_fixture.run_cmd_on_vm(cmds=cmd_to_pass2, as_sudo=True)

        # Bring the intreface up forcefully
        cmd_to_pass3 = ['ifconfig eth1 1']
        vn_l2_vm1_fixture.run_cmd_on_vm(cmds=cmd_to_pass3, as_sudo=True)
        cmd_to_pass4 = ['ifconfig eth1 1']
        vn_l2_vm2_fixture.run_cmd_on_vm(cmds=cmd_to_pass4, as_sudo=True)
        sleep(30)
        vm1_ipv6 = vn_l2_vm1_fixture.get_vm_ipv6_addr_from_vm(
            intf='eth1', addr_type='global').split('/')[0]
        vm2_ipv6 = vn_l2_vm2_fixture.get_vm_ipv6_addr_from_vm(
            intf='eth1', addr_type='global').split('/')[0]

        self.tcpdump_start_on_all_compute()
        assert vn_l2_vm1_fixture.ping_to_ipv6(vm2_ipv6, intf='eth1')
        assert vn_l2_vm2_fixture.ping_to_ipv6(vm1_ipv6, intf='eth1')
        comp_vm1_ip = vn_l2_vm1_fixture.vm_node_ip
        comp_vm2_ip = vn_l2_vm2_fixture.vm_node_ip

        self.tcpdump_analyze_on_compute(comp_vm1_ip, encap.upper())
        self.tcpdump_analyze_on_compute(comp_vm2_ip, encap.upper())

        return result
    # End verify_change_of_l2l3_vn_forwarding_mode

    def get_matching_vrf(self, vrf_objs, vrf_name):
        return [x for x in vrf_objs if x['name'] == vrf_name][0]

    def verify_l2_vm_file_trf_by_scp(self, encap):
        '''Description: Test to validate File Transfer using scp between VMs. Files of different sizes. L2 forwarding mode is used for scp.
        '''
        # Setting up default encapsulation
        self.logger.info('Setting new Encap before continuing')
        if (encap == 'gre'):
            config_id = self.connections.update_vrouter_config_encap(
                'MPLSoGRE', 'MPLSoUDP', 'VXLAN')
            self.logger.info(
                'Created.UUID is %s. MPLSoGRE is the highest priority encap' % (config_id))
        elif (encap == 'udp'):
            config_id = self.connections.update_vrouter_config_encap(
                'MPLSoUDP', 'MPLSoGRE', 'VXLAN')
            self.logger.info(
                'Created.UUID is %s. MPLSoUDP is the highest priority encap' % (config_id))
        elif (encap == 'vxlan'):
            config_id = self.connections.update_vrouter_config_encap(
                'VXLAN', 'MPLSoUDP', 'MPLSoGRE')
            self.logger.info(
                'Created.UUID is %s. VXLAN is the highest priority encap' % (config_id))
        result = True
        host_list = []
        for host in self.inputs.compute_ips:
            host_list.append(self.inputs.host_data[host]['name'])
        compute_1 = host_list[0]
        compute_2 = host_list[0]
        compute_3 = host_list[0]
        if len(host_list) > 2:
            compute_1 = host_list[0]
            compute_2 = host_list[1]
            compute_3 = host_list[2]
        elif len(host_list) > 1:
            compute_1 = host_list[0]
            compute_2 = host_list[1]
            compute_3 = host_list[1]

        vn3_fixture = self.res.vn3_fixture
        vn4_fixture = self.res.vn4_fixture
        vn_l2_vm1_name = self.res.vn_l2_vm1_name
        vn_l2_vm2_name = self.res.vn_l2_vm2_name

        vm1_name = 'dhcp-server-vm'
        vm1_fixture = self.useFixture(VMFixture(project_name=self.inputs.project_name, connections=self.connections, flavor='contrail_flavor_large', vn_objs=[
                                      vn3_fixture.obj, vn4_fixture.obj], image_name='redmine-dhcp-server', vm_name=vm1_name, node_name=compute_1))

        vn_l2_vm1_fixture = self.useFixture(VMFixture(project_name=self.inputs.project_name, connections=self.connections, vn_objs=[
                                            vn3_fixture.obj, vn4_fixture.obj], image_name='ubuntu', vm_name=vn_l2_vm1_name, node_name=compute_2))
        vn_l2_vm2_fixture = self.useFixture(VMFixture(project_name=self.inputs.project_name, connections=self.connections, vn_objs=[
                                            vn3_fixture.obj, vn4_fixture.obj], image_name='ubuntu', vm_name=vn_l2_vm2_name, node_name=compute_3))

        # Wait till vm is up
        assert vm1_fixture.wait_till_vm_is_up()
        assert vn_l2_vm1_fixture.wait_till_vm_is_up()
        assert vn_l2_vm2_fixture.wait_till_vm_is_up()

        assert vn3_fixture.verify_on_setup()
        assert vn4_fixture.verify_on_setup()
        assert vm1_fixture.verify_on_setup()
        assert vn_l2_vm1_fixture.verify_on_setup()
        assert vn_l2_vm2_fixture.verify_on_setup()

        # Configure dhcp-server vm on eth1 and bring the intreface up
        # forcefully

        cmd_to_pass1 = ['ifconfig eth1 13.1.1.253 netmask 255.255.255.0']
        vm1_fixture.run_cmd_on_vm(cmds=cmd_to_pass1)

        cmd_to_pass2 = ['service isc-dhcp-server restart']
        vm1_fixture.run_cmd_on_vm(cmds=cmd_to_pass2)
        sleep(5)
        for i in range(5):
            self.logger.info("Retry %s for bringing up eth1 up" % (i))
            cmd_to_pass3 = ['dhclient eth1']
            ret1 = vn_l2_vm1_fixture.run_cmd_on_vm(
                cmds=cmd_to_pass3, as_sudo=True)
            cmd_to_pass4 = ['dhclient eth1']
            ret2 = vn_l2_vm2_fixture.run_cmd_on_vm(
                cmds=cmd_to_pass4, as_sudo=True)
            if ret1 and ret2:
                break
            sleep(2)
        sleep(30)
        i = 'ifconfig eth1'
        cmd_to_pass5 = [i]
        out = vn_l2_vm2_fixture.run_cmd_on_vm(cmds=cmd_to_pass5)
        output = vn_l2_vm2_fixture.return_output_cmd_dict[i]
        match = re.search('inet addr:(.+?)  Bcast:', output)

        if match:
            dest_vm_ip = match.group(1)
        valid_ip = re.search('13.1.1.(.*)', output)
        assert valid_ip, 'failed to get ip from 13.1.1.0 subnet as configured in dhcp vm'
        vn_l2_vm1_fixture.put_pub_key_to_vm()
        vn_l2_vm2_fixture.put_pub_key_to_vm()
        file_sizes = ['1000', '1101', '1202', '1303', '1373',
                      '1374', '2210', '2845', '3000', '10000', '2000000']
        for size in file_sizes:
            self.logger.info("-" * 80)
            self.logger.info("FILE SIZE = %sB" % size)
            self.logger.info("-" * 80)

            self.logger.info('Transferring the file from %s to %s using scp' %
                             (vn_l2_vm1_fixture.vm_name, vn_l2_vm2_fixture.vm_name))
            filename = 'testfile'

            # Create file
            cmd = 'dd bs=%s count=1 if=/dev/zero of=%s' % (size, filename)
            vn_l2_vm1_fixture.run_cmd_on_vm(cmds=[cmd])

            # Copy key
            vn_l2_vm2_fixture.run_cmd_on_vm(
                cmds=['cp -f ~root/.ssh/authorized_keys ~/.ssh/'], as_sudo=True)
            # Scp file from EVPN_VN_L2_VM1 to EVPN_VN_L2_VM2 using
            # EVPN_VN_L2_VM2 vm's eth1 interface ip
            vn_l2_vm1_fixture.scp_file_to_vm(filename, vm_ip=dest_vm_ip)
            vn_l2_vm1_fixture.run_cmd_on_vm(cmds=['sync'])
            # Verify if file size is same in destination vm
            out_dict = vn_l2_vm2_fixture.run_cmd_on_vm(
                cmds=['ls -l %s' % (filename)])
            if size in out_dict.values()[0]:
                self.logger.info('File of size %s is trasferred successfully to \
                    %s by scp ' % (size, dest_vm_ip))
            else:
                self.logger.warn('File of size %s is not trasferred fine to %s \
                    by scp !! Pls check logs' % (size, dest_vm_ip))
                result = False
                assert result

        return result

    def verify_l2_vm_file_trf_by_tftp(self, encap):
        '''Description: Test to validate File Transfer using tftp between VMs. Files of different sizes. L2 forwarding mode is used for tftp.
        '''
        # Setting up default encapsulation
        self.logger.info('Setting new Encap before continuing')
        if (encap == 'gre'):
            config_id = self.connections.update_vrouter_config_encap(
                'MPLSoGRE', 'MPLSoUDP', 'VXLAN')
            self.logger.info(
                'Created.UUID is %s. MPLSoGRE is the highest priority encap' % (config_id))
        elif (encap == 'udp'):
            config_id = self.connections.update_vrouter_config_encap(
                'MPLSoUDP', 'MPLSoGRE', 'VXLAN')
            self.logger.info(
                'Created.UUID is %s. MPLSoUDP is the highest priority encap' % (config_id))
        elif (encap == 'vxlan'):
            config_id = self.connections.update_vrouter_config_encap(
                'VXLAN', 'MPLSoUDP', 'MPLSoGRE')
            self.logger.info(
                'Created.UUID is %s. VXLAN is the highest priority encap' % (config_id))
        result = True
        host_list = []
        for host in self.inputs.compute_ips:
            host_list.append(self.inputs.host_data[host]['name'])
        compute_1 = host_list[0]
        compute_2 = host_list[0]
        compute_3 = host_list[0]
        if len(host_list) > 2:
            compute_1 = host_list[0]
            compute_2 = host_list[1]
            compute_3 = host_list[2]
        elif len(host_list) > 1:
            compute_1 = host_list[0]
            compute_2 = host_list[1]
            compute_3 = host_list[1]

        vn3_fixture = self.res.vn3_fixture
        vn4_fixture = self.res.vn4_fixture
        vn_l2_vm1_name = self.res.vn_l2_vm1_name
        vn_l2_vm2_name = self.res.vn_l2_vm2_name

        file = 'testfile'
        y = 'ls -lrt /var/lib/tftpboot/%s' % file
        cmd_to_check_file = [y]
        z = 'ls -lrt /var/lib/tftpboot/%s' % file
        cmd_to_check_tftpboot_file = [z]
        file_sizes = ['1000', '1101', '1202', '1303', '1373',
                      '1374', '2210', '2845', '3000', '10000', '2000000']

        vm1_name = 'dhcp-server-vm'
        vm1_fixture = self.useFixture(VMFixture(project_name=self.inputs.project_name, connections=self.connections, flavor='contrail_flavor_large', vn_objs=[
                                      vn3_fixture.obj, vn4_fixture.obj], image_name='redmine-dhcp-server', vm_name=vm1_name, node_name=compute_1))

        vn_l2_vm1_fixture = self.useFixture(VMFixture(project_name=self.inputs.project_name, connections=self.connections, flavor='contrail_flavor_small', vn_objs=[
                                            vn3_fixture.obj, vn4_fixture.obj], image_name='ubuntu-traffic', vm_name=vn_l2_vm1_name, node_name=compute_2))
        vn_l2_vm2_fixture = self.useFixture(VMFixture(project_name=self.inputs.project_name, connections=self.connections, flavor='contrail_flavor_small', vn_objs=[
                                            vn3_fixture.obj, vn4_fixture.obj], image_name='ubuntu-traffic', vm_name=vn_l2_vm2_name, node_name=compute_3))

        # Wait till vm is up
        assert vm1_fixture.wait_till_vm_is_up()
        assert vn_l2_vm1_fixture.wait_till_vm_is_up()
        assert vn_l2_vm2_fixture.wait_till_vm_is_up()
        assert vn3_fixture.verify_on_setup()
        assert vn4_fixture.verify_on_setup()
        assert vm1_fixture.verify_on_setup()
        assert vn_l2_vm1_fixture.verify_on_setup()
        assert vn_l2_vm2_fixture.verify_on_setup()

        # Configure dhcp-server vm on eth1 and bring the intreface up
        # forcefully

        cmd_to_pass1 = ['ifconfig eth1 13.1.1.253 netmask 255.255.255.0']
        vm1_fixture.run_cmd_on_vm(cmds=cmd_to_pass1)
        cmd_to_pass2 = ['service isc-dhcp-server restart']
        vm1_fixture.run_cmd_on_vm(cmds=cmd_to_pass2)
        sleep(5)
        for i in range(5):
            self.logger.info("Retry %s for bringing up eth1 up" % (i))
            cmd_to_pass3 = ['dhclient eth1']
            ret1 = vn_l2_vm1_fixture.run_cmd_on_vm(
                cmds=cmd_to_pass3, as_sudo=True)
            cmd_to_pass4 = ['dhclient eth1']
            ret2 = vn_l2_vm2_fixture.run_cmd_on_vm(
                cmds=cmd_to_pass4, as_sudo=True)
            if ret1 and ret2:
                break
            sleep(2)
        sleep(30)
        i = 'ifconfig eth1'
        cmd_to_pass5 = [i]
        out = vn_l2_vm2_fixture.run_cmd_on_vm(cmds=cmd_to_pass5)
        output = vn_l2_vm2_fixture.return_output_cmd_dict[i]
        match = re.search('inet addr:(.+?)  Bcast:', output)

        if match:
            dest_vm_ip = match.group(1)
        valid_ip = re.search('13.1.1.(.*)', output)
        assert valid_ip, 'failed to get ip from 13.1.1.0 subnet as configured in dhcp vm'

        for size in file_sizes:
            self.logger.info("-" * 80)
            self.logger.info("FILE SIZE = %sB" % size)
            self.logger.info("-" * 80)

            self.logger.info('Transferring the file from %s to %s using tftp' %
                             (vn_l2_vm1_fixture.vm_name, vn_l2_vm2_fixture.vm_name))
            filename = 'testfile'

            # Create file
            cmd = 'dd bs=%s count=1 if=/dev/zero of=%s' % (size, filename)
            vn_l2_vm1_fixture.run_cmd_on_vm(cmds=[cmd])

            # Create the file on the remote machine so that put can be done
            vn_l2_vm2_fixture.run_cmd_on_vm(
                cmds=['sudo touch /var/lib/tftpboot/%s' % (filename),
                      'sudo chmod 777 /var/lib/tftpboot/%s' % (filename)])
            # tftp file from EVPN_VN_L2_VM1 to EVPN_VN_L2_VM2 using
            # EVPN_VN_L2_VM2 vm's eth1 interface ip
            vn_l2_vm1_fixture.tftp_file_to_vm(filename, vm_ip=dest_vm_ip)
            vn_l2_vm1_fixture.run_cmd_on_vm(cmds=['sync'])

            # Verify if file size is same in destination vm
            self.logger.info('Checking if the file exists on %s' %
                             (vn_l2_vm2_fixture.vm_name))
            vn_l2_vm2_fixture.run_cmd_on_vm(cmds=cmd_to_check_file)
            output = vn_l2_vm2_fixture.return_output_cmd_dict[y]
            print output
            if size in output:
                self.logger.info(
                    'File of size %sB transferred via tftp properly' % size)
            else:
                result = False
                self.logger.error(
                    'File of size %sB not transferred via tftp ' % size)
                assert result, 'File of size %sB not transferred via tftp ' % size

        return result

    def verify_vlan_tagged_packets_for_l2_vn(self, encap):
        ''' Send traffic on tagged interfaces eth1.100 and eth1.200 respectively and verify configured  vlan tag in tcpdump
        '''
        # Setting up default encapsulation
        self.logger.info('Setting new Encap before continuing')
        if (encap == 'gre'):
            config_id = self.connections.update_vrouter_config_encap(
                'MPLSoGRE', 'MPLSoUDP', 'VXLAN')
            self.logger.info(
                'Created.UUID is %s. MPLSoGRE is the highest priority encap' % (config_id))
        elif (encap == 'udp'):
            config_id = self.connections.update_vrouter_config_encap(
                'MPLSoUDP', 'MPLSoGRE', 'VXLAN')
            self.logger.info(
                'Created.UUID is %s. MPLSoUDP is the highest priority encap' % (config_id))
        elif (encap == 'vxlan'):
            config_id = self.connections.update_vrouter_config_encap(
                'VXLAN', 'MPLSoUDP', 'MPLSoGRE')
            self.logger.info(
                'Created.UUID is %s. VXLAN is the highest priority encap' % (config_id))
        result = True
        host_list = []
        for host in self.inputs.compute_ips:
            host_list.append(self.inputs.host_data[host]['name'])
        compute_1 = host_list[0]
        compute_2 = host_list[0]
        if len(host_list) > 1:
            compute_1 = host_list[0]
            compute_2 = host_list[1]
        # Setup multi interface vms with eth1 as l2 interface
        vn3_fixture = self.res.vn3_fixture
        vn4_fixture = self.res.vn4_fixture
        vn_l2_vm1_name = self.res.vn_l2_vm1_name
        vn_l2_vm2_name = self.res.vn_l2_vm2_name
        vn3_subnets = self.res.vn3_subnets
        vn4_subnets = self.res.vn4_subnets

        vn_l2_vm1_fixture = self.useFixture(VMFixture(project_name=self.inputs.project_name, connections=self.connections, flavor='contrail_flavor_large',  vn_objs=[
                                            vn3_fixture.obj, vn4_fixture.obj],  image_name='ubuntu-with-vlan8021q', vm_name=vn_l2_vm1_name, node_name=compute_1))
        vn_l2_vm2_fixture = self.useFixture(VMFixture(project_name=self.inputs.project_name, connections=self.connections, flavor='contrail_flavor_large',  vn_objs=[
                                            vn3_fixture.obj, vn4_fixture.obj],  image_name='ubuntu-with-vlan8021q', vm_name=vn_l2_vm2_name, node_name=compute_2))

        assert vn3_fixture.verify_on_setup()
        assert vn4_fixture.verify_on_setup()
        assert vn_l2_vm1_fixture.verify_on_setup()
        assert vn_l2_vm2_fixture.verify_on_setup()

        # Wait till vm is up
        assert vn_l2_vm1_fixture.wait_till_vm_is_up()
        assert vn_l2_vm2_fixture.wait_till_vm_is_up()

        # Bring the intreface up forcefully
        cmd_to_pass1 = ['ifconfig eth1 1']
        vn_l2_vm1_fixture.run_cmd_on_vm(cmds=cmd_to_pass1, as_sudo=True)
        cmd_to_pass2 = ['ifconfig eth1 1']
        vn_l2_vm2_fixture.run_cmd_on_vm(cmds=cmd_to_pass2, as_sudo=True)

        # Configure 2 vlan's on eth1 with id 100 and 200 configure ips and
        # bring up the new interfaces,  first configure vlan 100
        cmd_to_pass1 = ['vconfig add eth1 100']
        vn_l2_vm1_fixture.run_cmd_on_vm(cmds=cmd_to_pass1, as_sudo=True)
        cmd_to_pass2 = ['vconfig add eth1 100']
        vn_l2_vm2_fixture.run_cmd_on_vm(cmds=cmd_to_pass2, as_sudo=True)
        cmd_to_pass3 = ['ip addr add 10.0.0.1/24 dev eth1.100']
        vn_l2_vm1_fixture.run_cmd_on_vm(cmds=cmd_to_pass3, as_sudo=True)
        cmd_to_pass4 = ['ip addr add 10.0.0.2/24 dev eth1.100']
        vn_l2_vm2_fixture.run_cmd_on_vm(cmds=cmd_to_pass4, as_sudo=True)

        # Configure vlan with id 200 and give ip to new interface on both vms
        cmd_to_pass1 = ['vconfig add eth1 200']
        vn_l2_vm1_fixture.run_cmd_on_vm(cmds=cmd_to_pass1, as_sudo=True)
        cmd_to_pass2 = ['vconfig add eth1 200']
        vn_l2_vm2_fixture.run_cmd_on_vm(cmds=cmd_to_pass2, as_sudo=True)
        cmd_to_pass3 = ['ip addr add 20.0.0.1/24 dev eth1.200']
        vn_l2_vm1_fixture.run_cmd_on_vm(cmds=cmd_to_pass3, as_sudo=True)
        cmd_to_pass4 = ['ip addr add 20.0.0.2/24 dev eth1.200']
        vn_l2_vm2_fixture.run_cmd_on_vm(cmds=cmd_to_pass4, as_sudo=True)

        # Bring the new interfaces eth1.100 and eth1.200 forcefully
        cmd_to_pass1 = ['ifconfig eth1.100 up']
        vn_l2_vm1_fixture.run_cmd_on_vm(cmds=cmd_to_pass1, as_sudo=True)
        cmd_to_pass2 = ['ifconfig eth1.100 up']
        vn_l2_vm2_fixture.run_cmd_on_vm(cmds=cmd_to_pass2, as_sudo=True)
        cmd_to_pass3 = ['ifconfig eth1.200 up']
        vn_l2_vm1_fixture.run_cmd_on_vm(cmds=cmd_to_pass3, as_sudo=True)
        cmd_to_pass4 = ['ifconfig eth1.200 up']
        vn_l2_vm2_fixture.run_cmd_on_vm(cmds=cmd_to_pass4, as_sudo=True)
        sleep(30)

        i = 'ifconfig eth1.100'
        j = 'ifconfig eth1.200'
        cmd_to_pass1 = [i, j]
        out = vn_l2_vm1_fixture.run_cmd_on_vm(cmds=cmd_to_pass1)
        output = vn_l2_vm1_fixture.return_output_cmd_dict[i]
        match = re.search('inet addr:(.+?)  Bcast:', output)
        assert match, 'Failed to get configured ip'
        vn_l2_vm1_fixture_eth1_100_ip = match.group(1)
        output = vn_l2_vm1_fixture.return_output_cmd_dict[j]
        match = re.search('inet addr:(.+?)  Bcast:', output)
        assert match, 'Failed to get configured ip'
        vn_l2_vm1_fixture_eth1_200_ip = match.group(1)

        out = vn_l2_vm2_fixture.run_cmd_on_vm(cmds=cmd_to_pass1)
        output = vn_l2_vm2_fixture.return_output_cmd_dict[i]
        match = re.search('inet addr:(.+?)  Bcast:', output)
        assert match, 'Failed to get configured ip'
        vn_l2_vm2_fixture_eth1_100_ip = match.group(1)
        output = vn_l2_vm2_fixture.return_output_cmd_dict[j]
        match = re.search('inet addr:(.+?)  Bcast:', output)
        assert match, 'Failed to get configured ip'
        vn_l2_vm2_fixture_eth1_200_ip = match.group(1)

        # Analyze traffic and verify that configured vlan_id is seen
        vlan_id_pattern1 = '8100' + str('\ ') + '0064'
        vlan_id_pattern2 = '8100' + str('\ ') + '00c8'
        self.tcpdump_start_on_all_compute()
        assert vn_l2_vm1_fixture.ping_to_ip(
            vn_l2_vm2_fixture_eth1_100_ip, count='15')
        comp_vm2_ip = vn_l2_vm2_fixture.vm_node_ip
        self.tcpdump_analyze_on_compute(
            comp_vm2_ip, encap.upper(), vlan_id=vlan_id_pattern1)
        self.tcpdump_start_on_all_compute()
        assert vn_l2_vm2_fixture.ping_to_ip(
            vn_l2_vm1_fixture_eth1_100_ip, count='15')
        comp_vm1_ip = vn_l2_vm1_fixture.vm_node_ip
        self.tcpdump_analyze_on_compute(
            comp_vm1_ip, encap.upper(), vlan_id=vlan_id_pattern1)

        self.tcpdump_start_on_all_compute()
        assert vn_l2_vm1_fixture.ping_to_ip(
            vn_l2_vm2_fixture_eth1_200_ip, count='15')
        comp_vm2_ip = vn_l2_vm2_fixture.vm_node_ip
        self.tcpdump_analyze_on_compute(
            comp_vm2_ip, encap.upper(), vlan_id=vlan_id_pattern2)
        self.tcpdump_start_on_all_compute()
        assert vn_l2_vm2_fixture.ping_to_ip(
            vn_l2_vm1_fixture_eth1_200_ip, count='15')
        comp_vm1_ip = vn_l2_vm1_fixture.vm_node_ip
        self.tcpdump_analyze_on_compute(
            comp_vm1_ip, encap.upper(), vlan_id=vlan_id_pattern2)

        return True
    # end verify_vlan_tagged_packets_for_l2_vn

    def verify_vlan_qinq_tagged_packets_for_l2_vn(self, encap):
        ''' Send traffic on tagged interfaces eth1.100.1000 and eth1.200.2000 respectively on both vms and verify configured  vlan tag in tcpdump
        '''
        # Setting up default encapsulation
        self.logger.info('Setting new Encap before continuing')
        if (encap == 'vxlan'):
            config_id = self.connections.update_vrouter_config_encap(
                'VXLAN', 'MPLSoUDP', 'MPLSoGRE')
            self.logger.info(
                'Created.UUID is %s. VXLAN is the highest priority encap' % (config_id))
        result = True
        host_list = []
        for host in self.inputs.compute_ips:
            host_list.append(self.inputs.host_data[host]['name'])
        compute_1 = host_list[0]
        compute_2 = host_list[0]
        if len(host_list) > 1:
            compute_1 = host_list[0]
            compute_2 = host_list[1]
        # Setup multi interface vms with eth1 as l2 interface
        vn3_fixture = self.res.vn3_fixture
        vn4_fixture = self.res.vn4_fixture
        vn_l2_vm1_name = self.res.vn_l2_vm1_name
        vn_l2_vm2_name = self.res.vn_l2_vm2_name
        vn3_subnets = self.res.vn3_subnets
        vn4_subnets = self.res.vn4_subnets

        vn_l2_vm1_fixture = self.useFixture(VMFixture(project_name=self.inputs.project_name, connections=self.connections, flavor='contrail_flavor_large',  vn_objs=[
                                            vn3_fixture.obj, vn4_fixture.obj],  image_name='ubuntu-with-vlan8021q', vm_name=vn_l2_vm1_name, node_name=compute_1))
        vn_l2_vm2_fixture = self.useFixture(VMFixture(project_name=self.inputs.project_name, connections=self.connections, flavor='contrail_flavor_large',  vn_objs=[
                                            vn3_fixture.obj, vn4_fixture.obj],  image_name='ubuntu-with-vlan8021q', vm_name=vn_l2_vm2_name, node_name=compute_2))

        assert vn3_fixture.verify_on_setup()
        assert vn4_fixture.verify_on_setup()
        assert vn_l2_vm1_fixture.verify_on_setup()
        assert vn_l2_vm2_fixture.verify_on_setup()

        # Wait till vm is up
        assert vn_l2_vm1_fixture.wait_till_vm_is_up()
        assert vn_l2_vm2_fixture.wait_till_vm_is_up()

        # Bring the intreface up forcefully
        cmd_to_pass1 = ['ifconfig eth1 up']
        vn_l2_vm1_fixture.run_cmd_on_vm(cmds=cmd_to_pass1, as_sudo=True)
        cmd_to_pass2 = ['ifconfig eth1 up']
        vn_l2_vm2_fixture.run_cmd_on_vm(cmds=cmd_to_pass2, as_sudo=True)

        # Configure 2 vlan's on eth1 with id 100 and 200 configure ips and
        # bring up the new interface forcefully
        vlan_id1 = '100'
        vlan_id2 = '200'
        i = 'vconfig add eth1 ' + vlan_id1
        j = 'ip addr add 10.0.0.1/24 dev eth1.' + vlan_id1
        k = 'vconfig add eth1 ' + vlan_id2
        l = 'ip addr add 20.0.0.1/24 dev eth1.' + vlan_id2
        cmd_to_pass1 = [i, j, k, l]
        vn_l2_vm1_fixture.run_cmd_on_vm(cmds=cmd_to_pass1, as_sudo=True)
        j = 'ip addr add 10.0.0.2/24 dev eth1.' + vlan_id1
        l = 'ip addr add 20.0.0.2/24 dev eth1.' + vlan_id2
        cmd_to_pass2 = [i, j, k, l]
        vn_l2_vm2_fixture.run_cmd_on_vm(cmds=cmd_to_pass2, as_sudo=True)

        # Bring the new interfaces eth1.100 and eth1.200 forcefully
        cmd_to_pass1 = ['ifconfig eth1.100 up']
        vn_l2_vm1_fixture.run_cmd_on_vm(cmds=cmd_to_pass1, as_sudo=True)
        cmd_to_pass2 = ['ifconfig eth1.100 up']
        vn_l2_vm2_fixture.run_cmd_on_vm(cmds=cmd_to_pass2, as_sudo=True)
        cmd_to_pass3 = ['ifconfig eth1.200 up']
        vn_l2_vm1_fixture.run_cmd_on_vm(cmds=cmd_to_pass3, as_sudo=True)
        cmd_to_pass4 = ['ifconfig eth1.200 up']
        vn_l2_vm2_fixture.run_cmd_on_vm(cmds=cmd_to_pass4, as_sudo=True)

        sleep(30)

        # Check if interface got ip assigned correctly
        i = 'ifconfig eth1.100'
        j = 'ifconfig eth1.200'
        cmd_to_pass1 = [i, j]
        out = vn_l2_vm1_fixture.run_cmd_on_vm(cmds=cmd_to_pass1)
        output = vn_l2_vm1_fixture.return_output_cmd_dict[i]
        match = re.search('inet addr:(.+?)  Bcast:', output)
        assert match, 'Failed to get configured ip'
        vn_l2_vm1_fixture_eth1_100_ip = match.group(1)
        output = vn_l2_vm1_fixture.return_output_cmd_dict[j]
        match = re.search('inet addr:(.+?)  Bcast:', output)
        assert match, 'Failed to get configured ip'
        vn_l2_vm1_fixture_eth1_200_ip = match.group(1)

        out = vn_l2_vm2_fixture.run_cmd_on_vm(cmds=cmd_to_pass1)
        output = vn_l2_vm2_fixture.return_output_cmd_dict[i]
        match = re.search('inet addr:(.+?)  Bcast:', output)
        assert match, 'Failed to get configured ip'
        vn_l2_vm2_fixture_eth1_100_ip = match.group(1)
        output = vn_l2_vm2_fixture.return_output_cmd_dict[j]
        match = re.search('inet addr:(.+?)  Bcast:', output)
        assert match, 'Failed to get configured ip'
        vn_l2_vm2_fixture_eth1_200_ip = match.group(1)

        # Configure new vlans on top of eth1.100 and eth1.200 vlans with
        # vlan_ids 1000 and 2000 respectively
        vlan_eth1_id1 = '1000'
        vlan_eth1_id2 = '2000'
        i = 'vconfig add eth1.100 ' + vlan_eth1_id1
        j = 'ip addr add 30.0.0.1/24 dev eth1.100.' + vlan_eth1_id1
        k = 'vconfig add eth1.100 ' + vlan_eth1_id2
        l = 'ip addr add 40.0.0.1/24 dev eth1.100.' + vlan_eth1_id2
        cmd_to_pass1 = [i, j, k, l]
        vn_l2_vm1_fixture.run_cmd_on_vm(cmds=cmd_to_pass1, as_sudo=True)
        j = 'ip addr add 30.0.0.2/24 dev eth1.100.' + vlan_eth1_id1
        l = 'ip addr add 40.0.0.2/24 dev eth1.100.' + vlan_eth1_id2
        cmd_to_pass2 = [i, j, k, l]
        vn_l2_vm2_fixture.run_cmd_on_vm(cmds=cmd_to_pass2, as_sudo=True)

        i = 'vconfig add eth1.200 ' + vlan_eth1_id1
        j = 'ip addr add 50.0.0.1/24 dev eth1.200.' + vlan_eth1_id1
        k = 'vconfig add eth1.200 ' + vlan_eth1_id2
        l = 'ip addr add 60.0.0.1/24 dev eth1.200.' + vlan_eth1_id2
        cmd_to_pass1 = [i, j, k, l]
        vn_l2_vm1_fixture.run_cmd_on_vm(cmds=cmd_to_pass1, as_sudo=True)
        j = 'ip addr add 50.0.0.2/24 dev eth1.200.' + vlan_eth1_id1
        l = 'ip addr add 60.0.0.2/24 dev eth1.200.' + vlan_eth1_id2
        cmd_to_pass2 = [i, j, k, l]
        vn_l2_vm2_fixture.run_cmd_on_vm(cmds=cmd_to_pass2, as_sudo=True)

        # Bring the new interfaces on eth1.100 and eth1.200 with tag 1000 and
        # 2000 up
        cmd_to_pass1 = ['ifconfig eth1.100.1000 up']
        vn_l2_vm1_fixture.run_cmd_on_vm(cmds=cmd_to_pass1, as_sudo=True)
        cmd_to_pass2 = ['ifconfig eth1.100.1000 up']
        vn_l2_vm2_fixture.run_cmd_on_vm(cmds=cmd_to_pass2, as_sudo=True)
        sleep(10)
        cmd_to_pass3 = ['ifconfig eth1.100.2000 up']
        vn_l2_vm1_fixture.run_cmd_on_vm(cmds=cmd_to_pass3, as_sudo=True)
        cmd_to_pass4 = ['ifconfig eth1.100.2000 up']
        vn_l2_vm2_fixture.run_cmd_on_vm(cmds=cmd_to_pass4, as_sudo=True)
        sleep(10)
        cmd_to_pass1 = ['ifconfig eth1.200.1000 up']
        vn_l2_vm1_fixture.run_cmd_on_vm(cmds=cmd_to_pass1, as_sudo=True)
        cmd_to_pass2 = ['ifconfig eth1.200.1000 up']
        vn_l2_vm2_fixture.run_cmd_on_vm(cmds=cmd_to_pass2, as_sudo=True)
        sleep(10)
        cmd_to_pass3 = ['ifconfig eth1.200.2000 up']
        vn_l2_vm1_fixture.run_cmd_on_vm(cmds=cmd_to_pass3, as_sudo=True)
        cmd_to_pass4 = ['ifconfig eth1.200.2000 up']
        vn_l2_vm2_fixture.run_cmd_on_vm(cmds=cmd_to_pass4, as_sudo=True)
        sleep(10)

        # Check if interface got ip assigned correctly
        i = 'ifconfig eth1.100.1000'
        j = 'ifconfig eth1.100.2000'
        k = 'ifconfig eth1.200.1000'
        l = 'ifconfig eth1.200.2000'
        cmd_to_pass1 = [i, j, k, l]
        out = vn_l2_vm1_fixture.run_cmd_on_vm(cmds=cmd_to_pass1)
        output = vn_l2_vm1_fixture.return_output_cmd_dict[i]
        match = re.search('inet addr:(.+?)  Bcast:', output)
        assert match, 'Failed to get configured ip'
        vn_l2_vm1_fixture_eth1_100_1000_ip = match.group(1)
        output = vn_l2_vm1_fixture.return_output_cmd_dict[j]
        match = re.search('inet addr:(.+?)  Bcast:', output)
        assert match, 'Failed to get configured ip'
        vn_l2_vm1_fixture_eth1_100_2000_ip = match.group(1)
        output = vn_l2_vm1_fixture.return_output_cmd_dict[k]
        match = re.search('inet addr:(.+?)  Bcast:', output)
        assert match, 'Failed to get configured ip'
        vn_l2_vm1_fixture_eth1_200_1000_ip = match.group(1)
        output = vn_l2_vm1_fixture.return_output_cmd_dict[l]
        match = re.search('inet addr:(.+?)  Bcast:', output)
        assert match, 'Failed to get configured ip'
        vn_l2_vm1_fixture_eth1_200_2000_ip = match.group(1)

        out = vn_l2_vm2_fixture.run_cmd_on_vm(cmds=cmd_to_pass1)
        output = vn_l2_vm2_fixture.return_output_cmd_dict[i]
        match = re.search('inet addr:(.+?)  Bcast:', output)
        assert match, 'Failed to get configured ip'
        vn_l2_vm2_fixture_eth1_100_1000_ip = match.group(1)
        output = vn_l2_vm2_fixture.return_output_cmd_dict[j]
        match = re.search('inet addr:(.+?)  Bcast:', output)
        assert match, 'Failed to get configured ip'
        vn_l2_vm2_fixture_eth1_100_2000_ip = match.group(1)
        output = vn_l2_vm2_fixture.return_output_cmd_dict[k]
        match = re.search('inet addr:(.+?)  Bcast:', output)
        assert match, 'Failed to get configured ip'
        vn_l2_vm2_fixture_eth1_200_1000_ip = match.group(1)
        output = vn_l2_vm2_fixture.return_output_cmd_dict[l]
        match = re.search('inet addr:(.+?)  Bcast:', output)
        assert match, 'Failed to get configured ip'
        vn_l2_vm2_fixture_eth1_200_2000_ip = match.group(1)

        # Ping between the interface and verify that vlan id is seen in traffic
        vlan_id_pattern1 =  '8100' + \
            str('\ ') + '0064' + str('\ ') + '8100' + str('\ ') + '03e8'
        vlan_id_pattern2 =  '8100' + \
            str('\ ') + '00c8' + str('\ ') + '8100' + str('\ ') + '03e8'
        vlan_id_pattern3 =  '8100' + \
            str('\ ') + '0064' + str('\ ') + '8100' + str('\ ') + '07d0'
        vlan_id_pattern4 =  '8100' + \
            str('\ ') + '00c8' + str('\ ') + '8100' + str('\ ') + '07d0'
        self.tcpdump_start_on_all_compute()
        assert vn_l2_vm1_fixture.ping_to_ip(
            vn_l2_vm2_fixture_eth1_100_1000_ip, other_opt='-I eth1.100.1000', count='15')
        comp_vm2_ip = vn_l2_vm2_fixture.vm_node_ip
        self.tcpdump_analyze_on_compute(
            comp_vm2_ip, encap.upper(), vlan_id=vlan_id_pattern1)
        self.tcpdump_start_on_all_compute()
        assert vn_l2_vm2_fixture.ping_to_ip(
            vn_l2_vm1_fixture_eth1_100_1000_ip, other_opt='-I eth1.100.1000', count='15')
        comp_vm1_ip = vn_l2_vm1_fixture.vm_node_ip
        self.tcpdump_analyze_on_compute(
            comp_vm1_ip, encap.upper(), vlan_id=vlan_id_pattern1)

        self.tcpdump_start_on_all_compute()
        assert vn_l2_vm1_fixture.ping_to_ip(
            vn_l2_vm2_fixture_eth1_100_2000_ip, other_opt='-I eth1.100.2000', count='15')
        comp_vm2_ip = vn_l2_vm2_fixture.vm_node_ip
        self.tcpdump_analyze_on_compute(
            comp_vm2_ip, encap.upper(), vlan_id=vlan_id_pattern3)
        self.tcpdump_start_on_all_compute()
        assert vn_l2_vm2_fixture.ping_to_ip(
            vn_l2_vm1_fixture_eth1_100_2000_ip, other_opt='-I eth1.100.2000', count='15')
        comp_vm1_ip = vn_l2_vm1_fixture.vm_node_ip
        self.tcpdump_analyze_on_compute(
            comp_vm1_ip, encap.upper(), vlan_id=vlan_id_pattern3)

        self.tcpdump_start_on_all_compute()
        assert vn_l2_vm1_fixture.ping_to_ip(
            vn_l2_vm2_fixture_eth1_200_1000_ip, other_opt='-I eth1.200.1000', count='15')
        comp_vm2_ip = vn_l2_vm2_fixture.vm_node_ip
        self.tcpdump_analyze_on_compute(
            comp_vm2_ip, encap.upper(), vlan_id=vlan_id_pattern2)
        self.tcpdump_start_on_all_compute()
        assert vn_l2_vm2_fixture.ping_to_ip(
            vn_l2_vm1_fixture_eth1_200_1000_ip, other_opt='-I eth1.200.1000', count='15')
        comp_vm1_ip = vn_l2_vm1_fixture.vm_node_ip
        self.tcpdump_analyze_on_compute(
            comp_vm1_ip, encap.upper(), vlan_id=vlan_id_pattern2)

        self.tcpdump_start_on_all_compute()
        assert vn_l2_vm1_fixture.ping_to_ip(
            vn_l2_vm2_fixture_eth1_200_2000_ip, other_opt='-I eth1.200.2000', count='15')
        comp_vm2_ip = vn_l2_vm2_fixture.vm_node_ip
        self.tcpdump_analyze_on_compute(
            comp_vm2_ip, encap.upper(), vlan_id=vlan_id_pattern4)
        self.tcpdump_start_on_all_compute()
        assert vn_l2_vm2_fixture.ping_to_ip(
            vn_l2_vm1_fixture_eth1_200_2000_ip, other_opt='-I eth1.200.2000', count='15')
        comp_vm1_ip = vn_l2_vm1_fixture.vm_node_ip
        self.tcpdump_analyze_on_compute(
            comp_vm1_ip, encap.upper(), vlan_id=vlan_id_pattern4)

        # Ping between interfaces with different outer vlan tag and expect the
        # ping to fail
        self.logger.info(
            "Expecting the pings to fail as the outer vlan tag is different")
        assert not (
            vn_l2_vm1_fixture.ping_to_ip(vn_l2_vm2_fixture_eth1_200_1000_ip,
                                         other_opt='-I eth1.100.1000')), 'Failed in resolving outer vlan tag'
        assert not (
            vn_l2_vm1_fixture.ping_to_ip(vn_l2_vm2_fixture_eth1_200_2000_ip,
                                         other_opt='-I eth1.100.2000')), 'Failed in resolving outer vlan tag'
        assert not (
            vn_l2_vm2_fixture.ping_to_ip(vn_l2_vm1_fixture_eth1_100_1000_ip,
                                         other_opt='-I eth1.200.1000')), 'Failed in resolving outer vlan tag'
        assert not (
            vn_l2_vm2_fixture.ping_to_ip(vn_l2_vm1_fixture_eth1_100_2000_ip,
                                         other_opt='-I eth1.200.2000')), 'Failed in resolving outer vlan tag'

        return True
    # End verify_vlan_qinq_tagged_packets_for_l2_vn

    def verify_epvn_l2_mode_control_node_switchover(self, encap):
        '''Setup l2 evpn and do control node switch over verify ping before and after cn switch over
        '''
        if len(set(self.inputs.bgp_ips)) < 2:
            self.logger.info(
                "Skiping Test. At least 2 control node required to run the test")
            raise self.skipTest(
                "Skiping Test. At least 2 control node required to run the test")

        # Setting up default encapsulation
        self.logger.info('Setting new Encap before continuing')
        if (encap == 'gre'):
            config_id = self.connections.update_vrouter_config_encap(
                'MPLSoGRE', 'MPLSoUDP', 'VXLAN')
            self.logger.info(
                'Created.UUID is %s. MPLSoGRE is the highest priority encap' % (config_id))
        elif (encap == 'udp'):
            config_id = self.connections.update_vrouter_config_encap(
                'MPLSoUDP', 'MPLSoGRE', 'VXLAN')
            self.logger.info(
                'Created.UUID is %s. MPLSoUDP is the highest priority encap' % (config_id))
        elif (encap == 'vxlan'):
            config_id = self.connections.update_vrouter_config_encap(
                'VXLAN', 'MPLSoUDP', 'MPLSoGRE')
            self.logger.info(
                'Created.UUID is %s. VXLAN is the highest priority encap' % (config_id))

        result = True
        host_list = []
        for host in self.inputs.compute_ips:
            host_list.append(self.inputs.host_data[host]['name'])
        compute_1 = host_list[0]
        compute_2 = host_list[0]
        if len(host_list) > 1:
            compute_1 = host_list[0]
            compute_2 = host_list[1]

        vn1_vm1 = '1001::1/64'
        vn1_vm2 = '1001::2/64'
        vn3_fixture = self.res.vn3_fixture
        vn4_fixture = self.res.vn4_fixture
        vn_l2_vm1_name = self.res.vn_l2_vm1_name
        vn_l2_vm2_name = self.res.vn_l2_vm2_name

        vn_l2_vm1_fixture = self.useFixture(VMFixture(project_name=self.inputs.project_name, connections=self.connections, vn_objs=[
                                            vn3_fixture.obj, vn4_fixture.obj], image_name='ubuntu', vm_name=vn_l2_vm1_name, node_name=compute_1))
        vn_l2_vm2_fixture = self.useFixture(VMFixture(project_name=self.inputs.project_name, connections=self.connections, vn_objs=[
                                            vn3_fixture.obj, vn4_fixture.obj], image_name='ubuntu', vm_name=vn_l2_vm2_name, node_name=compute_2))

        assert vn3_fixture.verify_on_setup()
        assert vn4_fixture.verify_on_setup()
        assert vn_l2_vm1_fixture.verify_on_setup()
        assert vn_l2_vm2_fixture.verify_on_setup()

        # Wait till vm is up
        assert vn_l2_vm1_fixture.wait_till_vm_is_up()
        assert vn_l2_vm2_fixture.wait_till_vm_is_up()

        # Configured IPV6 address
        cmd_to_pass1 = ['ifconfig eth1 inet6 add %s' % (vn1_vm1)]
        vn_l2_vm1_fixture.run_cmd_on_vm(cmds=cmd_to_pass1, as_sudo=True)
        cmd_to_pass2 = ['ifconfig eth1 inet6 add %s' % (vn1_vm2)]
        vn_l2_vm2_fixture.run_cmd_on_vm(cmds=cmd_to_pass2, as_sudo=True)

        # Bring the intreface up forcefully
        cmd_to_pass3 = ['ifconfig eth1 1']
        vn_l2_vm1_fixture.run_cmd_on_vm(cmds=cmd_to_pass3, as_sudo=True)
        cmd_to_pass4 = ['ifconfig eth1 1']
        vn_l2_vm2_fixture.run_cmd_on_vm(cmds=cmd_to_pass4, as_sudo=True)
        sleep(30)
        vm1_ipv6 = vn_l2_vm1_fixture.get_vm_ipv6_addr_from_vm(
            intf='eth1', addr_type='global')
        vm2_ipv6 = vn_l2_vm2_fixture.get_vm_ipv6_addr_from_vm(
            intf='eth1', addr_type='global')
        self.tcpdump_start_on_all_compute()
        assert vn_l2_vm1_fixture.ping_to_ipv6(
            vm2_ipv6.split("/")[0], count='15')
        assert vn_l2_vm2_fixture.ping_to_ipv6(
            vm1_ipv6.split("/")[0], count='15')
        comp_vm1_ip = vn_l2_vm1_fixture.vm_node_ip
        comp_vm2_ip = vn_l2_vm2_fixture.vm_node_ip
        self.tcpdump_analyze_on_compute(comp_vm1_ip, encap.upper())
        self.tcpdump_analyze_on_compute(comp_vm2_ip, encap.upper())

        # Figuring the active control node
        active_controller = None
        self.agent_inspect = self.connections.agent_inspect
        inspect_h = self.agent_inspect[vn_l2_vm1_fixture.vm_node_ip]
        agent_xmpp_status = inspect_h.get_vna_xmpp_connection_status()
        for entry in agent_xmpp_status:
            if entry['cfg_controller'] == 'Yes':
                active_controller = entry['controller_ip']
        active_controller_host_ip = self.inputs.host_data[
            active_controller]['host_ip']
        self.logger.info('Active control node from the Agent %s is %s' %
                         (vn_l2_vm1_fixture.vm_node_ip, active_controller_host_ip))

        # Stop on Active node
        self.logger.info('Stoping the Control service in  %s' %
                         (active_controller_host_ip))
        self.inputs.stop_service(
            'contrail-control', [active_controller_host_ip])
        sleep(5)

        # Check the control node shifted to other control node
        new_active_controller = None
        new_active_controller_state = None
        inspect_h = self.agent_inspect[vn_l2_vm1_fixture.vm_node_ip]
        agent_xmpp_status = inspect_h.get_vna_xmpp_connection_status()
        for entry in agent_xmpp_status:
            if entry['cfg_controller'] == 'Yes':
                new_active_controller = entry['controller_ip']
                new_active_controller_state = entry['state']
        new_active_controller_host_ip = self.inputs.host_data[
            new_active_controller]['host_ip']
        self.logger.info('Active control node from the Agent %s is %s' %
                         (vn_l2_vm1_fixture.vm_node_ip, new_active_controller_host_ip))
        if new_active_controller_host_ip == active_controller_host_ip:
            self.logger.error(
                'Control node switchover fail. Old Active controlnode was %s and new active control node is %s' %
                (active_controller_host_ip, new_active_controller_host_ip))
            result = False

        if new_active_controller_state != 'Established':
            self.logger.error(
                'Agent does not have Established XMPP connection with Active control node')
            result = result and False

        # Start the control node service again
        self.logger.info('Starting the Control service in  %s' %
                         (active_controller_host_ip))
        self.inputs.start_service(
            'contrail-control', [active_controller_host_ip])

        # Check the BGP peering status from the currently active control node
        sleep(5)
        cn_bgp_entry = self.cn_inspect[
            new_active_controller_host_ip].get_cn_bgp_neigh_entry()
        sleep(5)
        for entry in cn_bgp_entry:
            if entry['state'] != 'Established':
                result = result and False
                self.logger.error(
                    'With Peer %s peering is not Established. Current State %s ' %
                    (entry['peer'], entry['state']))
        # Check ping
        self.tcpdump_start_on_all_compute()
        assert vn_l2_vm1_fixture.ping_to_ipv6(
            vm2_ipv6.split("/")[0], count='15')
        assert vn_l2_vm2_fixture.ping_to_ipv6(
            vm1_ipv6.split("/")[0], count='15')
        comp_vm1_ip = vn_l2_vm1_fixture.vm_node_ip
        comp_vm2_ip = vn_l2_vm2_fixture.vm_node_ip
        self.tcpdump_analyze_on_compute(comp_vm1_ip, encap.upper())
        self.tcpdump_analyze_on_compute(comp_vm2_ip, encap.upper())

        return result
    # verify_epvn_l2_mode_control_node_switchover

    def verify_epvn_with_agent_restart(self, encap):
        '''Restart the vrouter service and verify the impact on L2 route
        '''

        # Setting up default encapsulation
        self.logger.info('Setting new Encap before continuing')
        if (encap == 'gre'):
            config_id = self.connections.update_vrouter_config_encap(
                'MPLSoGRE', 'MPLSoUDP', 'VXLAN')
            self.logger.info(
                'Created.UUID is %s. MPLSoGRE is the highest priority encap' % (config_id))
        elif (encap == 'udp'):
            config_id = self.connections.update_vrouter_config_encap(
                'MPLSoUDP', 'MPLSoGRE', 'VXLAN')
            self.logger.info(
                'Created.UUID is %s. MPLSoUDP is the highest priority encap' % (config_id))
        elif (encap == 'vxlan'):
            config_id = self.connections.update_vrouter_config_encap(
                'VXLAN', 'MPLSoUDP', 'MPLSoGRE')
            self.logger.info(
                'Created.UUID is %s. VXLAN is the highest priority encap' % (config_id))
        result = True
        host_list = []
        for host in self.inputs.compute_ips:
            host_list.append(self.inputs.host_data[host]['name'])
        compute_1 = host_list[0]
        compute_2 = host_list[0]
        if len(host_list) > 1:
            compute_1 = host_list[0]
            compute_2 = host_list[1]

        vn1_fixture = self.res.vn1_fixture
        vn2_fixture = self.res.vn2_fixture
        vm1_name = self.res.vn1_vm1_name
        vm2_name = self.res.vn1_vm2_name
        vn1_name = self.res.vn1_name
        vn1_subnets = self.res.vn1_subnets
        vn1_vm1_fixture = self.useFixture(
            VMFixture(
                project_name=self.inputs.project_name, connections=self.connections,
                vn_obj=vn1_fixture.obj, image_name='ubuntu', vm_name=vm1_name, node_name=compute_1))
        vn1_vm2_fixture = self.useFixture(
            VMFixture(
                project_name=self.inputs.project_name, connections=self.connections,
                vn_obj=vn1_fixture.obj, image_name='ubuntu', vm_name=vm2_name, node_name=compute_2))
        assert vn1_fixture.verify_on_setup()
        assert vn2_fixture.verify_on_setup()
        assert vn1_vm1_fixture.verify_on_setup()
        assert vn1_vm2_fixture.verify_on_setup()
        assert vn1_vm1_fixture.wait_till_vm_is_up()
        assert vn1_vm2_fixture.wait_till_vm_is_up()
        for i in range(0, 20):
            vm2_ipv6 = vn1_vm2_fixture.get_vm_ipv6_addr_from_vm()
            if vm2_ipv6 is not None:
                break
        if vm2_ipv6 is None:
            self.logger.error('Not able to get VM link local address')
            return False
        self.logger.info(
            'Checking the communication between 2 VM using ping6 to VM link local address from other VM')
        assert vn1_vm1_fixture.ping_to_ipv6(vm2_ipv6.split("/")[0])
        self.logger.info('Will restart compute  services now')
        for compute_ip in self.inputs.compute_ips:
            self.inputs.restart_service('contrail-vrouter', [compute_ip])
        sleep(10)
        self.logger.info(
            'Verifying L2 route and other VM verification after restart')
        assert vn1_vm1_fixture.verify_on_setup(force=True)
        assert vn1_vm2_fixture.verify_on_setup(force=True)
        for i in range(0, 20):
            vm2_ipv6 = vn1_vm2_fixture.get_vm_ipv6_addr_from_vm()
            if vm2_ipv6 is not None:
                break
        if vm2_ipv6 is None:
            self.logger.error('Not able to get VM link local address')
            return False
        self.logger.info(
            'Checking the communication between 2 VM after vrouter restart')
        self.tcpdump_start_on_all_compute()
        assert vn1_vm1_fixture.ping_to_ipv6(
            vm2_ipv6.split("/")[0], count='15')
        comp_vm2_ip = vn1_vm2_fixture.vm_node_ip
        if len(set(self.inputs.compute_ips)) >= 2:
            self.tcpdump_analyze_on_compute(comp_vm2_ip, encap.upper())
        return True
    # End test_epvn_with_agent_restart

    def verify_epvn_l2_mode(self, encap):
        '''Restart the vrouter service and verify the impact on L2 route
        '''

        # Setting up default encapsulation
        self.logger.info('Setting new Encap before continuing')
        if (encap == 'gre'):
            config_id = self.connections.update_vrouter_config_encap(
                'MPLSoGRE', 'MPLSoUDP', 'VXLAN')
            self.logger.info(
                'Created.UUID is %s. MPLSoGRE is the highest priority encap' % (config_id))
        elif (encap == 'udp'):
            config_id = self.connections.update_vrouter_config_encap(
                'MPLSoUDP', 'MPLSoGRE', 'VXLAN')
            self.logger.info(
                'Created.UUID is %s. MPLSoUDP is the highest priority encap' % (config_id))
        elif (encap == 'vxlan'):
            config_id = self.connections.update_vrouter_config_encap(
                'VXLAN', 'MPLSoUDP', 'MPLSoGRE')
            self.logger.info(
                'Created.UUID is %s. VXLAN is the highest priority encap' % (config_id))
        result = True
        host_list = []
        for host in self.inputs.compute_ips:
            host_list.append(self.inputs.host_data[host]['name'])
        compute_1 = host_list[0]
        compute_2 = host_list[0]
        if len(host_list) > 1:
            compute_1 = host_list[0]
            compute_2 = host_list[1]

        vn1_vm1 = '1001::1/64'
        vn1_vm2 = '1001::2/64'
        nova_fixture = self.res.nova_fixture
        vn3_fixture = self.res.vn3_fixture
        vn4_fixture = self.res.vn4_fixture
        vn_l2_vm1_name = self.res.vn_l2_vm1_name
        vn_l2_vm2_name = self.res.vn_l2_vm2_name
        vn3_name = self.res.vn3_name
        vn4_name = self.res.vn4_name
        vn3_subnets = self.res.vn3_subnets
        vn4_subnets = self.res.vn4_subnets

        vn_l2_vm1_fixture = self.useFixture(VMFixture(project_name=self.inputs.project_name, connections=self.connections, vn_objs=[
                                            vn3_fixture.obj, vn4_fixture.obj], image_name='ubuntu', vm_name=vn_l2_vm1_name, node_name=compute_1))
        vn_l2_vm2_fixture = self.useFixture(VMFixture(project_name=self.inputs.project_name, connections=self.connections, vn_objs=[
                                            vn3_fixture.obj, vn4_fixture.obj], image_name='ubuntu', vm_name=vn_l2_vm2_name, node_name=compute_2))

        assert vn3_fixture.verify_on_setup()
        assert vn4_fixture.verify_on_setup()
        assert vn_l2_vm1_fixture.verify_on_setup()
        assert vn_l2_vm2_fixture.verify_on_setup()

        # Wait till vm is up
        vn_l2_vm1_fixture.wait_till_vm_is_up()
        vn_l2_vm2_fixture.wait_till_vm_is_up()

        # Configured IPV6 address
        cmd_to_pass1 = ['ifconfig eth1 inet6 add %s' % (vn1_vm1)]
        vn_l2_vm1_fixture.run_cmd_on_vm(cmds=cmd_to_pass1, as_sudo=True)
        cmd_to_pass2 = ['ifconfig eth1 inet6 add %s' % (vn1_vm2)]
        vn_l2_vm2_fixture.run_cmd_on_vm(cmds=cmd_to_pass2, as_sudo=True)

        # Bring the intreface up forcefully
        cmd_to_pass3 = ['ifconfig eth1 1']
        vn_l2_vm1_fixture.run_cmd_on_vm(cmds=cmd_to_pass3, as_sudo=True)
        cmd_to_pass4 = ['ifconfig eth1 1']
        vn_l2_vm2_fixture.run_cmd_on_vm(cmds=cmd_to_pass4, as_sudo=True)
        sleep(30)

        vm1_ipv6 = vn_l2_vm1_fixture.get_vm_ipv6_addr_from_vm(
            intf='eth1', addr_type='global')
        vm2_ipv6 = vn_l2_vm2_fixture.get_vm_ipv6_addr_from_vm(
            intf='eth1', addr_type='global')
        self.tcpdump_start_on_all_compute()
        assert vn_l2_vm1_fixture.ping_to_ipv6(
            vm2_ipv6.split("/")[0], count='15', intf='eth1')
        comp_vm2_ip = vn_l2_vm2_fixture.vm_node_ip
        if len(set(self.inputs.compute_ips)) >= 2:
            self.tcpdump_analyze_on_compute(comp_vm2_ip, encap.upper())

        #self.logger.info('Will restart compute  services now')
        # for compute_ip in self.inputs.compute_ips:
        #    self.inputs.restart_service('contrail-vrouter',[compute_ip])
        # sleep(10)

        # TODO
        #assert vn1_vm1_fixture.verify_on_setup()
        #assert vn1_vm2_fixture.verify_on_setup()

        #self.logger.info('Checking the communication between 2 VM after vrouter restart')
        #assert vn_l2_vm1_fixture.ping_to_ipv6(vm2_ipv6.split("/")[0])
        return True
    # End verify_epvn_l2_mode
