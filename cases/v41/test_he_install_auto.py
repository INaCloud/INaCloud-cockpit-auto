# Check he install auto.py

#from pages.common.he_install import *
#from pages.common.he_install_auto import *
from cases import CONF
from selenium import webdriver
from fabric.api import run, settings, put, local, get, env
from vncdotool import api
from HTMLParser import HTMLParser
#import logging
#import logging.config
import time, os, re, urllib2

from utils.log import Log
log = Log()

host_ip, host_user, host_password, browser = CONF.get('common').get(
    'host_ip'), CONF.get('common').get('host_user'), CONF.get('common').get(
        'host_password'), CONF.get('common').get('browser')

nfs_ip, nfs_password, nfs_storage_path, rhvm_appliance_path, vm_mac, vm_fqdn, vm_ip, vm_password, engine_password, auto_answer = CONF.get(
    'hosted_engine'
).get('nfs_ip'), CONF.get('hosted_engine').get('nfs_password'), CONF.get(
    'hosted_engine'
).get('he_install_nfs'), CONF.get('hosted_engine').get(
    'rhvm_appliance_path'
), CONF.get('hosted_engine').get('he_vm_mac'), CONF.get('hosted_engine').get(
    'he_vm_fqdn'), CONF.get('hosted_engine').get('he_vm_ip'), CONF.get(
        'hosted_engine').get('he_vm_password'), CONF.get('hosted_engine').get(
            'engine_password'), CONF.get('hosted_engine').get('auto_answer')


env.host_string = host_user + '@' + host_ip
env.password = host_password

"""
dirname = os.path.dirname(os.path.dirname(__file__))
conf_path = os.path.join(dirname + "/logger.conf")
logging.config.fileConfig(conf_path)
log = logging.getLogger("sherry")
"""

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
    log.info("Getting the latest rhvm appliance...")
    req = urllib2.Request(appliance_path)
    response = urllib2.urlopen(req)
    rhvm_appliance_html = response.read()

    # Parse the html
    mp = MyHTMLParser()
    mp.feed(rhvm_appliance_html)
    mp.close()

    # Get the latest rhvm appliance url link
    mp.a_texts.sort()
    latest_rhvm_appliance_name = mp.a_texts[-1]

    latest_rhvm_appliance_link = None
    for link in mp.links:
        if re.search(latest_rhvm_appliance_name, link):
            latest_rhvm_appliance_link = link

    latest_rhvm_appliance = appliance_path + latest_rhvm_appliance_link

    return latest_rhvm_appliance

def init_browser():
    if browser == 'firefox':
        driver = webdriver.Firefox()
        driver.implicitly_wait(20)
        driver.root_uri = "https://{}:9090".format(host_ip)
        return driver
    elif browser == 'chrome':
        driver = webdriver.Chrome()
        driver.implicitly_wait(20)
        driver.root_uri = "https://{}:9090".format(host_ip)
        return driver
        #return None
    else:
        raise NotImplementedError

def he_install_auto(host_dict, nfs_dict, install_dict, vm_dict):
    host_ip = host_dict['host_ip']
    host_user = host_dict['host_user']
    host_password = host_dict['host_password']
    if 'cockpit_port' in host_dict:
        cockpit_port = host_dict['cockpit_port']
    else:
        cockpit_port = "9090"
    root_uri = "https://" + host_ip + ":" + cockpit_port
    nfs_ip = nfs_dict['nfs_ip']
    nfs_password = nfs_dict['nfs_password']
    nfs_path = nfs_dict['nfs_path']

    rhvm_appliance_path = install_dict['rhvm_appliance_path']
    he_nic = install_dict['he_nic']

    vm_mac = vm_dict['vm_mac']
    vm_fqdn = vm_dict['vm_fqdn']
    vm_ip = vm_dict['vm_ip']
    vm_password = vm_dict['vm_password']
    engine_password = vm_dict['engine_password']
    auto_answer = vm_dict['auto_answer']

    rhn_user = RHN_USER
    rhn_password = RHN_PASSWORD

    # Subscription to RHSM via CMD
    log.info("Subscripation to RHN or RHSM ,then enable rhvh repos...")
    with settings(
            warn_only=True,
            host_string=host_user + '@' + host_ip,
            password=host_password):
        cmd0 = "subscription-manager register --username=%s --password=%s" % (
            rhn_user, rhn_password)
        run(cmd0)
        cmd1 = "subscription-manager attach --auto"
        run(cmd1)
        cmd2 = "subscription-manager repos --enable=rhel-7-server-rhvh-4*"
        run(cmd2)
        cmd3 = "subscription-manager repos --list-enable |grep 'Repo ID' |grep 'rhvh'"
        output = run("os.popen(cmd3).read()")
        if output == 0:
            raise RuntimeError("Failed to find rhvh repos")

    # Delete the files in nfs storage path
    log.info("Cleaning the nfs storage...")
    with settings(
            warn_only=True, host_string='root@' + nfs_ip,
            password=nfs_password):
        run("rm -rf %s/*" % nfs_path)
        run("service nfs restart", quiet=True)

    # Get the rhvm_appliance from rhvm_appliance_path
    rhvm_appliance_link = get_latest_rhvm_appliance(rhvm_appliance_path)
    local_rhvm_appliance = "/root/%s" % rhvm_appliance_link.split('/')[-1]
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
    log.info("Adding the host to /etc/hosts and installing the rhvm appliance...")
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

    time.sleep(2)
    log.info("Deploying the HostedEngine...")
    dr = webdriver.Chrome()
    dr.get(root_uri)
    time.sleep(5)
    id = dr.find_element_by_id
    class_name = dr.find_element_by_class_name
    tag_name = dr.find_elements_by_tag_name
    xpath = dr.find_element_by_xpath

    # Login to cockpit
    log.info("Logining to the cockpit...")
    id("login-user-input").send_keys(host_user)
    time.sleep(2)
    id("login-password-input").send_keys(host_password)
    time.sleep(2)
    id("login-button").click()
    time.sleep(5)
    dr.get(root_uri + "/ovirt-dashboard")
    dr.switch_to_frame("cockpit1:localhost/ovirt-dashboard")
    xpath("//a[@href='#/he']").click()
    time.sleep(5)

    log.info("Deploying the HostedEngine step by step...")
    class_name("btn-primary").click()  # Click to deploy HE
    time.sleep(10)
    class_name("btn-default").click()  # click next button,continue yes
    # dr.implicitly_wait(60)
    time.sleep(60)
    #class_name("btn-default").click()  # click next button,download the rhvm-appliance
    #time.sleep(2400)
    #class_name("btn-default").click()  # click next button,confirm gpg key
    #time.sleep(2)
    #class_name("btn-default").click()  # double to confirm gpg key,install rhvm-appliance
    #time.sleep(120)

    class_name("btn-default").click()  # specify storage mode
    time.sleep(2)

    nfs_storage = nfs_ip + ':' + nfs_path
    log.info("Selecting the NFS storage...")
    list(tag_name("input"))[0].send_keys(nfs_storage)  # NFS storage path
    time.sleep(2)
    class_name("btn-default").click()
    time.sleep(5)

    log.info("Confirming the iptables...")
    class_name("btn-default").click()  # iptables default confirm
    time.sleep(2)

    log.info("Confirming the gateway ip...")
    class_name("btn-default").click()  # gateway ip confirm
    time.sleep(2)

    log.info("Selecting the NIC...")
    list(tag_name("input"))[0].clear()  # select NIC
    time.sleep(2)
    list(tag_name("input"))[0].send_keys(he_nic)
    time.sleep(2)
    class_name("btn-default").click()
    time.sleep(2)

    log.info("Selecting the rhvm appliance...")
    class_name("btn-default").click()  # select appliance
    time.sleep(120)

    log.info("Seclecting the VNC...")
    class_name("btn-default").click()  # select vnc
    time.sleep(2)

    log.info("Seclecting the cloud-init mode...")
    class_name("btn-default").click()  # select cloud-init
    time.sleep(2)

    log.info("Setting the VM FQDN...")
    class_name("btn-default").click()  # select Generate
    time.sleep(2)

    list(tag_name("input"))[0].send_keys(vm_fqdn)  # set VM FQDN
    time.sleep(2)
    class_name("btn-default").click()
    time.sleep(2)

    log.info("Setting the VM domain...")
    class_name("btn-default").click()  # set vm domain
    time.sleep(2)

    log.info("Selecting the automatically engine-setup and restart the engine-vm...")
    class_name("btn-default").click()  # select automatically engine-setup
    time.sleep(2)
    class_name("btn-default").click()  # automatically restart the engine-vm
    time.sleep(2)
    """
    list(tag_name("input"))[0].clear()      # Manual setup
    time.sleep(2)
    list(tag_name("input"))[0].send_keys("No")
    time.sleep(2)
    class_name("btn-default").click()
    time.sleep(2)
    """
    log.info("Setting the root password...")
    list(tag_name("input"))[0].clear()  # set root password
    time.sleep(2)
    list(tag_name("input"))[0].send_keys(vm_password)
    time.sleep(2)
    class_name("btn-default").click()
    time.sleep(2)
    list(tag_name("input"))[0].clear()
    time.sleep(2)
    list(tag_name("input"))[0].send_keys(vm_password)
    time.sleep(2)
    class_name("btn-default").click()
    time.sleep(2)

    log.info("Setting the ssh login...")
    class_name("btn-default").click()  # leave ssh key empty
    time.sleep(2)

    list(tag_name("input"))[0].clear()  # enable ssh access for root
    time.sleep(2)
    list(tag_name("input"))[0].send_keys("yes")
    time.sleep(2)
    class_name("btn-default").click()
    time.sleep(2)

    log.info("Setting the VM disk, memory, type, vcpu...")
    class_name("btn-default").click()  # set vm disk,default
    time.sleep(2)

    class_name("btn-default").click()  # set vm memory,default
    time.sleep(2)

    class_name("btn-default").click()  # set cpu type,default
    time.sleep(2)

    class_name("btn-default").click()  # set the number of vcpu
    time.sleep(2)

    log.info("Seting VM MAC and DHCP...")
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

    log.info("Setting the engine admin password...")
    list(tag_name("input"))[0].clear()  # set engine admin password
    time.sleep(1)
    list(tag_name("input"))[0].send_keys(engine_password)
    time.sleep(1)
    class_name("btn-default").click()
    time.sleep(1)
    list(tag_name("input"))[0].clear()
    time.sleep(1)
    list(tag_name("input"))[0].send_keys(engine_password)
    time.sleep(1)
    class_name("btn-default").click()
    time.sleep(2)

    log.info("Configuring the SMTP service and email address...")
    class_name("btn-default").click()  # set the name of SMTP
    time.sleep(1)

    class_name("btn-default").click()  # set the port of SMTP,default 25
    time.sleep(1)

    class_name("btn-default").click()  # set email address
    time.sleep(1)

    class_name("btn-default").click()  # set comma-separated email address
    time.sleep(5)

    log.info("Confirm the configuration and deployment...")
    class_name("btn-default").click()  # confirm the configuration
    time.sleep(750)

    with settings(
            warn_only=True, host_string='root@' + vm_ip, password='redhat'):
        cmd1 = "echo '%s  %s' >> /etc/hosts" % (host_ip, host_name)
        run(cmd1)
        cmd2 = "echo '%s  %s' >> /etc/hosts" % (vm_ip, vm_fqdn)
        run(cmd2)

    time.sleep(750)

    dr.quit()




def check_he_is_deployed(host_ip, host_user, host_password):
    """
    Purpose:
        Check the HE is deployed on the host
    """
    with settings(
            warn_only=True,
            host_string=host_user + '@' + host_ip,
            password=host_password):
        cmd = "hosted-engine --check-deployed"
        ret = run(cmd)
        assert ret.succeeded, "HE is not deployed on %s" % host_ip

        cmd = "find /var/log -type f |grep ovirt-hosted-engine-setup-.*.log"
        ret = run(cmd)
        assert ret.succeeded, "No hosted engine setup log found"

        cmd = "grep 'Hosted Engine successfully deployed' %s" % ret
        ret = run(cmd)
        assert ret.succeeded, "Not found the successfully message in the setup log %s" % ret


<<<<<<< HEAD
"""
@pytest.fixture(scope="session", autouse=True)
def _environment(request):
    with settings(warn_only=True):
        cmd = "rpm -qa|grep cockpit-ovirt"
        cockpit_ovirt_version = run(cmd)

        cmd = "rpm -q imgbased"
        result = run(cmd)
        if result.failed:
            cmd = "cat /etc/redhat-release"
            redhat_release = run(cmd)
            request.config._environment.append((
                'redhat-release', redhat_release))
        else:
            cmd_imgbase = "imgbase w"
            output_imgbase = run(cmd_imgbase)
            rhvh_version = output_imgbase.split()[-1].split('+')[0]
            request.config._environment.append(('rhvh-version', rhvh_version))

        request.config._environment.append((
            'cockpit-ovirt', cockpit_ovirt_version))


@pytest.fixture(scope="module")
def firefox(request):
    pass
"""



=======
>>>>>>> 4839b3af42b4ea58c4d0e8e3339bedac31c4fe47
def test_18667(ctx):
    """
    Purpose:
        RHEVM-18667
        Setup Hosted Engine with OVA(engine-appliance-rpm)
    """
    # Get the nic from host_ip
    cmd = "ip a s|grep %s" % host_ip
    output = run(cmd)
    he_nic = output.split()[-1]

    host_dict = {'host_ip': host_ip,
    'host_user': host_user,
    'host_password': host_password}

    nfs_dict = {
    'nfs_ip': nfs_ip,
    'nfs_password': nfs_password,
    'nfs_path': nfs_storage_path}

    install_dict = {
    'rhvm_appliance_path': rhvm_appliance_path,
    'he_nic': he_nic}

    vm_dict = {
    'vm_mac': vm_mac,
    'vm_fqdn': vm_fqdn,
    'vm_ip': vm_ip,
    'vm_password': vm_password,
    'engine_password': engine_password,
    'auto_answer': auto_answer
    }

    try:
        #he_install(host_dict, nfs_dict, install_dict, vm_dict)
        he_install_auto(host_dict, nfs_dict, install_dict, vm_dict)
        log.info("Deploy HE finished!")
    except Exception as e:
        log.exception(e)
        return False
    return True

    # Check the hosted engine is deployed
    check_he_is_deployed(host_ip, host_user, host_password)


def runtest():
    ctx = init_browser()
    test_18667(ctx)
    ctx.close()

#TO DO
