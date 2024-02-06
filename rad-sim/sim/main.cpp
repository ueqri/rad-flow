#include <design_context.hpp>
#include <fstream>
#include <iostream>
#include <radsim_config.hpp>
#include <sstream>
#include <systemc.h>
#include <radsim_cluster.hpp> //AKB ADDED
#include <radsim_inter_rad.hpp> //AKB ADDED

#include <add_system.hpp>
#include <mult_system.hpp> //AKB ADDED to test multi-design

RADSimConfig radsim_config;
//RADSimDesignContext radsim_design; //AKB: commented out
std::ostream *gWatchOut;
SimLog sim_log;
SimTraceRecording sim_trace_probe;

int sc_main(int argc, char *argv[]) {
	//AKB: using RADSimCluster class instead of creating new above
	RADSimCluster* cluster = new RADSimCluster(2);

	gWatchOut = &cout;
	int log_verbosity = radsim_config.GetIntKnob("telemetry_log_verbosity");
	sim_log.SetLogSettings(log_verbosity, "sim.log");

	int num_traces = radsim_config.GetIntKnob("telemetry_num_traces");
	sim_trace_probe.SetTraceRecordingSettings("sim.trace", num_traces);


	sc_clock *driver_clk_sig = new sc_clock(
		"node_clk0", radsim_config.GetDoubleKnob("sim_driver_period"), SC_NS);

	add_system *system = new add_system("add_system", driver_clk_sig, cluster->all_rads[0]); //AKB ADDED
	//mult_system *system = new mult_system("mult_system", driver_clk_sig, cluster->all_rads[0]); //AKB ADDED

	sc_clock *driver_clk_sig2 = new sc_clock(
		"node_clk0", radsim_config.GetDoubleKnob("sim_driver_period"), SC_NS); //AKB ADDED

	//add_system *system2 = new add_system("add_system", driver_clk_sig2, cluster->all_rads[1]); //AKB ADDED
	mult_system *system2 = new mult_system("mult_system", driver_clk_sig2, cluster->all_rads[1]); //AKB ADDED
	
	//AKB ADDED:
	cluster->StoreSystem(system);
	cluster->StoreSystem(system2);
	RADSimInterRad* blackbox = new RADSimInterRad(cluster);
	blackbox->ConnectRadPair(0, 1);
	
	
	while (cluster->AllRADsNotDone()) {
		sc_start(1, SC_NS);
		std::cout << "read system portal_in: " << system->dut_inst->portal_in.read() << std::endl;
		std::cout << "read system2 portal_in: " << system2->dut_inst->portal_in.read() << std::endl;
	}
	//std::cout << "stopping" << std::endl;
	sc_stop();

	delete system;
	delete system2; //AKB ADDED
	delete driver_clk_sig;
	delete driver_clk_sig2; //AKB ADDED
	sc_flit scf;
	scf.FreeAllFlits();
	Flit *f = Flit::New();
	f->FreeAll();
	Credit *c = Credit::New();
	c->FreeAll();
	sim_trace_probe.dump_traces();
	(void)argc;
	(void)argv;
	return 0;
}
