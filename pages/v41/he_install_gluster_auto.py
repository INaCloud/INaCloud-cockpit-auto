import time
import os
import re
import logging
from selenium import webdriver
from fabric.api import run, settings, put, local, get, env
import urllib2
from vncdotool import api
from HTMLParser import HTMLParser
from cases import CONF
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import ConfigParser
from selenium.webdriver.common.by import By


log = logging.getLogger("sherry")

host_ip, host_user, host_password, browser, host2_ip, host3_ip = CONF.get('common').get(
    'host_ip'), CONF.get('common').get('host_user'), CONF.get('common').get(
    'host_password'), CONF.get('common').get('browser'), CONF.get('common').get('host2_ip'), CONF.get('common').get(
    'host3_ip')

rhn_user, rhn_password = CONF.get('subscription').get('rhn_user'), CONF.get(
    'subscription').get('rhn_password')

gluster_ip, gluster_storage_path, rhvm_appliance_path, vm_mac, vm_fqdn, vm_ip, vm_password, engine_password, auto_answer, no_of_cpus, mem_size, vm_disk_size, gw_address  = CONF.get(
    'hosted_engine'
).get('glusterfs_ip'), CONF.get('hosted_engine').get('gluster_storage_path'),CONF.get('hosted_engine').get(
    'rhvm_appliance_path'
), CONF.get('hosted_engine').get('he_vm_mac'), CONF.get('hosted_engine').get(
    'he_vm_fqdn'), CONF.get('hosted_engine').get('he_vm_ip'), CONF.get(
    'hosted_engine').get('he_vm_password'), CONF.get('hosted_engine').get('engine_password'), CONF.get('hosted_engine').get(
    'auto_answer'), CONF.get('hosted_engine').get('no_of_cpus'), CONF.get('hosted_engine').get('mem_size'), CONF.get(
    'hosted_engine').get('vm_disk_size'), CONF.get('hosted_engine').get('gw_address')



env.host_string = host_user + '@' + host_ip
env.password = host_password

gluster_data_node1, gluster_data_node2, gluster_arbiter_node, vmstore_is_arbiter, data_is_arbiter, data_disk_count, device_name_engine, device_name_data, device_name_vmstore, size_of_datastore_lv, size_of_vmstore_lv, gdeploy_conf_file_path, mount_engine_brick, mount_data_brick, mount_vmstore_brick, gluster_vg_name, gluster_pv_name, number_of_Volumes, engine_lv_name, file_path_interface1, file_path_interface2, rhhi_version = CONF.get(
    'gluster_details'
).get('gluster_data_node1'), CONF.get('gluster_details').get('gluster_data_node2'), CONF.get('gluster_details').get(
    'gluster_arbiter_node'), CONF.get('gluster_details').get('vmstore_is_arbiter'), CONF.get('gluster_details').get(
    'data_is_arbiter'), CONF.get('gluster_details').get('data_disk_count'), CONF.get('gluster_details').get(
    'device_name_engine'), CONF.get('gluster_details').get('device_name_data'), CONF.get('gluster_details').get(
    'device_name_vmstore'), CONF.get('gluster_details').get('size_of_datastore_lv'), CONF.get('gluster_details').get(
    'size_of_vmstore_lv'), CONF.get('gluster_details').get('gdeploy_conf_file_path'), CONF.get('gluster_details').get(
    'mount_engine_brick'), CONF.get('gluster_details').get('mount_data_brick'), CONF.get('gluster_details').get(
    'mount_vmstore_brick'), CONF.get('gluster_details').get('gluster_vg_name'), CONF.get('gluster_details').get(
    'gluster_pv_name'), CONF.get('gluster_details').get('number_of_Volumes'), CONF.get('gluster_details').get(
    'engine_lv_name'), CONF.get('gluster_details').get('file_path_interface1'), CONF.get('gluster_details').get(
    'file_path_interface2'), CONF.get('gluster_details').get('rhhi_version')






class MyHTMLParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.links = []
        self.a_texts = []
        self.a_text_flag = False

    def handle_starttag(self, tag, attrs):
        # print "Encountered the beginning of a %s tag" % tag
        if tag == "a":
            self.a_text_flag = True
            if len(attrs) == 0:
                pass
            else:
                for (variable, value) in attrs:
                    if variable == "href":
                        self.links.append(value)

    def handle_endtag(self, tag):
        if tag == "a":
            self.a_text_flag = False

    def handle_data(self, data):
        if self.a_text_flag:
            if data.startswith("rhvm-appliance"):
                self.a_texts.append(data)

def get_latest_rhvm_appliance(appliance_path):
    """
    Purpose:
        Get the latest rhvm appliance from appliance parent path
    """
    # Get the html page from appliance path
    # log.info("Getting the latest rhvm appliance...")
    req = urllib2.Request(appliance_path)
    response = urllib2.urlopen(req)
    rhvm_appliance_html = response.read()
    # Parse the html
    mp = MyHTMLParser()
    mp.feed(rhvm_appliance_html)
    mp.close()

    # Get the latest rhvm appliance url link
    mp.a_texts.sort()
    link_42 = []
    # link_42 = []
    all_link = mp.a_texts
    for link in all_link:
        if "4.2" in link:
            link_42.append(link)

    latest_rhvm_appliance_name = link_42[-1]

    latest_rhvm_appliance_link = None
    for link in mp.links:
        if re.search(latest_rhvm_appliance_name, link):
            latest_rhvm_appliance_link = link

    latest_rhvm_appliance = appliance_path + latest_rhvm_appliance_link
    
    return latest_rhvm_appliance


def verify_gluster_deployment(host_dict):
    host_ip = host_dict['host_ip']
    host_user = host_dict['host_user']
    host_password = host_dict['host_password']
    with settings(
        warn_only=True,
        host_string=host_user + '@' + host_ip,
        password=host_password):
        while(True):
            cmd0 = 'gluster volume list'
            ret0 = run(cmd0)
            if not ret0.__contains__("vmstore"):
                log.info("waiting for gluster deployment to finish")
            else:
                volume_list = ret0.split("\n")
                if volume_list.__len__() == number_of_Volumes:
                    cmd1 = "gluster volume info vmstore | grep Status" 
                    ret1 = run(cmd1)
                    if ret1.__contains__("Status: Started"):
                        time.sleep(10)
                        break
    

def he_install_gluster_auto(host_dict, gluster_storage_dict, install_dict, vm_dict, gluster_dict):
    host_ip = host_dict['host_ip']
    host_user = host_dict['host_user']
    host_password = host_dict['host_password']
    if 'cockpit_port' in host_dict:
        cockpit_port = host_dict['cockpit_port']
    else:
        cockpit_port = "9090"
    root_uri = "https://" + host_ip + ":" + cockpit_port
    gluster_ip = gluster_storage_dict['gluster_ip']
    gluster_storage_path = gluster_storage_dict['gluster_storage_path']

    rhvm_appliance_path = install_dict['rhvm_appliance_path']
    he_nic = install_dict['he_nic']

    vm_mac = vm_dict['vm_mac']
    vm_fqdn = vm_dict['vm_fqdn']
    vm_ip = vm_dict['vm_ip']
    vm_password = vm_dict['vm_password']
    engine_password = vm_dict['engine_password']
    auto_answer = vm_dict['auto_answer']

     # Subscription to RHSM via CMD
    log.info("Subscription to RHN or RHSM ,then enable rhvh repos...")
    with settings(
            warn_only=True,
            host_string=host_user + '@' + host_ip,
            password=host_password):
            cmd0 = "subscription-manager register --username=%s --password=%s" % (
                rhn_user, rhn_password)
            run(cmd0)
            cmd1 = "subscription-manager attach --auto"
            run(cmd1)
            cmd2 = "subscription-manager repos --enable=rhel-7-server-rhvh-4-rpms"
            run(cmd2)
            cmd3 = "subscription-manager repos --list-enable |grep 'Repo ID' |grep 'rhvh'"
            output = run("os.popen(cmd3).read()")
            if output == 0:
                raise RuntimeError("Failed to find rhvh repos")
    
    
    #Downloading the rhevm appliance to the host machine
    rhvm_appliance_link = rhvm_appliance_path
    local_rhvm_appliance = "/root/%s" % rhvm_appliance_link.split('/')[-2]
    log.info("Getting the latest rhvm appliance...")
    with settings(
        warn_only=True,
        host_string=host_user + '@' + host_ip,
        password=host_password):
        cmd = "curl -o %s %s" % (local_rhvm_appliance, rhvm_appliance_link)
        output = run(cmd)
    if output.failed:
        raise RuntimeError("Failed to download the latest rhvm appliance")
    
    # Add host to /etc/hosts and install rhvm_appliance
    log.info(
        "Adding the host to /etc/hosts and installing the rhvm appliance...")
    with settings(
        warn_only=True,
        host_string=host_user + '@' + host_ip,
        password=host_password):
        cmd0 = "hostname"
        host_name = run(cmd0)
        cmd1 = "echo '%s  %s' >> /etc/hosts" % (host_ip, host_name)
        run(cmd1)
        cmd2 = "echo '%s' > /etc/hostname" % host_name
        run(cmd2)
        cmd3 = "hostname %s" % host_name
        run(cmd3)
        cmd4 = "echo '%s  %s' >> /etc/hosts" % (vm_ip, vm_fqdn)
        run(cmd4)
        cmd5 = "rpm -ivh %s" % local_rhvm_appliance
        run(cmd5)
        cmd6 = "rm -f %s" % local_rhvm_appliance
        run(cmd6)
    
    
    log.info("Generating and copying keys")
    #generating keys
    generate_keys()
    copy_keys()
    time.sleep(2)
    log.info("Deploying gluster...")
    dr = webdriver.Firefox()
    dr.get(root_uri)
    time.sleep(5)
    id = dr.find_element_by_id
    class_name = dr.find_element_by_class_name
    tag_name = dr.find_elements_by_tag_name
    xpath = dr.find_element_by_xpath
    xpaths = dr.find_elements_by_xpath
    

    # Login to cockpit
    log.info("Logining to the cockpit...")
    id("login-user-input").send_keys(host_user)
    time.sleep(2)
    id("login-password-input").send_keys(host_password)
    time.sleep(2)
    id("login-button").click()
    time.sleep(5)
    dr.get(root_uri + "/ovirt-dashboard")
    time.sleep(5)
    dr.switch_to_frame("cockpit1:localhost/ovirt-dashboard")
    time.sleep(10)
    xpath("//a[@href='#/he']").click()
    time.sleep(10)

      
    
    # code for configuring gluster
    log.info("Configuring gluster to deploy Hosted Engine............")
    xpath("//input[@value='hci']").click()                                               #click on 'Configure Hosted Engine with Gluster"
    time.sleep(2)
    xpath("//button[@class='btn btn-lg btn-primary']").click()                           #click Next Button
    time.sleep(2)
    xpaths("//input[@placeholder='Gluster network address']")[0].send_keys(gluster_data_node1)  #Enter the first gluster host
    time.sleep(2)
    xpaths("//input[@placeholder='Gluster network address']")[1].send_keys(gluster_data_node2)  #Enter the second gluster host
    time.sleep(2)
    xpaths("//input[@placeholder='Gluster network address']")[2].send_keys(gluster_arbiter_node) #Enter the third gluster host
    time.sleep(2)
    xpath("//button[@class='btn btn-primary wizard-pf-next']").click() #click on Next
    time.sleep(2)
    xpath("//button[@class='btn btn-primary wizard-pf-next']").click() #click on Next
    time.sleep(2)
    if vmstore_is_arbiter == "Yes":
        xpaths("//input[@title='Third host in the host list will be used for creating arbiter bricks']")[1].click() #check arbiter checkbox to create vmstore as arbiter volume
        time.sleep(2)
    if data_is_arbiter == "Yes":
        xpaths("//input[@title='Third host in the host list will be used for creating arbiter bricks']")[2].click() #check arbiter checkbox to create data as arbiter volume
        time.sleep(2)
    time.sleep(5)
    xpath("//button[@class='btn btn-primary wizard-pf-next']").click()                                          # click Next
    xpaths("//input[@type='number']")[1].clear()
    time.sleep(1)
    xpaths("//input[@type='number']")[1].send_keys(data_disk_count)           #Enter the disk count of RAID
    time.sleep(1)
    xpaths("//input[@placeholder='device name']")[0].clear()
    xpaths("//input[@placeholder='device name']")[0].send_keys(device_name_engine)  #Enter the device name to create engine lv
    time.sleep(1)
    xpaths("//input[@placeholder='device name']")[1].clear()
    xpaths("//input[@placeholder='device name']")[1].send_keys(device_name_data)    #Enter the device name to create data lv
    time.sleep(1)
    xpaths("//input[@placeholder='device name']")[2].clear()
    xpaths("//input[@placeholder='device name']")[2].send_keys(device_name_vmstore)  #Enter the device name to create vmstore lv
    time.sleep(1)
    xpaths("//input[@type='number']")[3].clear()
    time.sleep(1)
    xpaths("//input[@type='number']")[3].send_keys(size_of_datastore_lv)          #Enter the size for data store lv
    time.sleep(1)
    xpaths("//input[@type='number']")[4].clear()
    time.sleep(1)
    xpaths("//input[@type='number']")[4].send_keys(size_of_vmstore_lv)            #Enter the size for vmstore lv
    time.sleep(1)
    xpath("//button[@class='btn btn-primary wizard-pf-next']").click()            #click Next
    time.sleep(5)
    xpath("//button[@class='btn btn-primary wizard-pf-finish']").click()          #Click on Deploy Button
    verify_gluster_deployment(host_dict)                                         #Validate Gluster Deployment
    time.sleep(10)
    if not xpath("//button[@class='btn btn-lg btn-primary']").is_displayed(): 
        log.error("continue to Hosted Engine deployment not found")
        
    else:
        log.info("Going to Deploy HostedEngine on Gluster...")
    
    xpath("//button[@class='btn btn-lg btn-primary']").click()  # click on button 'Continue to Hosted Engine deployment'
    time.sleep(10)
    
    # Test starts from here
    if rhhi_version == "1.1":
        class_name("btn-default").click()  # click next button,continue yes
        time.sleep(20)
        list(tag_name("input"))[0].clear()  # clear the text box to configure gluster cluster
        time.sleep(5)
        list(tag_name("input"))[0].send_keys("Yes") #entering the input as yes to configure gluster cluster
        time.sleep(5)
        class_name("btn-default").click()  # click next button, continue yes
        time.sleep(10)
    
        class_name("btn-default").click()  # gateway ip confirm
        time.sleep(5)

        list(tag_name("input"))[0].clear()  # select NIC
        time.sleep(5)
        list(tag_name("input"))[0].send_keys(he_nic)
        time.sleep(5)

        class_name("btn-default").click() #confirm nic  
        time.sleep(5)

        class_name("btn-default").click() #select the appliance
        time.sleep(120)

        class_name("btn-default").click()  # select vnc
        time.sleep(2)

        class_name("btn-default").click()  # select cloud-init
        time.sleep(2)

        list(tag_name("input"))[0].send_keys(vm_fqdn)  # set VM FQDN
        time.sleep(2)
        class_name("btn-default").click()
        time.sleep(2)

        class_name("btn-default").click()  # set vm domain
        time.sleep(5)

        class_name("btn-default").click() #Automatically setup engine-setup on first boot
        time.sleep(5)

        list(tag_name("input"))[0].clear()  # Enter root password that will be used for engine appliance
        time.sleep(5)
        list(tag_name("input"))[0].send_keys(vm_password)
        time.sleep(2)
        class_name("btn-default").click()
        time.sleep(2)
        list(tag_name("input"))[0].clear()
        time.sleep(2)
        list(tag_name("input"))[0].send_keys(vm_password) #confirm appliance password
        time.sleep(2)
        class_name("btn-default").click()
        time.sleep(2)

        class_name("btn-default").click()  # leave ssh key empty
        time.sleep(2)

        list(tag_name("input"))[0].clear()  # enable ssh access for root
        time.sleep(2)
        list(tag_name("input"))[0].send_keys("yes")
        time.sleep(2)
        class_name("btn-default").click()
        time.sleep(2)

        class_name("btn-default").click()  # set vm disk size,default
        time.sleep(2)

        class_name("btn-default").click()  # set vm memory,default
        time.sleep(2)

        class_name("btn-default").click()  # set cpu type,default
        time.sleep(2)

        class_name("btn-default").click()  # set the number of vcpu
        time.sleep(2)

        list(tag_name("input"))[0].clear()  # set unicast MAC
        time.sleep(2)
        list(tag_name("input"))[0].send_keys(vm_mac)
        time.sleep(2)
        class_name("btn-default").click()
        time.sleep(2)

        class_name("btn-default").click()  # network,default DHCP
        time.sleep(2)

        class_name("btn-default").click()  # resolve hostname
        time.sleep(2)

        list(tag_name("input"))[0].clear()  # set engine admin password
        time.sleep(2)
        list(tag_name("input"))[0].send_keys(engine_password)
        time.sleep(2)
        class_name("btn-default").click()
        time.sleep(2)
        list(tag_name("input"))[0].clear()
        time.sleep(2)
        list(tag_name("input"))[0].send_keys(engine_password) #confirm the engine password again
        time.sleep(2)
        class_name("btn-default").click()
        time.sleep(2)

        class_name("btn-default").click()  # set the name of SMTP
        time.sleep(2)

        class_name("btn-default").click()  # set the port of SMTP,default 25
        time.sleep(2)

        class_name("btn-default").click()  # set email address
        time.sleep(2)

        class_name("btn-default").click()  # set comma-separated email address
        time.sleep(5)

        class_name("btn-default").click()  # confirm the configuration
        
    elif rhhi_version == "2.0":
        log.info("rhhi_version is 2.0 & configuring HE")
        xpaths("//input[@type='checkbox']")[0].click()              # uncheck Auto-import Appliance
        time.sleep(5)
        xpath("//input[@placeholder='Installation File Path']").clear()
        time.sleep(2)
        xpath("//input[@placeholder='Installation File Path']").send_keys(rhvm_appliance_path) # Enter installation file path
        time.sleep(2)
        xpath("//input[@placeholder='Number of CPUs']").clear()
        time.sleep(2)
        xpath("//input[@placeholder='Number of CPUs']").send_keys(no_of_cpus)                 # Enter no.of cpu cores
        time.sleep(2)
        xpath("//input[@placeholder='Disk Size']").clear()
        time.sleep(2)
        xpath("//input[@placeholder='Disk Size']").send_keys(mem_size)                # Enter no.of memory size of HE VM
        time.sleep(2)
        xpath("//input[@title='Enter the MAC address for the VM.']").clear()
        time.sleep(2)
        xpath("//input[@title='Enter the MAC address for the VM.']").send_keys(vm_mac) # Enter mac address of the HE VM
        time.sleep(2)
        xpath("//input[@placeholder='engine-host.example.com']").clear()
        time.sleep(2)
        xpath("//input[@placeholder='engine-host.example.com']").send_keys(host_ip)  # Enter Hosted engine FQDN
        time.sleep(2)
        xpath("//input[@title='Enter the engine FQDN.']").clear()
        time.sleep(2)
        xpath("//input[@title='Enter the engine FQDN.']").send_keys(vm_fqdn)  # Enter Hosted engine FQDN
        time.sleep(2)
        xpath("//input[@type='password']").clear()
        time.sleep(2)
        xpath("//input[@type='password']").send_keys(vm_password)  # Enter Hosted engine Root password
        time.sleep(2)
        xpaths("//input[@type='password']")[1].send_keys(vm_password)  # Confirm Hosted Engine root password
        time.sleep(5)
        xpath("//button[@class='btn btn-primary wizard-pf-next']").click()  #proceed to Engine tab by clicking on next
        time.sleep(10)
        log.info("Inside Engine tab")
        xpath("//input[@title='Enter the admin portal password.']").send_keys(engine_password) #Enter Admin portal password
        time.sleep(2)
        xpath("//input[@title='Confirm the admin portal password.']").send_keys(engine_password) # confirm Admin portal password
        time.sleep(2)
        xpath("//button[@class='btn btn-primary wizard-pf-next']").click()  # proceed to Review tab by clicking on next
        time.sleep(10)
        xpath("//button[@class='btn btn-primary wizard-pf-next']").click()  # proceed to preview tab and click on execute
        
        #Add code here to check if Hosted engine has been deployed, not aware of the command as of today.
        
        log.info("Inside Storage tab")
        xpath("//input[@placeholder='Disk Size']").clear()  # clear the disk size value
        time.sleep(2)
        xpath("//input[@placeholder='Disk Size']").send_keys(vm_disk_size)  # Enter the disk size for vm
        time.sleep(2)
        xpath("//button[@class='btn btn-default dropdown-toggle']").click() #select glusterfs for storage
        time.sleep(5)
        xpath("//li[@value='glusterfs']").click()
        time.sleep(5)
        xpath("//input[@placeholder='Enter the path for the shared storage you wish to use.']").clear()
        time.sleep(2)
        shared_storage = str(gluster_ip)+":/"+str(gluster_storage_path)
        xpath("//input[@placeholder='Enter the path for the shared storage you wish to use.']").send_keys(shared_storage) #set the path for shared storage
        time.sleep(2)
        mount_options = "backup-volfile-servers="+str(gluster_data_node2)+":"+str(gluster_arbiter_node)
        xpath("//input[@type='text']")[1].send_keys(mount_options) #Enter the mount options
        time.sleep(5)
        xpath("//button[@class='btn btn-primary wizard-pf-next']").click()  # proceed to Network tab by clicking on next
        time.sleep(10)
        xpath("//button[@class='btn btn-default dropdown-toggle']").click()  # select Bridge interface for storage
        time.sleep(5)
        xpath("//li[@value='"+file_path_interface1+"']").click() # Enter the interface
        time.sleep(5)
        xpaths("//input[@type='checkbox']")[0].click()  # uncheck configure iptables
        time.sleep(5)
        xpath("//input[@title='Enter a pingable gateway address.']").clear()
        time.sleep(2)
        xpath("//input[@title='Enter a pingable gateway address.']").send_keys(gw_address) #Enter gateway address
        time.sleep(2)
        xpath("//button[@class='btn btn-primary wizard-pf-next']").click()  # proceed to Review tab by clicking on next
        time.sleep(10)
        xpath("//button[@class='btn btn-primary wizard-pf-finish").click() # start deployment
    
    else:
        log.error("rhhi version specified in conf file is not present")
    
    

def check_he_is_deployed(host_ip, host_user, host_password):
    """
    Purpose:
        Check the HE is deployed on the host
    """
    with settings(
        warn_only=True,
        host_string=host_user + '@' + host_ip,
        password=host_password):
        
        while (True):
            cmd = "hosted-engine --vm-status | grep 'Engine status'"
            ret = run(cmd)
            if not ret.__contains__('"health": "good", "vm": "up"'):
                log.info("Waiting for HE to be deployed on host %s" % host_ip)
            else:
                log.info ("HE is deployed on %s" % host_ip)
                break
            

        cmd = "find /var/log -type f |grep ovirt-hosted-engine-setup-.*.log"
        ret = run(cmd)
        if ret.succeeded == True:
            log.info("Hosted engine setup log found")
        else:
            log.error("No hosted engine log found")
        
        cmd = "grep 'Hosted Engine successfully deployed' %s" % ret
        ret = run(cmd)
        if ret.succeeded == True:
            log.info("Found the successfully message in the setup log %s" % ret)
        else:
            log.error("Not found the successfully message in the setup log %s" % ret)
                                   

def generate_keys():
    """
        Purpose:
            Generate keys on the first node
        """
    with settings(
        warn_only=True,
        host_string=host_user + '@' + host_ip,
        password=host_password):
        cmd = run("echo -e  'y\n'|ssh-keygen -t rsa -f /root/.ssh/id_rsa -q -P '' ")
        ret=run(cmd)
        if ret.succeeded == True:
            log.info("Successfully generated keys on the first host %s" % host_ip)
        elif ret!=0:
            log.info("Keys already exists and overridden")
        else:
            log.info("could not generate keys")


def copy_keys():
    """
        Purpose:
            copy  keys from first node to all other nodes.
        """
    gluster_dict = {'gluster_data_node1': gluster_data_node1,
                    'gluster_data_node2': gluster_data_node2,
                    'gluster_arbiter_node': gluster_arbiter_node
                    }
    for gluster_node_name, gluster_node_ip in gluster_dict.items():
        with settings(
            warn_only=True,
            host_string=host_user + '@' + host_ip,
            password=host_password):
            cmd0 = "echo '%s' > password.txt" % host_password
            run(cmd0)
            cmd1 = "sshpass -f password.txt ssh-copy-id -i /root/.ssh/id_rsa -o StrictHostKeyChecking=no -f root" + '@' + \
                   gluster_node_ip
            ret = run(cmd1)
            if ret.__contains__("Number of key(s) added: 1"):
                log.info("Successfully copied keys to %s" % gluster_node_ip)
            else:
                log.info("Could not copy keys to %s" % gluster_node_ip)
