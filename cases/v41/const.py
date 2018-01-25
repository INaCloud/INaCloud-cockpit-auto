# test_common_ui 
common_ui = [
    'check_another_server', 'check_dashboard_cpu', 'check_dashboard_memory', 
    'check_dashboard_network', 'check_dashboard_disk_io', 
    'check_ui_logs', 
    'check_ui_services', 
    'check_allowunknown_default', 'check_allowunknown_true',
    'check_allowunknown_true_wrong_account',
    'check_allowunknown_true_remote_closed',
    'check_allowunknown_true_wrong_address',
    'check_allowunknown_true_empty_username', 'check_system_login_host',
    'check_system_configure_hostname', 'check_system_configure_timezone',
    'check_system_configure_time', 'check_change_system_performance_profile'
]
common_ui_id = [18371, 18372, 18373, 18374, 18375, 
                18394, 18392, 18379, 18380, 18381, 
                18382, 18383, 18384, 18377, 18385, 
                18386, 18387, 18390]


# test_common_tools
common_tools = [
    'check_create_account', 'check_create_diagnostic'
]
common_tools_id = [18410, 18416]


# test_common_tools_subscription
common_tools_subscription = [
    'check_subscription_rhsm', 'check_subscription_key', 'check_subscription_password'
]
common_tools_subscription_id = [18412, 18413, 18414]


# test_dashboard_nodectl
dashboard_nodectl = [
    'check_nodectl_help_func', 'check_nodectl_info_func',
    'check_nodectl_check_func', 'check_nodectl_debug_func',
    'check_nodectl_json_func', 'check_nodectl_motd_func',
    'check_nodectl_banner_func'
]
dashboard_nodectl_id = [18545, 18547, 18550, 18551, 18552, 18830, 18831]


# test_dashboard_ui
dashboard_ui = [
    'check_node_status_func', 'check_node_health_func', 'check_node_info_func',
    'check_network_func', 'check_system_log_func', 'check_storage_func',
    'check_ssh_key_func'
]
dashboard_ui_id = [18534, 18535, 18536, 18540, 18541, 18542, 18543]


# test_dashboard_ui_efi
dashboard_ui_efi = [
    'check_nodestatus_efi'
]
dashboard_ui_efi_id = [18539]


# test_dashboard_ui_fc
dashboard_ui_fc = [
    'check_nodestatus_fc'
]
dashboard_ui_fc_id = [18538]


# test_he_install
he_install = ['check_he_install']
he_install_id = [18667, 18674, 18675, 18677]


# test_he_install_bond
he_install_bond = ['check_he_install_bond']
he_install_bond_id = [18674]


# test_he_install_bv
he_install_bv = ['check_he_install_bv']
he_install_bv_id = [18677]


# test_he_install_vlan
he_install_vlan = ['check_he_install_vlan']
he_install_vlan_id = [18675]


# test_he_install_non_default_port
he_install_non_default_port = ['check_he_install_non_default']
he_install_non_default_port_id = [18667]


# test_he_install_redeploy
he_install_redeploy = ['check_he_install_redploy']
he_install_redeploy_id = [18686]


# test_he_info
he_info = [
    'check_engine_status_func', 'check_vm_status_func',
    'check_three_buttons_func', 'check_he_running_on_host_func',
    'check_no_password_saved_func', 'check_add_additional_host', 
    'check_put_local_maintenance', 'check_remove_from_maintenance', 
    'check_put_global_maintenance'
]
he_info_id = [18669, 18670, 18671, 18672, 18685, 18668, 18678, 18679, 18680]


# test_he_info_add_host
he_info_add_host = [
    'check_add_additional_host', 'check_put_local_maintenance', 
    'check_remove_from_maintenance', 'check_put_global_maintenance'
]
he_info_add_host_id = [18668, 18678, 18679, 18680]


# test_vm_registerd
vm_registerd = [
    'check_running_vms_register_func', 'check_vdsm_func',
    'check_vm_login_logout_engine_func', 'check_vm_refresh_func',
    'check_non_root_alert_func' 
]
vm_registerd_id = [18805, 18808, 18809, 18811, 18813]


# test_vm_unregisterd
vm_unregisterd = [
    'check_running_vms_unregister_func', 
    'check_vms_in_cluster_unregister_func' 
]
vm_unregisterd_id = [18803, 18804]

deployment_cases_RHHI = [
    'check_engine_lv_of_type_thick_and_volume_of_type_replicate',
    'check_gluster_packages_presence_on_rhvh_node', 
    'check_glusterfs_firewall_service_availability_with_default_firewallzone',
    'check_cockpitui_should_be_reachable_for_the_user',
    'check_option_to_start_with_gluster_deployment',
    'check_saving_the_generated_gdeploy_config_file',
    'check_cockpit_gdeploy_plugin_provides_redeploy_button',
    'check_cleanup_of_gluster_setup_done',
    'check_deployment_with_hostedengine_on_gluster',
    'check_gluster_deployment_wizard',
    'validate_host_deployment_tab',
    'check_back_and_cancel_buttons_on_gdeploy_wizard',
    'validate_arbiter_volume_creation',
    'validate_packages_tab',
    'check_gdeploy_stops_deploying_when_error_is_encountered'
    
]

deployment_cases_RHHI_id =['RHHI-138', 'RHHI-118', 'RHHI-119', 'RHHI-121', 'RHHI-122', 'RHHI-127', 'RHHI-129',
                           'RHHI-130', 'RHHI-132', 'RHHI-144', 'RHHI-145', 'RHHI-148', 'RHHI-147', 'RHHI-146',
                           'RHHI-140']