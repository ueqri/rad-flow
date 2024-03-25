#pragma once

#include <radsim_config.hpp>
#include <mult.hpp>
#include <client_mult.hpp>
#include <portal_mult.hpp>
#include <systemc.h>
#include <vector>
#include <design_top.hpp>
#include <radsim_module.hpp>

class mult_top : public design_top {
private:
  mult *mult_inst;
  client_mult *client_inst;
  portal_mult *portal_inst;

public:
  sc_in<bool> rst;
  // Client's interface
  sc_in<sc_bv<DATAW>> client_tdata;
  sc_in<bool> client_tlast;
  sc_in<bool> client_valid;
  sc_out<bool> client_ready;
  sc_out<sc_bv<DATAW>> response;
  sc_out<bool> response_valid;
  sc_out<bool> mult_inter_rad_recvd;

  mult_top(const sc_module_name &name, RADSimDesignContext* radsim_design);
  ~mult_top();
};