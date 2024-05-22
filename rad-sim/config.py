import os
import math
import yaml
import sys
import shutil
from itertools import repeat
from copy import deepcopy

def parse_config_file(config_filename, booksim_params, radsim_header_params, radsim_knobs, cluster_knobs):
    with open(config_filename, 'r') as yaml_config:
        config = yaml.safe_load(yaml_config)
    
    config_counter = 0
    for config_section in config:
        print(config_section + ':')
        for param_category, param in config[config_section].items():
            if 'config' in config_section and (isinstance(param, dict)):
                print('     ' + param_category + ':')
                for param, param_value in param.items():
                    print('         ' + param, param_value)
                    param_name = param_category + '_' + param
                    invalid_param = True
                    if param_name in booksim_params[config_counter]:
                        booksim_params[config_counter][param_name] = param_value
                        invalid_param = False
                    if param_name in radsim_header_params[config_counter]:
                        radsim_header_params[config_counter][param_name] = param_value
                        invalid_param = False
                    if param_name in radsim_knobs[config_counter]:
                        radsim_knobs[config_counter][param_name] = param_value
                        invalid_param = False
                    if param_name == "dram_config_files":
                        print('param_value')
                        print(config_counter)
                        print(param_value)

                    if invalid_param:
                        print("Config Error: Parameter " + param_name + " is invalid!")
                        exit(1)
            elif config_section == "cluster":
                param_value = param #bc no subsection, so correction
                param = param_category #bc no subsection, so correction
                print('     ' + param, param_value)
                if 'topology' in param or 'configs' in param:
                    param_name = 'cluster_' + param
                else:
                    param_name = param
                #print(param_name)
                #TODO: below doesnt rlly make sense for cluster-level params, fix up
                invalid_param = True
                if param_name in cluster_knobs:
                    cluster_knobs[param_name] = param_value
                    invalid_param = False
                # if param_name in booksim_params[config_counter]:
                #     booksim_params[config_counter][param_name] = param_value
                #     invalid_param = False
                # if param_name in radsim_header_params[config_counter]:
                #     radsim_header_params[config_counter][param_name] = param_value
                #     invalid_param = False
                # if param_name in radsim_knobs[config_counter]:
                #     radsim_knobs[config_counter][param_name] = param_value
                #     invalid_param = False
                if invalid_param:
                    print("Config Error: Parameter " + param_name + " is invalid!")
                    exit(1)
        config_counter += 1

    for i in range(0, num_configs):
        radsim_knobs[i]["radsim_user_design_root_dir"] = cluster_knobs["radsim_root_dir"] + "/example-designs/" + radsim_knobs[i]["design_name"]

    #commented out below bc yaml file now explicitly sets sim_driver_perid
    # longest_clk_period = radsim_knobs["design_clk_periods"][0]
    # for p in radsim_knobs["design_clk_periods"]:
    #     if p > longest_clk_period:
    #         longest_clk_period = p
    # radsim_knobs["sim_driver_period"] = longest_clk_period
    

def print_config(booksim_params, radsim_header_params, radsim_knobs):
    print("*****************************")
    print("**  RAD-FLOW CONFIGURATION **")
    print("*****************************")
    for param in booksim_params:
        print(param + " : " + str(booksim_params[param]))
    for param in radsim_header_params:
        print(param + " : " + str(radsim_header_params[param]))
    for param in radsim_knobs:
        print(param + " : " + str(radsim_knobs[param]))


def generate_booksim_config_files(booksim_params, radsim_header_params, radsim_knobs, cluster_knobs):
    for curr_config_num in range(num_configs):
        for i in range(booksim_params[curr_config_num]["noc_num_nocs"]):
            booksim_config_file = open(booksim_params[curr_config_num]["radsim_root_dir"] + "/sim/noc/noc" + str(i) + "_config"+ str(curr_config_num) + "_config_akb_test", "w") #AKB created temp file to test

            # Booksim topology configuration
            booksim_config_file.write("// Topology\n")
            noc_topology = booksim_params[curr_config_num]["noc_topology"][i]
            noc_type = booksim_params[curr_config_num]["noc_type"][i]
            if noc_topology == "mesh" or noc_topology == "torus":
                # A 3D RAD instance is modeled as a concenterated mesh NoC
                if noc_type == "2d":
                    booksim_config_file.write("topology = " + noc_topology + ";\n")
                elif noc_type == "3d" and noc_topology == "mesh":
                    booksim_config_file.write("topology = cmesh;\n")
                else:
                    print("Config Error: noc_type parameter value has to be 2d or 3d")
                    exit(1)

                # Booksim does not support assymetric meshes so it is simplified as a square mesh assuming that a simple dim
                # order routing will never use the links/routers outside the specified grid
                noc_dim_x = booksim_params[curr_config_num]["noc_dim_x"][i]
                noc_dim_y = booksim_params[curr_config_num]["noc_dim_y"][i]
                larger_noc_dim = noc_dim_x
                if noc_dim_y > noc_dim_x:
                    larger_noc_dim = noc_dim_y
                booksim_config_file.write("k = " + str(larger_noc_dim) + ";\n")
                booksim_config_file.write("n = 2;\n")

                # Booksim supports concentrated meshes of 4 nodes per router only -- RAD-Sim works around that by modeling 
                # 3D RAD instances as a concentrated mesh of FPGA node, base die node, and two "empty" nodes by adjusting 
                # their IDs
                if noc_type == "3d":
                    radsim_header_params[curr_config_num]["noc_num_nodes"][i] = (larger_noc_dim * larger_noc_dim * 4)
                    #TODO: make changes to have per-RAD booksim config too. for now, just hacky workaround to get radsim_knobs set
                    #for j in range(cluster_knobs["num_rads"]):
                        #radsim_knobs[j]["noc_num_nodes"][i] = larger_noc_dim * larger_noc_dim * 4
                    radsim_knobs[curr_config_num]["noc_num_nodes"][i] = larger_noc_dim * larger_noc_dim * 4
                    booksim_config_file.write("c = 4;\n")
                    booksim_config_file.write("xr = 2;\n")
                    booksim_config_file.write("yr = 2;\n")
                else:
                    radsim_header_params[curr_config_num]["noc_num_nodes"][i] = (larger_noc_dim * larger_noc_dim)
                    #TODO: make changes to have per-RAD booksim config AND radsim_header_params too. for now, just hacky workaround to get radsim_knobs set
                    # for j in range(cluster_knobs["num_rads"]):
                    #     radsim_knobs[j]["noc_num_nodes"][i] = larger_noc_dim * larger_noc_dim
                    radsim_knobs[curr_config_num]["noc_num_nodes"][i] = larger_noc_dim * larger_noc_dim

            elif noc_topology == "anynet":
                booksim_config_file.write("topology = anynet;\n")
                booksim_config_file.write("network_file = " + booksim_params[curr_config_num]["noc_anynet_file"][i] + ";\n")
                if radsim_header_params[curr_config_num]["noc_num_nodes"][i] == 0:
                    print("Config Error: Number of nodes parameter missing for anynet NoC topologies!")
                    exit(1)

            else:
                print("Config Error: This NoC topology is not supported by RAD-Sim!")
                exit(1)
            booksim_config_file.write("\n")

            # Booksim routing function configuration
            booksim_config_file.write("// Routing\n")
            booksim_config_file.write("routing_function = " + booksim_params[curr_config_num]["noc_routing_func"][i] + ";\n")
            booksim_config_file.write("\n")

            # Booksim flow control configuration
            booksim_config_file.write("// Flow control\n")
            noc_vcs = booksim_params[curr_config_num]["noc_vcs"][i]
            noc_num_packet_types = booksim_params[curr_config_num]["noc_num_packet_types"][i]
            if noc_vcs % noc_num_packet_types != 0:
                print("Config Error: Number of virtual channels has to be a multiple of the number of packet types!")
                exit(1)
            if noc_num_packet_types > 5:
                print("Config Error: RAD-Sim supports up to 5 packet types")
                exit(1)
            noc_num_vcs_per_packet_type = int(noc_vcs / noc_num_packet_types)
            booksim_config_file.write("num_vcs = " + str(noc_vcs) + ";\n")
            booksim_config_file.write("vc_buf_size = " + str(booksim_params[curr_config_num]["noc_vc_buffer_size"][i]) + ";\n")
            booksim_config_file.write("output_buffer_size = "+ str(booksim_params[curr_config_num]["noc_output_buffer_size"][i])+ ";\n")
            booksim_flit_types = ["read_request", "write_request", "write_data", "read_reply", "write_reply"]
            vc_count = 0
            for t in range(noc_num_packet_types):
                booksim_config_file.write(booksim_flit_types[t] + "_begin_vc = " + str(vc_count) + ";\n")
                vc_count = vc_count + noc_num_vcs_per_packet_type
                booksim_config_file.write(booksim_flit_types[t] + "_end_vc = " + str(vc_count - 1) + ";\n")
            booksim_config_file.write("\n")

            # Booksim router architecture and delays configuration
            booksim_config_file.write("// Router architecture & delays\n")
            booksim_config_file.write("router = " + booksim_params[curr_config_num]["noc_router_uarch"][i] + ";\n")
            booksim_config_file.write("vc_allocator = " + booksim_params[curr_config_num]["noc_vc_allocator"][i] + ";\n")
            booksim_config_file.write("sw_allocator = " + booksim_params[curr_config_num]["noc_sw_allocator"][i] + ";\n")
            booksim_config_file.write("alloc_iters = 1;\n")
            booksim_config_file.write("wait_for_tail_credit = 0;\n")
            booksim_config_file.write("credit_delay = " + str(booksim_params[curr_config_num]["noc_credit_delay"][i]) + ";\n")
            booksim_config_file.write("routing_delay = " + str(booksim_params[curr_config_num]["noc_routing_delay"][i]) + ";\n")
            booksim_config_file.write("vc_alloc_delay = " + str(booksim_params[curr_config_num]["noc_vc_alloc_delay"][i]) + ";\n")
            booksim_config_file.write("sw_alloc_delay = " + str(booksim_params[curr_config_num]["noc_sw_alloc_delay"][i]) + ";\n")
            booksim_config_file.close()


def generate_radsim_params_header(radsim_header_params):
    radsim_params_header_file = open(radsim_header_params["radsim_root_dir"] + "/sim/radsim_defines_akb_test.hpp", "w") #AKB created temp file to test
    radsim_params_header_file.write("#pragma once\n\n")
    radsim_params_header_file.write("// clang-format off\n")
    radsim_params_header_file.write('#define RADSIM_ROOT_DIR "' + radsim_header_params["radsim_root_dir"] + '"\n\n')

    radsim_params_header_file.write("// NoC-related Parameters\n")
    # Finding maximum NoC payload width and setting its definition
    max_noc_payload_width = 0
    for w in radsim_header_params["noc_payload_width"]:
        if w > max_noc_payload_width:
            max_noc_payload_width = w
    radsim_params_header_file.write("#define NOC_LINKS_PAYLOAD_WIDTH   " + str(max_noc_payload_width) + "\n")
    # Finding maximum NoC VC count and setting definition for VC ID bitwidth
    max_noc_vcs = 0
    for v in radsim_header_params["noc_vcs"]:
        if v > max_noc_vcs:
            max_noc_vcs = v
    if max_noc_vcs == 1:
        max_vc_id_bitwidth = 1
    else:
        max_vc_id_bitwidth = int(math.ceil(math.log(max_noc_vcs, 2)))
    radsim_params_header_file.write("#define NOC_LINKS_VCID_WIDTH      " + str(max_vc_id_bitwidth) + "\n")
    # Setting definition for packet ID bitwidth as directly specified by the user
    packet_id_bitwidth = radsim_header_params["noc_packet_id_width"]
    radsim_params_header_file.write("#define NOC_LINKS_PACKETID_WIDTH  " + str(packet_id_bitwidth) + "\n")
    # Finding maximum number of packet types and setting definition for type ID bitwidth & generic packet type mappings
    # to Booksim flit types
    max_num_types = 0
    for t in radsim_header_params["noc_num_packet_types"]:
        if t > max_num_types:
            max_num_types = t
    if (max_num_types == 1):
        max_type_id_bitwidth = 1
    else:
        max_type_id_bitwidth = int(math.ceil(math.log(max_num_types, 2)))
    radsim_params_header_file.write("#define NOC_LINKS_TYPEID_WIDTH    " + str(max_type_id_bitwidth) + "\n")
    # Finding maximum NoC node count and setting definition for destination bitwidth
    max_num_nodes = 0
    for n in radsim_header_params["noc_num_nodes"]:
        if n > max_num_nodes:
            max_num_nodes = n
    max_destination_bitwidth = int(math.ceil(math.log(max_num_nodes, 2))) * 3 # TO-DO-MR: Multiply by 3 for (rad_id, node_id1, node_id0). If single RAD, node_id0 and node_id1 is the same. If not, node_id0 is portal and node_id1 is destination node on other RAD. 
    max_destination_field_bitwidth = int(math.ceil(math.log(max_num_nodes, 2))) # TO-DO-MR: Bitwidth of a single field of the destination described above.
    radsim_params_header_file.write("#define NOC_LINKS_DEST_WIDTH      " + str(max_destination_bitwidth) + "\n")

    dest_interface_bitwidth = int(math.ceil(math.log(radsim_header_params["noc_max_num_router_dest_interfaces"], 2)))
    radsim_params_header_file.write("#define NOC_LINKS_DEST_INTERFACE_WIDTH " + str(dest_interface_bitwidth) + "\n")
    radsim_params_header_file.write("#define NOC_LINKS_WIDTH           (NOC_LINKS_PAYLOAD_WIDTH + NOC_LINKS_VCID_WIDTH \
        + NOC_LINKS_PACKETID_WIDTH + NOC_LINKS_DEST_WIDTH + NOC_LINKS_DEST_INTERFACE_WIDTH)\n\n")

    radsim_params_header_file.write("// AXI Parameters\n")
    radsim_params_header_file.write("#define AXIS_MAX_DATAW " + 
        str(radsim_header_params["interfaces_max_axis_tdata_width"]) + "\n")
    radsim_params_header_file.write("#define AXI4_MAX_DATAW " + 
        str(radsim_header_params["interfaces_max_axi_data_width"]) + "\n")
    radsim_params_header_file.write("#define AXIS_USERW     " + 
        str(radsim_header_params["interfaces_axis_tuser_width"]) + "\n")
    radsim_params_header_file.write("#define AXI4_USERW     " + 
        str(radsim_header_params["interfaces_axi_user_width"]) + "\n")

    radsim_params_header_file.write("// (Almost always) Constant AXI Parameters\n")
    radsim_params_header_file.write("#define AXIS_STRBW  " + str(radsim_header_params["interfaces_axis_tstrb_width"]) + "\n")
    radsim_params_header_file.write("#define AXIS_KEEPW  " + str(radsim_header_params["interfaces_axis_tkeep_width"]) + "\n")
    radsim_params_header_file.write("#define AXIS_IDW    NOC_LINKS_PACKETID_WIDTH\n")
    radsim_params_header_file.write("#define AXIS_DESTW  NOC_LINKS_DEST_WIDTH\n")
    radsim_params_header_file.write("#define AXIS_DEST_FIELDW  " + str(max_destination_field_bitwidth) + "\n") # TO-DO-MR: Define parameter for destination field width (to separate 3 fields)
    radsim_params_header_file.write("#define AXI4_IDW    " + str(radsim_header_params["interfaces_axi_id_width"]) + "\n")
    radsim_params_header_file.write("#define AXI4_ADDRW  64\n")
    radsim_params_header_file.write("#define AXI4_LENW   8\n")
    radsim_params_header_file.write("#define AXI4_SIZEW  3\n")
    radsim_params_header_file.write("#define AXI4_BURSTW 2\n")
    radsim_params_header_file.write("#define AXI4_RESPW  2\n")
    radsim_params_header_file.write("#define AXI4_NODE_ADDRW " + str(max_destination_field_bitwidth) + "\n")
    radsim_params_header_file.write("#define AXI4_CTRLW  (AXI4_LENW + AXI4_SIZEW + AXI4_BURSTW)\n\n")

    radsim_params_header_file.write("// AXI Packetization Defines\n")
    radsim_params_header_file.write("#define AXIS_PAYLOADW (AXIS_MAX_DATAW + AXIS_USERW + 1)\n")
    radsim_params_header_file.write("#define AXIS_TLAST(t) t.range(0, 0)\n")
    radsim_params_header_file.write("#define AXIS_TUSER(t) t.range(AXIS_USERW, 1)\n")
    radsim_params_header_file.write("#define AXIS_TDATA(t) t.range(AXIS_MAX_DATAW + AXIS_USERW, AXIS_USERW + 1)\n")
    radsim_params_header_file.write("#define AXIS_TSTRB(t) t.range(AXIS_MAX_DATAW + AXIS_USERW + AXIS_STRBW, AXIS_MAX_DATAW + AXIS_USERW + 1)\n")
    radsim_params_header_file.write("#define AXIS_TKEEP(t) t.range(AXIS_MAX_DATAW + AXIS_USERW + AXIS_STRBW + AXIS_KEEPW, AXIS_MAX_DATAW + AXIS_USERW + AXIS_STRBW + 1)\n")
    radsim_params_header_file.write("#define AXIS_TID(t)   t.range(AXIS_MAX_DATAW + AXIS_USERW + AXIS_STRBW + AXIS_KEEPW + AXIS_IDW, AXIS_MAX_DATAW + AXIS_USERW + AXIS_STRBW + AXIS_KEEPW + 1)\n")
    radsim_params_header_file.write("#define AXIS_TDEST(t) t.range(AXIS_MAX_DATAW + AXIS_USERW + AXIS_STRBW + AXIS_KEEPW + AXIS_IDW + AXIS_DESTW, AXIS_MAX_DATAW + AXIS_USERW + AXIS_STRBW + AXIS_KEEPW + AXIS_IDW + 1)\n")
    radsim_params_header_file.write("#define AXIS_TUSER_RANGE(t, s, e) t.range(1 + e, 1 + s)\n")
    radsim_params_header_file.write("#define DEST_LOCAL_NODE(t) t.range(AXIS_DEST_FIELDW - 1, 0)\n") # TO-DO-MR: Extract local destination node from destination bitvector
    radsim_params_header_file.write("#define DEST_REMOTE_NODE(t) t.range(2 * AXIS_DEST_FIELDW - 1, AXIS_DEST_FIELDW)\n") # TO-DO-MR: Extract remote destination node from destination bitvector
    radsim_params_header_file.write("#define DEST_RAD(t) t.range(3 * AXIS_DEST_FIELDW - 1, 2 * AXIS_DEST_FIELDW)\n") # TO-DO-MR: Extract destination RAD from destination bitvector
    radsim_params_header_file.write("#define AXIS_TRANSACTION_WIDTH (AXIS_MAX_DATAW + AXIS_STRBW + AXIS_KEEPW + AXIS_IDW + AXIS_DESTW + AXIS_USERW + 1)\n")
    radsim_params_header_file.write("#define AXI4_PAYLOADW (AXI4_MAX_DATAW + AXI4_RESPW + AXI4_USERW + 1)\n")
    radsim_params_header_file.write("#define AXI4_LAST(t)  t.range(0, 0)\n")
    radsim_params_header_file.write("#define AXI4_USER(t)  t.range(AXI4_USERW, 1)\n")
    radsim_params_header_file.write("#define AXI4_RESP(t)  t.range(AXI4_RESPW + AXI4_USERW, AXI4_USERW + 1)\n")
    radsim_params_header_file.write("#define AXI4_DATA(t)  t.range(AXI4_MAX_DATAW + AXI4_RESPW + AXI4_USERW, AXI4_RESPW + AXI4_USERW + 1)\n")
    radsim_params_header_file.write("#define AXI4_CTRL(t)  t.range(AXI4_CTRLW + AXI4_RESPW + AXI4_USERW, AXI4_RESPW + AXI4_USERW + 1)\n")
    radsim_params_header_file.write("#define AXI4_ADDR(t)  t.range(AXI4_ADDRW + AXI4_CTRLW + AXI4_RESPW + AXI4_USERW, AXI4_CTRLW + AXI4_RESPW + AXI4_USERW + 1)\n\n")
    
    radsim_params_header_file.write("// Constants (DO NOT CHANGE)\n")
    radsim_params_header_file.write("#define AXI_TYPE_AR       0\n")
    radsim_params_header_file.write("#define AXI_TYPE_AW       1\n")
    radsim_params_header_file.write("#define AXI_TYPE_W        2\n")
    radsim_params_header_file.write("#define AXI_TYPE_R        3\n")
    radsim_params_header_file.write("#define AXI_TYPE_B        4\n")
    radsim_params_header_file.write("#define AXI_NUM_RSP_TYPES 2\n")
    radsim_params_header_file.write("#define AXI_NUM_REQ_TYPES 3\n\n")

    radsim_params_header_file.write("// clang-format on\n")

    radsim_params_header_file.close()


def generate_radsim_config_file(radsim_knobs, cluster_knobs):
    radsim_config_file = open(radsim_header_params["radsim_root_dir"] + "/sim/radsim_knobs_akb_test", "w") #AKB created temp file to test
    for i in range(len(cluster_knobs["cluster_configs"])):
        curr_config_num = cluster_knobs["cluster_configs"][i] #bc config # for a certain RAD may or may not match RAD ID
        for param in radsim_knobs[i]:
            radsim_config_file.write(param + " " + str(i) + " ") # second element is RAD ID
            if isinstance(radsim_knobs[curr_config_num][param], list):
                for value in radsim_knobs[curr_config_num][param]:
                    radsim_config_file.write(str(value) + " ")
                radsim_config_file.write("\n")
            else:
                radsim_config_file.write(str(radsim_knobs[curr_config_num][param]) + "\n")
    for param in cluster_knobs: #for params shared across cluster
        if param == 'configs':
            continue
        else:
            radsim_config_file.write(param + " " )
        
        if isinstance(cluster_knobs[param], list):
            for value in cluster_knobs[param]:
                radsim_config_file.write(str(value) + " ")
            radsim_config_file.write("\n")
        else:
            radsim_config_file.write(str(cluster_knobs[param]) + "\n")
    radsim_config_file.close()

def generate_radsim_main(design_name):
    main_cpp_file = open(radsim_header_params["radsim_root_dir"] + "/sim/main_akb_test.cpp", "w") #AKB created temp file to test
    main_cpp_file.write("#include <design_context.hpp>\n")
    main_cpp_file.write("#include <fstream>\n")
    main_cpp_file.write("#include <iostream>\n")
    main_cpp_file.write("#include <radsim_config.hpp>\n")
    main_cpp_file.write("#include <sstream>\n")
    main_cpp_file.write("#include <systemc.h>\n\n")
    main_cpp_file.write("#include <" + design_name + "_system.hpp>\n\n")
    main_cpp_file.write("RADSimConfig radsim_config;\n")
    main_cpp_file.write("RADSimDesignContext radsim_design;\n")
    main_cpp_file.write("std::ostream *gWatchOut;\n")
    main_cpp_file.write("SimLog sim_log;\n")
    main_cpp_file.write("SimTraceRecording sim_trace_probe;\n\n")
    main_cpp_file.write("int sc_main(int argc, char *argv[]) {\n")
    main_cpp_file.write("\tgWatchOut = &cout;\n")
    main_cpp_file.write("\tint log_verbosity = radsim_config.GetIntKnob(\"telemetry_log_verbosity\");\n")
    main_cpp_file.write("\tsim_log.SetLogSettings(log_verbosity, \"sim.log\");\n\n")
    main_cpp_file.write("\tint num_traces = radsim_config.GetIntKnob(\"telemetry_num_traces\");\n")
    main_cpp_file.write("\tsim_trace_probe.SetTraceRecordingSettings(\"sim.trace\", num_traces);\n\n")
    main_cpp_file.write("\tsc_clock *driver_clk_sig = new sc_clock(\n")
    main_cpp_file.write("\t\t\"node_clk0\", radsim_config.GetDoubleKnob(\"sim_driver_period\"), SC_NS);\n\n")
    main_cpp_file.write("\t" + design_name + "_system *system = new " + design_name + "_system(\"" + design_name + "_system\", driver_clk_sig);\n")
    main_cpp_file.write("\tsc_start();\n\n")
    main_cpp_file.write("\tdelete system;\n")
    main_cpp_file.write("\tdelete driver_clk_sig;\n")
    main_cpp_file.write("\tsc_flit scf;\n")
    main_cpp_file.write("\tscf.FreeAllFlits();\n")
    main_cpp_file.write("\tFlit *f = Flit::New();\n")
    main_cpp_file.write("\tf->FreeAll();\n")
    main_cpp_file.write("\tCredit *c = Credit::New();\n")
    main_cpp_file.write("\tc->FreeAll();\n")
    main_cpp_file.write("\tsim_trace_probe.dump_traces();\n")
    main_cpp_file.write("\t(void)argc;\n")
    main_cpp_file.write("\t(void)argv;\n")
    main_cpp_file.write("\treturn radsim_design.GetSimExitCode();\n")
    main_cpp_file.write("}\n")

def prepare_build_dir(design_names):
    if os.path.isdir("build"):
        shutil.rmtree("build", ignore_errors=True)
    os.makedirs("build")
    #os.system("cd build; cmake -DDESIGN:STRING=" + design_name + " ..; cd ..;")
    #os.system("cd build;")
    semicol_sep_design_names = ''
    count = 0
    count_max = len(design_names)
    for design_name in design_names:
        semicol_sep_design_names += design_name
        if count < count_max-1:
            semicol_sep_design_names += ';' 
        count = count+1
    #print("cmake -DDESIGN_NAMES=\"" + semicol_sep_design_names + "\" ..;")
    os.system("cd build; cmake -DDESIGN_NAMES=\"" + semicol_sep_design_names + "\" ..; cd .;")
    #os.system("cd build; cmake -DDESIGN:STRING=\"" + 'add' + "\" ..; cd .;")
    #os.system("cd ..;")

# Get design name from command line argument
if len(sys.argv) < 3:
    print("Invalid arguments: python config.py <number_of_configs> <design_name> <[optional] other_design_names>")
    exit(1)
num_configs = int(sys.argv[1])
design_names = set() #No duplicating design include statements and cmake commands
for i in range(2, len(sys.argv)): #skip 0th argument (that is current program name), and 1st (number_of_configs)
    design_names.add(sys.argv[i])
    print(sys.argv[i])

config_indices = []
for n in range(0, num_configs):
    config_indices.append(n)
print(config_indices)

# Check if design directory exists
for design_name in design_names:
    if not(os.path.isdir(os.getcwd() + "/example-designs/" + design_name)):
        print("Cannot find design directory under rad-sim/example-designs/")
        exit(1)

# Point to YAML configuration file
#config_filename = "example-designs/" + design_name + "/config.yml"
config_filename = "uni_config.yml"

# List default parameter values
booksim_params = {
    "radsim_root_dir": os.getcwd(),
    "noc_type": "2d",
    "noc_num_nocs": 1,
    "noc_topology": ["mesh"],
    "noc_anynet_file": [os.getcwd() + "/sim/noc/anynet_file"],
    "noc_dim_x": [8],
    "noc_dim_y": [8],
    "noc_routing_func": ["dim_order"],
    "noc_vcs": [5],
    "noc_vc_buffer_size": [8],
    "noc_output_buffer_size": [8],
    "noc_num_packet_types": [3],
    "noc_router_uarch": ["iq"],
    "noc_vc_allocator": ["islip"],
    "noc_sw_allocator": ["islip"],
    "noc_credit_delay": [1],
    "noc_routing_delay": [1],
    "noc_vc_alloc_delay": [1],
    "noc_sw_alloc_delay": [1],
}
radsim_header_params = {
    "radsim_root_dir": os.getcwd(),
    "noc_payload_width": [166],
    "noc_packet_id_width": 32,
    "noc_vcs": [3],
    "noc_num_packet_types": [3],
    "noc_num_nodes": [0],
    "noc_max_num_router_dest_interfaces": 32,
    "interfaces_max_axis_tdata_width": 512,
    "interfaces_axis_tkeep_width": 8,
    "interfaces_axis_tstrb_width": 8,
    "interfaces_axis_tuser_width": 75,
    "interfaces_axi_id_width": 8,
    "interfaces_axi_user_width": 64,
    "interfaces_max_axi_data_width": 512,
}
radsim_knobs = { #includes cluster config
    #"radsim_root_dir": os.getcwd(),
    "design_name": design_name,
    "noc_num_nocs": 1,
    "noc_clk_period": [0.571],
    "noc_vcs": [3],
    "noc_payload_width": [146],
    "noc_num_nodes": [0],
    "design_noc_placement": ["noc.place"],
    "noc_adapters_clk_period": [1.25],
    "noc_adapters_fifo_size": [16],
    "noc_adapters_obuff_size": [2],
    "noc_adapters_in_arbiter": ["fixed_rr"],
    "noc_adapters_out_arbiter": ["priority_rr"],
    "noc_adapters_vc_mapping": ["direct"],
    "design_clk_periods": [5.0],
    # "sim_driver_period": 5.0,
    # "telemetry_log_verbosity": 0,
    # "telemetry_traces": ["trace0", "trace1"],
    "dram_num_controllers": 0,
    "dram_clk_periods": [2.0],
    "dram_queue_sizes": [64],
    "dram_config_files": ["HBM2_8Gb_x128"]
}

cluster_knobs = { #shared among all RADs
    "radsim_root_dir": os.getcwd(),
    "sim_driver_period": 5.0,
    "telemetry_log_verbosity": 0,
    "telemetry_traces": ["trace0", "trace1"],
    "num_rads": 1,
    "cluster_configs": [0],
    "cluster_topology": 'all-to-all'
}

#deep copy (to allow changes to each dict)
radsim_knobs_per_rad = list(deepcopy(radsim_knobs) for i in range(num_configs))
#print(radsim_knobs_cluster)
radsim_header_params_per_rad = list(deepcopy(radsim_header_params) for i in range(num_configs))
booksim_params_per_rad = list(deepcopy(booksim_params) for i in range(num_configs))

# Parse configuration file
parse_config_file(config_filename, booksim_params_per_rad, radsim_header_params_per_rad, radsim_knobs_per_rad, cluster_knobs)
print(radsim_knobs_per_rad)
print(cluster_knobs)
#print_config(booksim_params, radsim_header_params, radsim_knobs)

# Generate RAD-Sim input files
generate_booksim_config_files(booksim_params_per_rad, radsim_header_params_per_rad, radsim_knobs_per_rad, cluster_knobs)
#generate_radsim_params_header(radsim_header_params)
generate_radsim_config_file(radsim_knobs_per_rad, cluster_knobs)
#generate_radsim_main(design_name)

#prepare_build_dir(design_names) #THIS WORKS -- commenting out for testing multi-rad config files

print("RAD-Sim was configured successfully!")
