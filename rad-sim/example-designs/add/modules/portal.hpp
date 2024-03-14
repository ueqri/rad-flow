#pragma once

#include <axis_interface.hpp>
#include <design_context.hpp>
#include <queue>
#include <radsim_defines.hpp>
#include <radsim_module.hpp>
#include <client.hpp>
#include <string>
#include <systemc.h>
#include <vector>
#include <radsim_utils.hpp>

class portal : public RADSimModule {
    private:
    public:
    RADSimDesignContext* radsim_design;
    sc_in<sc_bv<DATAW>> portal_in;
    sc_out<sc_bv<DATAW>> portal_out;
    //try adding axis_master_port for portal_out
    axis_master_port portal_axis_master;
    axis_slave_port portal_axis_slave;
    sc_out<bool> portal_recvd; //for testing: flag so add_driver keeps simulation going until data is sent to mult module
    //Interfaces to the NoC
    axis_slave_port axis_add_portal_slave_interface;
    axis_master_port axis_add_portal_master_interface;

    portal(const sc_module_name &name, RADSimDesignContext* radsim_design); //AKB added last arg
    ~portal();

    void Assign(); // Combinational logic process
    void Tick();   // Sequential logic process
    SC_HAS_PROCESS(portal);
    void RegisterModuleInfo(); //even tho did not add AXI Interface, need because is virtual fn in derived class
};