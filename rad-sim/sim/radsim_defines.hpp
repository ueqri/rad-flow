#pragma once

// clang-format off
#define RADSIM_ROOT_DIR "/home/andrew/repos/rad-flow-dev/rad-sim"

// NoC-related Parameters
#define NOC_LINKS_PAYLOAD_WIDTH   82
#define NOC_LINKS_VCID_WIDTH      3
#define NOC_LINKS_PACKETID_WIDTH  32
#define NOC_LINKS_TYPEID_WIDTH    3
#define NOC_LINKS_DEST_WIDTH      7
#define NOC_LINKS_DEST_INFC_WIDTH 5
#define NOC_LINKS_WIDTH           (NOC_LINKS_PAYLOAD_WIDTH + NOC_LINKS_VCID_WIDTH + NOC_LINKS_PACKETID_WIDTH + NOC_LINKS_DEST_WIDTH + NOC_LINKS_DEST_INFC_WIDTH)

// AXI Parameters
#define AXIS_MAX_DATAW 1024
#define AXI4_MAX_DATAW 512
#define AXIS_USERW     66
#define AXI4_USERW     64
// (Almost always) Constant AXI Parameters
#define AXIS_STRBW  8
#define AXIS_KEEPW  8
#define AXIS_IDW    NOC_LINKS_PACKETID_WIDTH
#define AXIS_DESTW  NOC_LINKS_DEST_WIDTH
#define AXI4_IDW    8
#define AXI4_ADDRW  64
#define AXI4_LENW   8
#define AXI4_SIZEW  3
#define AXI4_BURSTW 2
#define AXI4_RESPW  2
#define AXI4_CTRLW  (AXI4_LENW + AXI4_SIZEW + AXI4_BURSTW)

// AXI Packetization Defines
#define AXIS_PAYLOADW (AXIS_MAX_DATAW + AXIS_USERW + 1)
#define AXIS_TLAST(t) t.range(0, 0)
#define AXIS_TUSER(t) t.range(AXIS_USERW, 1)
#define AXIS_TDATA(t) t.range(AXIS_MAX_DATAW + AXIS_USERW, AXIS_USERW + 1)
#define AXI4_PAYLOADW (AXI4_MAX_DATAW + AXI4_RESPW + AXI4_USERW + 1)
#define AXI4_LAST(t)  t.range(0, 0)
#define AXI4_USER(t)  t.range(AXI4_USERW, 1)
#define AXI4_RESP(t)  t.range(AXI4_RESPW + AXI4_USERW, AXI4_USERW + 1)
#define AXI4_DATA(t)  t.range(AXI4_MAX_DATAW + AXI4_RESPW + AXI4_USERW, AXI4_RESPW + AXI4_USERW + 1)
#define AXI4_CTRL(t)  t.range(AXI4_CTRLW + AXI4_RESPW + AXI4_USERW, AXI4_RESPW + AXI4_USERW + 1)
#define AXI4_ADDR(t)  t.range(AXI4_ADDRW + AXI4_CTRLW + AXI4_RESPW + AXI4_USERW, AXI4_CTRLW + AXI4_RESPW + AXI4_USERW + 1)

// Constants (DO NOT CHANGE)
#define AXI_TYPE_AR       0
#define AXI_TYPE_AW       1
#define AXI_TYPE_W        2
#define AXI_TYPE_R        3
#define AXI_TYPE_B        4
#define AXI_NUM_RSP_TYPES 2
#define AXI_NUM_REQ_TYPES 3

// clang-format on
