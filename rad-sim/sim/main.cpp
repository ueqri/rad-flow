#include <design_context.hpp>
#include <fstream>
#include <iostream>
#include <radsim_config.hpp>
#include <sstream>
#include <systemc.h>
#include <radsim_cluster.hpp>
#include <radsim_inter_rad.hpp>

#include <dlrm_two_rad_system.hpp>
#define NUM_RADS 2 

RADSimConfig radsim_config;
std::ostream *gWatchOut;
SimLog sim_log;
SimTraceRecording sim_trace_probe;

int sc_main(int argc, char *argv[]) {
	std::string radsim_knobs_filename = "/sim/radsim_knobs";
	std::string radsim_knobs_filepath = RADSIM_ROOT_DIR + radsim_knobs_filename;
	radsim_config.ResizeAll(NUM_RADS);
	ParseRADSimKnobs(radsim_knobs_filepath);

	RADSimCluster* cluster = new RADSimCluster(NUM_RADS);

	gWatchOut = &cout;
	int log_verbosity = radsim_config.GetIntKnobShared("telemetry_log_verbosity");
	sim_log.SetLogSettings(log_verbosity, "sim.log");

	int num_traces = radsim_config.GetIntKnobShared("telemetry_num_traces");
	sim_trace_probe.SetTraceRecordingSettings("sim.trace", num_traces);

	sc_clock *driver_clk_sig0 = new sc_clock(
		"node_clk0", radsim_config.GetDoubleKnobShared("sim_driver_period"), SC_NS);
	dlrm_two_rad_system *system0 = new dlrm_two_rad_system("dlrm_two_rad_system", driver_clk_sig0, cluster->all_rads[0]);
	cluster->StoreSystem(system0);
	sc_clock *driver_clk_sig1 = new sc_clock(
		"node_clk0", radsim_config.GetDoubleKnobShared("sim_driver_period"), SC_NS);
	dlrm_two_rad_system *system1 = new dlrm_two_rad_system("dlrm_two_rad_system", driver_clk_sig1, cluster->all_rads[1]);
	cluster->StoreSystem(system1);

	sc_clock *inter_rad_clk_sig = new sc_clock(
		"node_clk0", radsim_config.GetDoubleKnobShared("sim_driver_period"), SC_NS);
	RADSimInterRad* blackbox = new RADSimInterRad("inter_rad_box", inter_rad_clk_sig, cluster);

	blackbox->ConnectClusterInterfaces(0);
	blackbox->ConnectClusterInterfaces(1);

	int start_cycle = GetSimulationCycle(radsim_config.GetDoubleKnobShared("sim_driver_period"));
	while (cluster->AllRADsNotDone()) {
		sc_start(1, SC_NS);
	}
	int end_cycle = GetSimulationCycle(radsim_config.GetDoubleKnobShared("sim_driver_period"));
	sc_stop();
	std::cout << "Simulation Cycles from main.cpp = " << end_cycle - start_cycle << std::endl;

	delete system0;
	delete driver_clk_sig0;
	delete system1;
	delete driver_clk_sig1;
	delete blackbox;
	delete inter_rad_clk_sig;

	sc_flit scf;
	scf.FreeAllFlits();
	Flit *f = Flit::New();
	f->FreeAll();
	Credit *c = Credit::New();
	c->FreeAll();
	sim_trace_probe.dump_traces();
	(void)argc;
	(void)argv;
	return cluster->all_rads[0]->GetSimExitCode();
}
