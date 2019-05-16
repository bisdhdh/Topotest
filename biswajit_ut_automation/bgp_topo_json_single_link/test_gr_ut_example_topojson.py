#!/usr/bin/env python

#
# Copyright (c) 2019 by VMware, Inc. ("VMware")
# Used Copyright (c) 2018 by Network Device Education Foundation, Inc. ("NetDEF")
# in this file.
#
# Permission to use, copy, modify, and/or distribute this software
# for any purpose with or without fee is hereby granted, provided
# that the above copyright notice and this permission notice appear
# in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND VMWARE DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL VMWARE BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY
# DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS,
# WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS
# ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE
# OF THIS SOFTWARE.
#

"""
<example>.py: Test <example tests>.
"""

import os
import sys
import json
import time
import inspect
import pytest

# Save the Current Working Directory to find configuration files.
CWD = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(CWD, '../../'))

# pylint: disable=C0413
# Import topogen and topotest helpers
from lib import topotest
from lib.topogen import Topogen, TopoRouter, get_topogen
from lib.topolog import logger

# Required to instantiate the topology builder class.
from mininet.topo import Topo

# Import topoJson from lib, to create topology and initial configuration
from lib.topojson import *

# Reading the data from JSON File for topology and configuration creation
jsonFile = "test_example_topojson.json"
try:
    with open(jsonFile, 'r') as topoJson:
        topo = json.load(topoJson)
except IOError:
    logger.info("Could not read file:", jsonFile)

# Global variables
bgp_convergence = False
input_dict = {}

class GenerateTopo(Topo):
    """
    Test topology builder
   
    * `Topo`: Topology object
    """

    def build(self, *_args, **_opts):
        "Build function"
        tgen = get_topogen(self)

        # This function only purpose is to create topology
        # as defined in input json file.
        #
        # Example
        #
        # Creating 2 routers having single links in between,
        # which is used to establised BGP neighborship

        # Building topology from json file
        build_topo_from_json(tgen, topo)

def setup_module(mod):
   '''
   Sets up the pytest environment

   * `mod`: module name
   '''

   testsuite_run_time = time.asctime(time.localtime(time.time()))
   logger.info("Testsuite start time: {}".format(testsuite_run_time))
   logger.info("="*40)

   logger.info("Running setup_module to create topology")

   # This function initiates the topology build with Topogen...
   tgen = Topogen(GenerateTopo, mod.__name__)
   # ... and here it calls Mininet initialization functions.

   # Starting topology
   tgen.start_topology()

   # Starting deamons and routers
   start_deamons_and_routers(tgen, CWD)

   # Creating configuration from JSON
   build_config_from_json(tgen, topo, CWD)

   # Checking BGP convergence
   global bgp_convergence

   # Dont run this test if we have any failure.
   if tgen.routers_have_failure():
       pytest.skip(tgen.errors)

   # Api call verify whether BGP is converged
   bgp_convergence = verify_bgp_convergence('ipv4', tgen, topo)
   if bgp_convergence != True: assert False, ("setup_module :Failed \n Error:"
                                               " {}".format(bgp_convergence))

   logger.info("Running setup_module() done")


def teardown_module(mod):
   '''
   Teardown the pytest environment

   * `mod`: module name
   '''

   logger.info("Running teardown_module to delete topology")

   tgen = get_topogen()

   # This function tears down the whole topology.
   tgen.stop_topology()

   # Removing tmp dirs and files
   remove_temp_files(tgen, CWD)

   logger.info("Testsuite end time: {}".\
               format(time.asctime(time.localtime(time.time()))))


def test_BGP_GR_UTP_1():
    logger.info(" Test Case : BGP_GR_UTP_1 >> BGP GR [Helper Mode]R1-----R2[Restart Mode] ")


    tgen = get_topogen()
    global bgp_convergence
    tc_name = "test_BGP_GR_UTP_1"
    
    if bgp_convergence != True:
        pytest.skip('skipped because of BGP Convergence failure')
   
    # redistribute static routes from r1 <--- r2 

    # GR test case starts from here.
    input_dict = {
   	"r1": {
       	  "bgp": {
            "bgp_neighbors": {
               "r2": {
                       "graceful-restart": "graceful-restart-helper"
                }
       	     }
           }
         },
        "r2": {
          "bgp": {
            "bgp_neighbors": {
               "r1": {
                       "graceful-restart": "graceful-restart"
                }
             }
           }
         }
    }

    result = configure_graceful_restart('ipv4', input_dict, tgen, CWD, topo)
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    clear_bgp_and_verify('ipv4', tgen, "r1", topo)
    clear_bgp_and_verify('ipv4', tgen, "r2", topo)

    logger.info("[Phase 1] : Test Setup [Helper Mode]R1-----R2[Restart Mode] Initilized >>>>>> ")

    #tgen.mininet_cli()

    result = verify_graceful_restart('ipv4', input_dict, tgen, topo, dut = "r1")
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)
    
    #tgen.mininet_cli()

    result = verify_r_bit('ipv4', input_dict, tgen, topo, dut="r1")
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    

    # Verifying BGP RIB routes
    dut = 'r1'
    next_hop = "192.168.1.10"
    input_dict = topo['routers']
    result = verify_bgp_rib('ipv4', dut, tgen, input_dict, next_hop, protocol = None)
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    # Verifying RIB routes
    protocol = 'bgp'
    result = verify_rib('ipv4', dut, tgen, input_dict, next_hop = next_hop, protocol = protocol)
    if result != True : assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    logger.info("[Phase 2] : R2 goes for reload >>>>>> ")
   
    #tgen.mininet_cli()

    # we need to replace this api with restart. Right now the resatrte api is not working. Test team is working on it.
    #clear_bgp_and_verify('ipv4', tgen, "r2", topo)

    send_SigTerm(tgen, CWD, "r2") 

    #sleep (10)

    #tgen.mininet_cli()

    logger.info("[Phase 3] : R2 is still down, restart time 120 sec. So time verify the routes are present in BGP RIB and ZEBRA >>>>>> ")
    #Verifying BGP RIB routes
    input_dict = topo['routers']
    dut = 'r1'
    next_hop = "192.168.1.10"
    input_dict = topo['routers']
    result = verify_bgp_rib('ipv4', dut, tgen, input_dict, next_hop, protocol = None)
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    #Verifying RIB routes
    protocol = 'bgp'
    result = verify_rib('ipv4', dut, tgen, input_dict, next_hop = next_hop, protocol = protocol)
    if result != True : assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)


    logger.info("[Phase 4] : sleep for 10 sec >>>>>> ")
    sleep (10)

    logger.info("[Phase 5] : R2 is about to come up now >>>>>> ")
    start_router(tgen, CWD, "r2")
    sleep (5)
    
    logger.info("[Phase 5] : R2 is UP Now ! >>>>>> ")


    # GR test case starts from here.
    input_dict = {
   	"r1": {
       	  "bgp": {
            "bgp_neighbors": {
               "r2": {
                       "graceful-restart": "graceful-restart-helper"
                }
       	     }
           }
         },
        "r2": {
          "bgp": {
            "bgp_neighbors": {
               "r1": {
                       "graceful-restart": "graceful-restart"
                }
             }
           }
         }
    }

    #tgen.mininet_cli()
    # Verifying GR stats
    result = verify_graceful_restart('ipv4', input_dict, tgen, topo, dut)
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    result = verify_r_bit('ipv4', input_dict, tgen, topo, dut)
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    # Verifying BGP RIB routes
    input_dict = topo['routers']
    dut = 'r1'
    next_hop = "192.168.1.10"
    result = verify_bgp_rib('ipv4', dut, tgen, input_dict, next_hop, protocol = None)
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    # Verifying RIB routes
    #protocol = 'bgp'
    #result = verify_rib('ipv4', dut, tgen, input_dict, next_hop = next_hop, protocol = protocol)
    #if result != True : assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)
        

    logger.info("[Phase 6] : R2 is UP now, so time to collect GR stats >>>>>> ")


    # GR test case starts from here.
    input_dict = {
   	"r1": {
       	  "bgp": {
            "bgp_neighbors": {
               "r2": {
                       "graceful-restart": "graceful-restart-helper"
                }
       	     }
           }
         },
        "r2": {
          "bgp": {
            "bgp_neighbors": {
               "r1": {
                       "graceful-restart": "graceful-restart"
                }
             }
           }
         }
    }

    # Verifying GR stats
    result = verify_graceful_restart('ipv4', input_dict, tgen, topo, dut)
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    result = verify_r_bit('ipv4', input_dict, tgen, topo, dut)
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    # Verifying BGP RIB routes
    input_dict = topo['routers']
    dut = 'r1'
    next_hop = "192.168.1.10"
    input_dict = topo['routers']
    result = verify_bgp_rib('ipv4', dut, tgen, input_dict, next_hop, protocol = None)
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    # Verifying RIB routes
    protocol = 'bgp'
    result = verify_rib('ipv4', dut, tgen, input_dict, next_hop = next_hop, protocol = protocol)
    if result != True : assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)
        

    logger.info("[Phase 7] : End of the Test >>>>>>")

    #tgen.mininet_cli()
 

def test_BGP_GR_UTP_3():
    logger.info(" Test Case : BGP_GR_UTP_3 >> BGP GR [Helper Mode]R1-----R2[Restart Mode] ")


    tgen = get_topogen()
    global bgp_convergence
    tc_name = "test_BGP_GR_UTP_3"
    
    if bgp_convergence != True:
        pytest.skip('skipped because of BGP Convergence failure')
   
    # redistribute static routes from r1 <--- r2 

    # GR test case starts from here.
    input_dict = {
   	"r1": {
       	  "bgp": {
            "bgp_neighbors": {
               "r2": {
                       "graceful-restart": "graceful-restart-helper"
                }
       	     }
           }
         },
        "r2": {
          "bgp": {
            "bgp_neighbors": {
               "r1": {
                       "graceful-restart": "graceful-restart"
                }
             }
           }
         }
    }
    result = configure_graceful_restart('ipv4', input_dict, tgen, CWD, topo)
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    clear_bgp_and_verify('ipv4', tgen, "r1", topo)
    clear_bgp_and_verify('ipv4', tgen, "r2", topo)

    logger.info("[Phase 1] : Test Setup [Helper Mode]R1-----R2[Restart Mode] Initilized >>>>>> ")


    result = verify_graceful_restart('ipv4', input_dict, tgen, topo, dut = "r1")
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    result = verify_r_bit('ipv4', input_dict, tgen, topo, dut="r1")
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    
    # tgen.mininet_cli()

    # Verifying BGP RIB routes
    dut = 'r1'
    next_hop = "192.168.1.10"
    input_dict = topo['routers']
    result = verify_bgp_rib('ipv4', dut, tgen, input_dict, next_hop, protocol = None)
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    # Verifying RIB routes
    protocol = 'bgp'
    result = verify_rib('ipv4', dut, tgen, input_dict, next_hop = next_hop, protocol = protocol)
    if result != True : assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    logger.info("[Phase 2] : R2 goes for reload >>>>>> ")
   
    # we need to replace this api with restart. Right now the resatrte api is not working. Test team is working on it.
    # >>> clear_bgp_and_verify('ipv4', tgen, "r2", topo)
   
    send_SigTerm(tgen, CWD, "r2") 

    #sleep (10)

    #tgen.mininet_cli()

    logger.info("[Phase 3] : R2 is still down, restart time 120 sec. So time verify the routes are present in BGP RIB and ZEBRA >>>>>> ")
    #Verifying BGP RIB routes
    input_dict = topo['routers']
    dut = 'r1'
    next_hop = "192.168.1.10"
    input_dict = topo['routers']
    result = verify_bgp_rib('ipv4', dut, tgen, input_dict, next_hop, protocol = None)
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    #Verifying RIB routes
    protocol = 'bgp'
    result = verify_rib('ipv4', dut, tgen, input_dict, next_hop = next_hop, protocol = protocol)
    if result != True : assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)


    logger.info("[Phase 4] : sleep for 120 sec >>>>>> ")
    sleep (120)

    logger.info("[Phase 5] : Verify the routes from r2 >>>>>> ")

    result = verify_bgp_rib('ipv4', dut, tgen, input_dict, next_hop, protocol = None)
    if result == True:
        logger.info("Unfortunitely the route is present {}".format(result))
        assert False, "Testcase {} :Failed".format(tc_name)

    #Verifying RIB routes
    protocol = 'bgp'
    result = verify_rib('ipv4', dut, tgen, input_dict, next_hop = next_hop, protocol = protocol)
    if result == True:
        logger.info("Unfortunitely the route is present {}".format(result))
        assert False, "Testcase {} :Failed".format(tc_name)

    logger.info("[Phase 6] : R2 is about to come up now >>>>>> ")
    start_router(tgen, CWD, "r2")
    sleep (5)
    
    logger.info("[Phase 7] : R2 is UP Now ! >>>>>> ")
    # GR test case starts from here.
    input_dict = {
   	"r1": {
       	  "bgp": {
            "bgp_neighbors": {
               "r2": {
                       "graceful-restart": "graceful-restart-helper"
                }
       	     }
           }
         },
        "r2": {
          "bgp": {
            "bgp_neighbors": {
               "r1": {
                       "graceful-restart": "graceful-restart"
                }
             }
           }
         }
    }

    # Verifying GR stats
    result = verify_graceful_restart('ipv4', input_dict, tgen, topo, dut)
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    result = verify_r_bit('ipv4', input_dict, tgen, topo, dut)
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    # Verifying BGP RIB routes
    input_dict = topo['routers']
    dut = 'r1'
    next_hop = "192.168.1.10"
    input_dict = topo['routers']
    result = verify_bgp_rib('ipv4', dut, tgen, input_dict, next_hop, protocol = None)
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    # Verifying RIB routes
    protocol = 'bgp'
    result = verify_rib('ipv4', dut, tgen, input_dict, next_hop = next_hop, protocol = protocol)
    if result != True : assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)
        

    logger.info("[Phase 8] : R2 is UP now, so time to collect GR stats >>>>>> ")


    # GR test case starts from here.
    input_dict = {
   	"r1": {
       	  "bgp": {
            "bgp_neighbors": {
               "r2": {
                       "graceful-restart": "graceful-restart-helper"
                }
       	     }
           }
         },
        "r2": {
          "bgp": {
            "bgp_neighbors": {
               "r1": {
                       "graceful-restart": "graceful-restart"
                }
             }
           }
         }
    }

    #tgen.mininet_cli()
    # Verifying GR stats
    result = verify_graceful_restart('ipv4', input_dict, tgen, topo, dut)
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    result = verify_r_bit('ipv4', input_dict, tgen, topo, dut)
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    # Verifying BGP RIB routes
    input_dict = topo['routers']
    dut = 'r1'
    next_hop = "192.168.1.10"
    input_dict = topo['routers']
    result = verify_bgp_rib('ipv4', dut, tgen, input_dict, next_hop, protocol = None)
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    # Verifying RIB routes
    protocol = 'bgp'
    result = verify_rib('ipv4', dut, tgen, input_dict, next_hop = next_hop, protocol = protocol)
    if result != True : assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)
        

    logger.info("[Phase 9] : End of the Test >>>>>>")

    #tgen.mininet_cli()



def test_BGP_GR_UTP_15():
    logger.info(" Test Case : BGP_GR_UTP_3 >> BGP GR [Restart]R1-----R2[Helper] ")


    tgen = get_topogen()
    global bgp_convergence
    tc_name = "test_BGP_GR_UTP_15"
    
    if bgp_convergence != True:
        pytest.skip('skipped because of BGP Convergence failure')
   
    # redistribute static routes from r1 <--- r2 

    # GR test case starts from here.
    input_dict = {
   	"r1": {
       	  "bgp": {
            "bgp_neighbors": {
               "r2": {
                       "graceful-restart": "graceful-restart"
                }
       	     }
           }
         },
        "r2": {
          "bgp": {
            "bgp_neighbors": {
               "r1": {
                       "graceful-restart": "graceful-restart-helper"
                }
             }
           }
         }
    }
    result = configure_graceful_restart('ipv4', input_dict, tgen, CWD, topo)
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    clear_bgp_and_verify('ipv4', tgen, "r1", topo)
    clear_bgp_and_verify('ipv4', tgen, "r2", topo)

    logger.info("[Phase 1] : Test Setup [Helper Mode]R1-----R2[Restart Mode] Initilized >>>>>> ")


    result = verify_graceful_restart('ipv4', input_dict, tgen, topo, dut = "r1")
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)


    # Verifying BGP RIB routes
    dut = 'r1'
    next_hop = "192.168.1.10"
    input_dict = topo['routers']
    result = verify_bgp_rib('ipv4', dut, tgen, input_dict, next_hop, protocol = None)
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    # Verifying RIB routes
    protocol = 'bgp'
    result = verify_rib('ipv4', dut, tgen, input_dict, next_hop = next_hop, protocol = protocol)
    if result != True : assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    logger.info("[Phase 2] : R1 goes for reload >>>>>> ")
   
    # we need to replace this api with restart. Right now the resatrte api is not working. Test team is working on it.
    # >>> clear_bgp_and_verify('ipv4', tgen, "r2", topo)
   
    send_SigTerm(tgen, CWD, "r1") 

    #sleep (10)

    #tgen.mininet_cli()

    logger.info("[Phase 6] : R1 is about to come up now >>>>>> ")
    start_router(tgen, CWD, "r1")
    sleep (5)
    
    logger.info("[Phase 7] : R1 is UP Now ! >>>>>> ")
    # GR test case starts from here.
    input_dict = {
   	"r1": {
       	  "bgp": {
            "bgp_neighbors": {
               "r2": {
                       "graceful-restart": "graceful-restart"
                }
       	     }
           }
         },
        "r2": {
          "bgp": {
            "bgp_neighbors": {
               "r1": {
                       "graceful-restart": "graceful-restart-helper"
                }
             }
           }
         }
    }

    # Verifying GR stats
    dut = 'r1'
    result = verify_graceful_restart('ipv4', input_dict, tgen, topo, dut)
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    dut = 'r2'
    result = verify_r_bit('ipv4', input_dict, tgen, topo, dut)
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

	# Verifying BGP RIB routes
    input_dict = topo['routers']
    dut = 'r1'
    next_hop = "192.168.1.10"
    input_dict = topo['routers']
    result = verify_bgp_rib('ipv4', dut, tgen, input_dict, next_hop, protocol = None)
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    # Verifying RIB routes
    protocol = 'bgp'
    result = verify_rib('ipv4', dut, tgen, input_dict, next_hop = next_hop, protocol = protocol)
    if result != True : assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)
        

    logger.info("[Phase 8] : R2 is UP now, so time to collect GR stats >>>>>> ")


    # GR test case starts from here.
    input_dict = {
   	"r1": {
       	  "bgp": {
            "bgp_neighbors": {
               "r2": {
                       "graceful-restart": "graceful-restart"
                }
       	     }
           }
         },
        "r2": {
          "bgp": {
            "bgp_neighbors": {
               "r1": {
                       "graceful-restart": "graceful-restart-helper"
                }
             }
           }
         }
    }

    dut = 'r1'
    # Verifying GR stats
    result = verify_graceful_restart('ipv4', input_dict, tgen, topo, dut)
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    dut = 'r2'
    result = verify_r_bit('ipv4', input_dict, tgen, topo, dut)
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    # Verifying BGP RIB routes
    input_dict = topo['routers']
    dut = 'r1'
    next_hop = "192.168.1.10"
    input_dict = topo['routers']
    result = verify_bgp_rib('ipv4', dut, tgen, input_dict, next_hop, protocol = None)
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    # Verifying RIB routes
    protocol = 'bgp'
    result = verify_rib('ipv4', dut, tgen, input_dict, next_hop = next_hop, protocol = protocol)
    if result != True : assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)
        

    logger.info("[Phase 9] : End of the Test >>>>>>")

def test_BGP_GR_UTP_17():
    logger.info(" Test Case : BGP_GR_UTP_17 >> [Helper]R1-----R2[Restart] ")


    tgen = get_topogen()
    global bgp_convergence
    tc_name = "test_BGP_GR_UTP_17"
    
    if bgp_convergence != True:
        pytest.skip('skipped because of BGP Convergence failure')
   
    # redistribute static routes from r1 <--- r2 

    # GR test case starts from here.
    input_dict = {
   	"r1": {
       	  "bgp": {
            "bgp_neighbors": {
               "r2": {
                       "graceful-restart": "graceful-restart-helper"
                }
       	     },
             "gracefulrestart":["graceful-restart"] 
           }
         },
        "r2": {
          "bgp": {
            "bgp_neighbors": {
               "r1": {
                       "graceful-restart": "graceful-restart"
                }
             }
           }
         }
    }
    result = configure_graceful_restart('ipv4', input_dict, tgen, CWD, topo)
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    clear_bgp_and_verify('ipv4', tgen, "r1", topo)
    clear_bgp_and_verify('ipv4', tgen, "r2", topo)

    logger.info("[Phase 1] : Test Setup [Helper Mode]R1-----R2[Restart Mode] Initilized >>>>>> ")

    #tgen.mininet_cli()

    result = verify_graceful_restart('ipv4', input_dict, tgen, topo, dut = "r1")
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    result = verify_r_bit('ipv4', input_dict, tgen, topo, dut="r1")
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    
    # tgen.mininet_cli()

    # Verifying BGP RIB routes
    dut = 'r1'
    next_hop = "192.168.1.10"
    input_dict = topo['routers']
    result = verify_bgp_rib('ipv4', dut, tgen, input_dict, next_hop, protocol = None)
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    # Verifying RIB routes
    protocol = 'bgp'
    result = verify_rib('ipv4', dut, tgen, input_dict, next_hop = next_hop, protocol = protocol)
    if result != True : assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    logger.info("[Phase 2] : R2 goes for reload >>>>>> ")
   
    # we need to replace this api with restart. Right now the resatrte api is not working. Test team is working on it.
    clear_bgp_and_verify('ipv4', tgen, "r2", topo)
    
    logger.info("[Phase 3] : R2 is still down, so time to collect GR stats >>>>>> ")

    
    # GR test case starts from here.
    input_dict = {
   	"r1": {
       	  "bgp": {
            "bgp_neighbors": {
               "r2": {
                       "graceful-restart": "graceful-restart-helper"
                }
       	     },
             "gracefulrestart":["graceful-restart"] 
           }
         },
        "r2": {
          "bgp": {
            "bgp_neighbors": {
               "r1": {
                       "graceful-restart": "graceful-restart"
                }
             }
           }
         }
    }

    # Verifying GR stats
    result = verify_graceful_restart('ipv4', input_dict, tgen, topo, dut)
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    result = verify_r_bit('ipv4', input_dict, tgen, topo, dut)
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    # Verifying BGP RIB routes
    input_dict = topo['routers']
    dut = 'r1'
    next_hop = "192.168.1.10"
    input_dict = topo['routers']
    result = verify_bgp_rib('ipv4', dut, tgen, input_dict, next_hop, protocol = None)
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    # Verifying RIB routes
    #protocol = 'bgp'
    #result = verify_rib('ipv4', dut, tgen, input_dict, next_hop = next_hop, protocol = protocol)
    #if result != True : assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)
        

    logger.info("[Phase 4] : R2 is UP now, so time to collect GR stats >>>>>> ")


    # GR test case starts from here.
    input_dict = {
   	"r1": {
       	  "bgp": {
            "bgp_neighbors": {
               "r2": {
                       "graceful-restart": "graceful-restart-helper"
                }
       	     },
             "gracefulrestart":["graceful-restart"]
           }
         },
        "r2": {
          "bgp": {
            "bgp_neighbors": {
               "r1": {
                       "graceful-restart": "graceful-restart"
                }
             }
           }
         }
    }

    # Verifying GR stats
    result = verify_graceful_restart('ipv4', input_dict, tgen, topo, dut)
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    result = verify_r_bit('ipv4', input_dict, tgen, topo, dut)
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    # Verifying BGP RIB routes
    input_dict = topo['routers']
    dut = 'r1'
    next_hop = "192.168.1.10"
    input_dict = topo['routers']
    result = verify_bgp_rib('ipv4', dut, tgen, input_dict, next_hop, protocol = None)
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    # Verifying RIB routes
    protocol = 'bgp'
    result = verify_rib('ipv4', dut, tgen, input_dict, next_hop = next_hop, protocol = protocol)
    if result != True : assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)
        

    logger.info("[Phase 5] : End of the Test >>>>>>")

    #tgen.mininet_cli()
 




def test_BGP_GR_UTP_18():
    logger.info(" Test Case : BGP_GR_UTP_18 >> [Restart]R1-----R2[Restart] ")


    tgen = get_topogen()
    global bgp_convergence
    tc_name = "test_BGP_GR_UTP_18"
    
    if bgp_convergence != True:
        pytest.skip('skipped because of BGP Convergence failure')
   
    # redistribute static routes from r1 <--- r2 

    # GR test case starts from here.
    input_dict = {
   	"r1": {
       	  "bgp": {
            "bgp_neighbors": {
               "r2": {
                       "graceful-restart": "graceful-restart"
                }
       	     },
             "gracefulrestart":["graceful-restart"]
           }
         },
        "r2": {
          "bgp": {
            "bgp_neighbors": {
               "r1": {
                       "graceful-restart": "graceful-restart"
                }
             }
           }
         }
    }

    result = configure_graceful_restart('ipv4', input_dict, tgen, CWD, topo)
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    clear_bgp_and_verify('ipv4', tgen, "r1", topo)
    clear_bgp_and_verify('ipv4', tgen, "r2", topo)

    logger.info("[Phase 1] : Test Setup [Restart]R1-----R2[Restart] Initilized >>>>>> ")

    #tgen.mininet_cli()

    result = verify_graceful_restart('ipv4', input_dict, tgen, topo, dut = "r1")
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    result = verify_r_bit('ipv4', input_dict, tgen, topo, dut="r1")
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    
    # tgen.mininet_cli()

    # Verifying BGP RIB routes
    dut = 'r1'
    next_hop = "192.168.1.10"
    input_dict = topo['routers']
    result = verify_bgp_rib('ipv4', dut, tgen, input_dict, next_hop, protocol = None)
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    # Verifying RIB routes
    protocol = 'bgp'
    result = verify_rib('ipv4', dut, tgen, input_dict, next_hop = next_hop, protocol = protocol)
    if result != True : assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    logger.info("[Phase 2] : R2 goes for reload >>>>>> ")
   
    # we need to replace this api with restart. Right now the resatrte api is not working. Test team is working on it.
    clear_bgp_and_verify('ipv4', tgen, "r2", topo)
    
    logger.info("[Phase 3] : R2 is still down, so time to collect GR stats >>>>>> ")

    
    # GR test case starts from here.
    input_dict = {
   	"r1": {
       	  "bgp": {
            "bgp_neighbors": {
               "r2": {
                       "graceful-restart": "graceful-restart"
                }
       	     },
             "gracefulrestart":["graceful-restart"]
           }
         },
        "r2": {
          "bgp": {
            "bgp_neighbors": {
               "r1": {
                       "graceful-restart": "graceful-restart"
                }
             }
           }
         }
    }

    # Verifying GR stats
    result = verify_graceful_restart('ipv4', input_dict, tgen, topo, dut)
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    result = verify_r_bit('ipv4', input_dict, tgen, topo, dut)
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    # Verifying BGP RIB routes
    input_dict = topo['routers']
    dut = 'r1'
    next_hop = "192.168.1.10"
    input_dict = topo['routers']
    result = verify_bgp_rib('ipv4', dut, tgen, input_dict, next_hop, protocol = None)
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    # Verifying RIB routes
    #protocol = 'bgp'
    #result = verify_rib('ipv4', dut, tgen, input_dict, next_hop = next_hop, protocol = protocol)
    #if result != True : assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)
        

    logger.info("[Phase 4] : R2 is UP now, so time to collect GR stats >>>>>> ")


    # GR test case starts from here.
    input_dict = {
   	"r1": {
       	  "bgp": {
            "bgp_neighbors": {
               "r2": {
                       "graceful-restart": "graceful-restart"
                }
       	     },
             "gracefulrestart":["graceful-restart"]
           }
         },
        "r2": {
          "bgp": {
            "bgp_neighbors": {
               "r1": {
                       "graceful-restart": "graceful-restart"
                }
             }
           }
         }
    }

    # Verifying GR stats
    result = verify_graceful_restart('ipv4', input_dict, tgen, topo, dut)
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    result = verify_r_bit('ipv4', input_dict, tgen, topo, dut)
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    # Verifying BGP RIB routes
    input_dict = topo['routers']
    dut = 'r1'
    next_hop = "192.168.1.10"
    input_dict = topo['routers']
    result = verify_bgp_rib('ipv4', dut, tgen, input_dict, next_hop, protocol = None)
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    # Verifying RIB routes
    protocol = 'bgp'
    result = verify_rib('ipv4', dut, tgen, input_dict, next_hop = next_hop, protocol = protocol)
    if result != True : assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)
        

    logger.info("[Phase 5] : End of the Test >>>>>>")

    #tgen.mininet_cli()


def test_BGP_GR_UTP_19():
    logger.info(" Test Case : BGP_GR_UTP_19 >> [Disable]R1-----R2[Restart] ")


    tgen = get_topogen()
    global bgp_convergence
    tc_name = "test_BGP_GR_UTP_19"
    
    if bgp_convergence != True:
        pytest.skip('skipped because of BGP Convergence failure')
   
    # redistribute static routes from r1 <--- r2 

    # GR test case starts from here.
    input_dict = {
   	"r1": {
       	  "bgp": {
            "bgp_neighbors": {
               "r2": {
                       "graceful-restart": "graceful-restart-disable"
                }
       	     },
             "gracefulrestart":["graceful-restart"]
           }
         },
        "r2": {
          "bgp": {
            "bgp_neighbors": {
               "r1": {
                       "graceful-restart": "graceful-restart"
                }
             }
           }
         }
    }
    result = configure_graceful_restart('ipv4', input_dict, tgen, CWD, topo)
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    clear_bgp_and_verify('ipv4', tgen, "r1", topo)
    clear_bgp_and_verify('ipv4', tgen, "r2", topo)

    logger.info("[Phase 1] : Test Setup [Restart]R1-----R2[Restart] Initilized >>>>>> ")

    #tgen.mininet_cli()

    result = verify_graceful_restart('ipv4', input_dict, tgen, topo, dut = "r1")
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    logger.info("[Phase 2] : End of the Test >>>>>>")
    #tgen.mininet_cli()

def test_BGP_GR_UTP_20():
    logger.info(" Test Case : BGP_GR_UTP_20 >> [Restart]R1-----R2[Restart] ")


    tgen = get_topogen()
    global bgp_convergence
    tc_name = "test_BGP_GR_UTP_20"
    
    if bgp_convergence != True:
        pytest.skip('skipped because of BGP Convergence failure')
   
    # redistribute static routes from r1 <--- r2 

    # GR test case starts from here.
    input_dict = {
   	"r1": {
       	  "bgp": {
            "bgp_neighbors": {
               "r2": {
                       "graceful-restart": "no_graceful-restart-disable"
                }
       	     },
             "gracefulrestart":["graceful-restart"]
           }
         },
        "r2": {
          "bgp": {
            "bgp_neighbors": {
               "r1": {
                       "graceful-restart": "graceful-restart"
                }
             }
           }
         }
    }
    result = configure_graceful_restart('ipv4', input_dict, tgen, CWD, topo)
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    clear_bgp_and_verify('ipv4', tgen, "r1", topo)
    clear_bgp_and_verify('ipv4', tgen, "r2", topo)

    logger.info("[Phase 1] : Test Setup [Restart]R1-----R2[Restart] Initilized >>>>>> ")

    #tgen.mininet_cli()
    
    #import pdb
    #pdb.set_trace()

    result = verify_graceful_restart('ipv4', input_dict, tgen, topo, dut = "r1")
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    #tgen.mininet_cli()
    logger.info("[Phase 2] : End of the Test >>>>>>")


def test_BGP_GR_UTP_21():
    logger.info(" Test Case : BGP_GR_UTP_21 >> [Helper]R1-----R2[Restart] ")


    tgen = get_topogen()
    global bgp_convergence
    tc_name = "test_BGP_GR_UTP_21"
    
    if bgp_convergence != True:
        pytest.skip('skipped because of BGP Convergence failure')
   
    # redistribute static routes from r1 <--- r2 

    # GR test case starts from here.
    input_dict = {
   	"r1": {
       	  "bgp": {
            "bgp_neighbors": {
               "r2": {
                       "graceful-restart": "graceful-restart-helper"
                }
       	     },
             "gracefulrestart":["no_graceful-restart"]
           }
         },
        "r2": {
          "bgp": {
            "bgp_neighbors": {
               "r1": {
                       "graceful-restart": "graceful-restart"
                }
             }
           }
         }
    }
    result = configure_graceful_restart('ipv4', input_dict, tgen, CWD, topo)
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    clear_bgp_and_verify('ipv4', tgen, "r1", topo)
    clear_bgp_and_verify('ipv4', tgen, "r2", topo)

    logger.info("[Phase 1] : Test Setup [Helper]R1-----R2[Restart] Initilized >>>>>> ")

    #tgen.mininet_cli()

    result = verify_graceful_restart('ipv4', input_dict, tgen, topo, dut = "r1")
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    #tgen.mininet_cli()
    logger.info("[Phase 2] : End of the Test >>>>>>")





def test_BGP_GR_UTP_22():
    logger.info(" Test Case : BGP_GR_UTP_22 >> [Restart]R1-----R2[Restart] ")


    tgen = get_topogen()
    global bgp_convergence
    tc_name = "test_BGP_GR_UTP_22"
    
    if bgp_convergence != True:
        pytest.skip('skipped because of BGP Convergence failure')
   
    # redistribute static routes from r1 <--- r2 

    # GR test case starts from here.
    input_dict = {
   	"r1": {
       	  "bgp": {
            "bgp_neighbors": {
               "r2": {
                       "graceful-restart": "graceful-restart"
                }
       	     }
           }
         },
        "r2": {
          "bgp": {
            "bgp_neighbors": {
               "r1": {
                       "graceful-restart": "graceful-restart"
                }
             }
           }
         }
    }
    result = configure_graceful_restart('ipv4', input_dict, tgen, CWD, topo)
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    clear_bgp_and_verify('ipv4', tgen, "r1", topo)
    clear_bgp_and_verify('ipv4', tgen, "r2", topo)

    logger.info("[Phase 1] : Test Setup [Restart]R1-----R2[Restart] Initilized >>>>>> ")

    #tgen.mininet_cli()

    result = verify_graceful_restart('ipv4', input_dict, tgen, topo, dut = "r1")
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    #tgen.mininet_cli()
    logger.info("[Phase 2] : End of the Test >>>>>>")





def test_BGP_GR_UTP_23():
    logger.info(" Test Case : BGP_GR_UTP_23 >> [Disable]R1-----R2[Restart] ")


    tgen = get_topogen()
    global bgp_convergence
    tc_name = "test_BGP_GR_UTP_23"
    
    if bgp_convergence != True:
        pytest.skip('skipped because of BGP Convergence failure')
   
    # redistribute static routes from r1 <--- r2 

    # GR test case starts from here.
    input_dict = {
   	"r1": {
       	  "bgp": {
            "bgp_neighbors": {
               "r2": {
                       "graceful-restart": "graceful-restart-disable"
               }
       	     }
           }
         },
        "r2": {
          "bgp": {
            "bgp_neighbors": {
               "r1": {
                       "graceful-restart": "graceful-restart"
                }
             }
           }
         }
    }
    result = configure_graceful_restart('ipv4', input_dict, tgen, CWD, topo)
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    clear_bgp_and_verify('ipv4', tgen, "r1", topo)
    clear_bgp_and_verify('ipv4', tgen, "r2", topo)

    logger.info("[Phase 1] : Test Setup [Restart]R1-----R2[Restart] Initilized >>>>>> ")

    #tgen.mininet_cli()

    result = verify_graceful_restart('ipv4', input_dict, tgen, topo, dut = "r1")
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    #tgen.mininet_cli()
    logger.info("[Phase 2] : End of the Test >>>>>>")






def test_BGP_GR_UTP_24():
    logger.info(" Test Case : BGP_GR_UTP_24 >> [Helper]R1-----R2[Restart] ")


    tgen = get_topogen()
    global bgp_convergence
    tc_name = "test_BGP_GR_UTP_24"
    
    if bgp_convergence != True:
        pytest.skip('skipped because of BGP Convergence failure')
   
    # redistribute static routes from r1 <--- r2 

    # GR test case starts from here.
    input_dict = {
   	"r1": {
       	  "bgp": {
            "bgp_neighbors": {
               "r2": {
                       "graceful-restart": "no_graceful-restart-disable"
               }
       	     }
           }
         },
        "r2": {
          "bgp": {
            "bgp_neighbors": {
               "r1": {
                       "graceful-restart": "graceful-restart"
                }
             }
           }
         }
    }
    result = configure_graceful_restart('ipv4', input_dict, tgen, CWD, topo)
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    clear_bgp_and_verify('ipv4', tgen, "r1", topo)
    clear_bgp_and_verify('ipv4', tgen, "r2", topo)

    logger.info("[Phase 1] : Test Setup [Restart]R1-----R2[Restart] Initilized >>>>>> ")

    #tgen.mininet_cli()

    result = verify_graceful_restart('ipv4', input_dict, tgen, topo, dut = "r1")
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    #tgen.mininet_cli()
    logger.info("[Phase 2] : End of the Test >>>>>>")



def test_BGP_GR_UTP_25():
    logger.info(" Test Case : BGP_GR_UTP_25 >> [Helper]R1-----R2[Restart] ")


    tgen = get_topogen()
    global bgp_convergence
    tc_name = "test_BGP_GR_UTP_25"
    
    if bgp_convergence != True:
        pytest.skip('skipped because of BGP Convergence failure')
   
    # redistribute static routes from r1 <--- r2 

    # GR test case starts from here.
    input_dict = {
   	"r1": {
       	  "bgp": {
            "bgp_neighbors": {
               "r2": {
                       "graceful-restart": "graceful-restart-helper"
               }
       	     },
             "gracefulrestart":["graceful-restart-disable"]
           }
         },
        "r2": {
          "bgp": {
            "bgp_neighbors": {
               "r1": {
                       "graceful-restart": "graceful-restart"
                }
             }
           }
         }
    }
    result = configure_graceful_restart('ipv4', input_dict, tgen, CWD, topo)
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    clear_bgp_and_verify('ipv4', tgen, "r1", topo)
    clear_bgp_and_verify('ipv4', tgen, "r2", topo)

    logger.info("[Phase 1] : Test Setup [Helper]R1-----R2[Restart] Initilized >>>>>> ")

    #tgen.mininet_cli()

    result = verify_graceful_restart('ipv4', input_dict, tgen, topo, dut = "r1")
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    #tgen.mininet_cli()
    logger.info("[Phase 2] : End of the Test >>>>>>")





def test_BGP_GR_UTP_26():
    logger.info(" Test Case : BGP_GR_UTP_26 >> [Restart]R1-----R2[Restart] ")


    tgen = get_topogen()
    global bgp_convergence
    tc_name = "test_BGP_GR_UTP_26"
    
    if bgp_convergence != True:
        pytest.skip('skipped because of BGP Convergence failure')
   
    # redistribute static routes from r1 <--- r2 

    # GR test case starts from here.
    input_dict = {
   	"r1": {
       	  "bgp": {
            "bgp_neighbors": {
               "r2": {
                       "graceful-restart": "graceful-restart"
               }
       	     },
             "gracefulrestart":["graceful-restart-disable"]
           }
         },
        "r2": {
          "bgp": {
            "bgp_neighbors": {
               "r1": {
                       "graceful-restart": "graceful-restart"
                }
             }
           }
         }
    }

    result = configure_graceful_restart('ipv4', input_dict, tgen, CWD, topo)
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    clear_bgp_and_verify('ipv4', tgen, "r1", topo)
    clear_bgp_and_verify('ipv4', tgen, "r2", topo)

    logger.info("[Phase 1] : Test Setup [Restart]R1-----R2[Restart] Initilized >>>>>> ")

    #tgen.mininet_cli()

    result = verify_graceful_restart('ipv4', input_dict, tgen, topo, dut = "r1")
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    #tgen.mininet_cli()
    logger.info("[Phase 2] : End of the Test >>>>>>")





def test_BGP_GR_UTP_27():
    logger.info(" Test Case : BGP_GR_UTP_27 >> [Disable]R1-----R2[Restart] ")


    tgen = get_topogen()
    global bgp_convergence
    tc_name = "test_BGP_GR_UTP_27"
    
    if bgp_convergence != True:
        pytest.skip('skipped because of BGP Convergence failure')
   
    # redistribute static routes from r1 <--- r2 

    # GR test case starts from here.
    input_dict = {
   	"r1": {
       	  "bgp": {
            "bgp_neighbors": {
               "r2": {
                       "graceful-restart": "graceful-restart-disable"
               }
       	     },
             "gracefulrestart":["graceful-restart-disable"]
           }
         },
        "r2": {
          "bgp": {
            "bgp_neighbors": {
               "r1": {
                       "graceful-restart": "graceful-restart"
                }
             }
           }
         }
    }

    result = configure_graceful_restart('ipv4', input_dict, tgen, CWD, topo)
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    clear_bgp_and_verify('ipv4', tgen, "r1", topo)
    clear_bgp_and_verify('ipv4', tgen, "r2", topo)

    logger.info("[Phase 1] : Test Setup [Restart]R1-----R2[Restart] Initilized >>>>>> ")

    #tgen.mininet_cli()

    result = verify_graceful_restart('ipv4', input_dict, tgen, topo, dut = "r1")
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    #tgen.mininet_cli()
    logger.info("[Phase 2] : End of the Test >>>>>>")






def test_BGP_GR_UTP_28():
    logger.info(" Test Case : BGP_GR_UTP_28 >> [Disable]R1-----R2[Restart] ")


    tgen = get_topogen()
    global bgp_convergence
    tc_name = "test_BGP_GR_UTP_28"
    
    if bgp_convergence != True:
        pytest.skip('skipped because of BGP Convergence failure')
   
    # redistribute static routes from r1 <--- r2 

    # GR test case starts from here.
    input_dict = {
   	"r1": {
       	  "bgp": {
            "bgp_neighbors": {
               "r2": {
                       "graceful-restart": "no_graceful-restart-disable"
               }
       	     },
             "gracefulrestart":["graceful-restart-disable"]
           }
         },
        "r2": {
          "bgp": {
            "bgp_neighbors": {
               "r1": {
                       "graceful-restart": "graceful-restart"
                }
             }
           }
         }
    }

    result = configure_graceful_restart('ipv4', input_dict, tgen, CWD, topo)
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    clear_bgp_and_verify('ipv4', tgen, "r1", topo)
    clear_bgp_and_verify('ipv4', tgen, "r2", topo)

    logger.info("[Phase 1] : Test Setup [Restart]R1-----R2[Restart] Initilized >>>>>> ")

    #tgen.mininet_cli()

    result = verify_graceful_restart('ipv4', input_dict, tgen, topo, dut = "r1")
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    #tgen.mininet_cli()
    logger.info("[Phase 2] : End of the Test >>>>>>")



def test_BGP_GR_UTP_29():
    logger.info(" Test Case : BGP_GR_UTP_29 >> [Helper]R1-----R2[Restart] ")


    tgen = get_topogen()
    global bgp_convergence
    tc_name = "test_BGP_GR_UTP_29"
    
    if bgp_convergence != True:
        pytest.skip('skipped because of BGP Convergence failure')
   
    # redistribute static routes from r1 <--- r2 

    # GR test case starts from here.
    input_dict = {
   	"r1": {
       	  "bgp": {
            "bgp_neighbors": {
               "r2": {
                       "graceful-restart":"graceful-restart-helper"
               }
       	     },
             "gracefulrestart":["no_graceful-restart-disable"]
           }
         },
        "r2": {
          "bgp": {
            "bgp_neighbors": {
               "r1": {
                       "graceful-restart": "graceful-restart"
                }
             }
           }
         }
    }

    result = configure_graceful_restart('ipv4', input_dict, tgen, CWD, topo)
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    clear_bgp_and_verify('ipv4', tgen, "r1", topo)
    clear_bgp_and_verify('ipv4', tgen, "r2", topo)

    logger.info("[Phase 1] : Test Setup [Helper]R1-----R2[Restart] Initilized >>>>>> ")

    #tgen.mininet_cli()

    result = verify_graceful_restart('ipv4', input_dict, tgen, topo, dut = "r1")
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    #tgen.mininet_cli()
    logger.info("[Phase 2] : End of the Test >>>>>>")


def test_BGP_GR_UTP_30():
    logger.info(" Test Case : BGP_GR_UTP_30 >> [Restart]R1-----R2[Restart] ")


    tgen = get_topogen()
    global bgp_convergence
    tc_name = "test_BGP_GR_UTP_30"
    
    if bgp_convergence != True:
        pytest.skip('skipped because of BGP Convergence failure')
   
    # redistribute static routes from r1 <--- r2 

    # GR test case starts from here.
    input_dict = {
   	"r1": {
       	  "bgp": {
            "bgp_neighbors": {
               "r2": {
                       "graceful-restart": "graceful-restart"
               }
       	     }
           }
         },
        "r2": {
          "bgp": {
            "bgp_neighbors": {
               "r1": {
                       "graceful-restart": "graceful-restart"
                }
             }
           }
         }
    }

    result = configure_graceful_restart('ipv4', input_dict, tgen, CWD, topo)
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    clear_bgp_and_verify('ipv4', tgen, "r1", topo)
    clear_bgp_and_verify('ipv4', tgen, "r2", topo)

    logger.info("[Phase 1] : Test Setup [Helper]R1-----R2[Restart] Initilized >>>>>> ")

    #tgen.mininet_cli()

    result = verify_graceful_restart('ipv4', input_dict, tgen, topo, dut = "r1")
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    #tgen.mininet_cli()
    logger.info("[Phase 2] : End of the Test >>>>>>")







def test_BGP_GR_UTP_31():
    logger.info(" Test Case : BGP_GR_UTP_31 >> [Restart]R1-----R2[Restart] ")


    tgen = get_topogen()
    global bgp_convergence
    tc_name = "test_BGP_GR_UTP_31"
    
    if bgp_convergence != True:
        pytest.skip('skipped because of BGP Convergence failure')
   
    # redistribute static routes from r1 <--- r2 

    # GR test case starts from here.
    input_dict = {
   	"r1": {
       	  "bgp": {
            "bgp_neighbors": {
               "r2": {
                       "graceful-restart": "graceful-restart-disable"
               }
       	     }
           }
         },
        "r2": {
          "bgp": {
            "bgp_neighbors": {
               "r1": {
                       "graceful-restart": "graceful-restart"
                }
             }
           }
         }
    }

    result = configure_graceful_restart('ipv4', input_dict, tgen, CWD, topo)
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    clear_bgp_and_verify('ipv4', tgen, "r1", topo)
    clear_bgp_and_verify('ipv4', tgen, "r2", topo)

    logger.info("[Phase 1] : Test Setup [Helper]R1-----R2[Restart] Initilized >>>>>> ")

    #tgen.mininet_cli()

    result = verify_graceful_restart('ipv4', input_dict, tgen, topo, dut = "r1")
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    #tgen.mininet_cli()
    logger.info("[Phase 2] : End of the Test >>>>>>")





def test_BGP_GR_UTP_32():
    logger.info(" Test Case : BGP_GR_UTP_32 >> [Helper]R1-----R2[Restart] ")


    tgen = get_topogen()
    global bgp_convergence
    tc_name = "test_BGP_GR_UTP_32"
    
    if bgp_convergence != True:
        pytest.skip('skipped because of BGP Convergence failure')
   
    # redistribute static routes from r1 <--- r2 

    # GR test case starts from here.
    input_dict = {
   	"r1": {
       	  "bgp": {
            "bgp_neighbors": {
               "r2": {
                       "graceful-restart": "no_graceful-restart-disable"
               }
       	     }
           }
         },
        "r2": {
          "bgp": {
            "bgp_neighbors": {
               "r1": {
                       "graceful-restart": "graceful-restart"
                }
             }
           }
         }
    }

    result = configure_graceful_restart('ipv4', input_dict, tgen, CWD, topo)
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    clear_bgp_and_verify('ipv4', tgen, "r1", topo)
    clear_bgp_and_verify('ipv4', tgen, "r2", topo)

    logger.info("[Phase 1] : Test Setup [Helper]R1-----R2[Restart] Initilized >>>>>> ")

    #tgen.mininet_cli()

    result = verify_graceful_restart('ipv4', input_dict, tgen, topo, dut = "r1")
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    #tgen.mininet_cli()
    logger.info("[Phase 2] : End of the Test >>>>>>")



def test_BGP_GR_UTP_33():
    logger.info(" Test Case : BGP_GR_UTP_33 >> BGP GR [Disable Mode]R1-----R2[Helper Mode] ")


    tgen = get_topogen()
    global bgp_convergence
    tc_name = "test_BGP_GR_UTP_33"
    
    if bgp_convergence != True:
        pytest.skip('skipped because of BGP Convergence failure')
   
    # redistribute static routes from r1 <--- r2 

    # GR test case starts from here.
    input_dict = {
   	"r1": {
       	  "bgp": {
            "bgp_neighbors": {
               "r2": {
                       "graceful-restart": "graceful-restart-disable"
                }
       	     }
           }
         },
        "r2": {
          "bgp": {
            "bgp_neighbors": {
               "r1": {
                       "graceful-restart": "graceful-restart-helper"
                }
             }
           }
         }
    }
    result = configure_graceful_restart('ipv4', input_dict, tgen, CWD, topo)
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    clear_bgp_and_verify('ipv4', tgen, "r1", topo)
    clear_bgp_and_verify('ipv4', tgen, "r2", topo)

    logger.info("[Phase 1] : Test Setup [Disable Mode]R1-----R2[Helper Mode] Initilized >>>>>> ")


    result = verify_graceful_restart('ipv4', input_dict, tgen, topo, dut = "r1")
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    
    # tgen.mininet_cli()

    # Verifying BGP RIB routes
    dut = 'r1'
    next_hop = "192.168.1.10"
    input_dict = topo['routers']
    result = verify_bgp_rib('ipv4', dut, tgen, input_dict, next_hop, protocol = None)
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    # Verifying RIB routes
    protocol = 'bgp'
    result = verify_rib('ipv4', dut, tgen, input_dict, next_hop = next_hop, protocol = protocol)
    if result != True : assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    logger.info("[Phase 2] : R1 goes for reload >>>>>> ")
   
    # we need to replace this api with restart. Right now the resatrte api is not working. Test team is working on it.
    # >>> clear_bgp_and_verify('ipv4', tgen, "r2", topo)
   
    send_SigTerm(tgen, CWD, "r1") 

    #sleep (10)

    #tgen.mininet_cli()

    logger.info("[Phase 3] : R2 is about to come up now >>>>>> ")
    start_router(tgen, CWD, "r1")
    sleep (5)
    
    logger.info("[Phase 4] : R2 is UP Now ! >>>>>> ")
    # GR test case starts from here.
    input_dict = {
   	"r1": {
       	  "bgp": {
            "bgp_neighbors": {
               "r2": {
                       "graceful-restart": "graceful-restart-disable"
                }
       	     }
           }
         },
        "r2": {
          "bgp": {
            "bgp_neighbors": {
               "r1": {
                       "graceful-restart": "graceful-restart-helper"
                }
             }
           }
         }
    }

    # Verifying GR stats
    result = verify_graceful_restart('ipv4', input_dict, tgen, topo, dut)
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)


    # Verifying BGP RIB routes
    input_dict = topo['routers']
    dut = 'r1'
    next_hop = "192.168.1.10"
    input_dict = topo['routers']
    result = verify_bgp_rib('ipv4', dut, tgen, input_dict, next_hop, protocol = None)
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    # Verifying RIB routes
    protocol = 'bgp'
    result = verify_rib('ipv4', dut, tgen, input_dict, next_hop = next_hop, protocol = protocol)
    if result != True : assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)
        

    logger.info("[Phase 5] : R2 is UP now, so time to collect GR stats >>>>>> ")


    # GR test case starts from here.
    input_dict = {
   	"r1": {
       	  "bgp": {
            "bgp_neighbors": {
               "r2": {
                       "graceful-restart": "graceful-restart-disable"
                }
       	     }
           }
         },
        "r2": {
          "bgp": {
            "bgp_neighbors": {
               "r1": {
                       "graceful-restart": "graceful-restart-helper"
                }
             }
           }
         }
    }

    # Verifying GR stats
    result = verify_graceful_restart('ipv4', input_dict, tgen, topo, dut)
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    # Verifying BGP RIB routes
    input_dict = topo['routers']
    dut = 'r1'
    next_hop = "192.168.1.10"
    input_dict = topo['routers']
    result = verify_bgp_rib('ipv4', dut, tgen, input_dict, next_hop, protocol = None)
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    # Verifying RIB routes
    protocol = 'bgp'
    result = verify_rib('ipv4', dut, tgen, input_dict, next_hop = next_hop, protocol = protocol)
    if result != True : assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)
        

    logger.info("[Phase 6] : End of the Test >>>>>>")

    #tgen.mininet_cli()
 


def test_BGP_GR_UTP_34():
    logger.info(" Test Case : BGP_GR_UTP_34 >> BGP GR [Disable Mode]R1-----R2[Helper Mode] ")


    tgen = get_topogen()
    global bgp_convergence
    tc_name = "test_BGP_GR_UTP_34"
    
    if bgp_convergence != True:
        pytest.skip('skipped because of BGP Convergence failure')
   
    # redistribute static routes from r1 <--- r2 

    # GR test case starts from here.
    input_dict = {
   	"r1": {
       	  "bgp": {
            "bgp_neighbors": {
               "r2": {
                       "graceful-restart": "graceful-restart-disable"
                }
       	     }
           }
         },
        "r2": {
          "bgp": {
            "bgp_neighbors": {
               "r1": {
                       "graceful-restart": "graceful-restart-helper"
                }
             }
           }
         }
    }
    result = configure_graceful_restart('ipv4', input_dict, tgen, CWD, topo)
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    clear_bgp_and_verify('ipv4', tgen, "r1", topo)
    clear_bgp_and_verify('ipv4', tgen, "r2", topo)

    logger.info("[Phase 1] : Test Setup [Disable Mode]R1-----R2[Helper Mode] Initilized >>>>>> ")


    result = verify_graceful_restart('ipv4', input_dict, tgen, topo, dut = "r2")
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    
    # tgen.mininet_cli()

    # Verifying BGP RIB routes
    dut = 'r1'
    next_hop = "192.168.1.10"
    input_dict = topo['routers']
    result = verify_bgp_rib('ipv4', dut, tgen, input_dict, next_hop, protocol = None)
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    # Verifying RIB routes
    protocol = 'bgp'
    result = verify_rib('ipv4', dut, tgen, input_dict, next_hop = next_hop, protocol = protocol)
    if result != True : assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    logger.info("[Phase 2] : R1 goes for reload >>>>>> ")
   
    # we need to replace this api with restart. Right now the resatrte api is not working. Test team is working on it.
    # >>> clear_bgp_and_verify('ipv4', tgen, "r2", topo)
   
    send_SigTerm(tgen, CWD, "r1") 

    #sleep (10)

    #tgen.mininet_cli()

    logger.info("[Phase 3] : R2 is about to come up now >>>>>> ")
    start_router(tgen, CWD, "r1")
    sleep (5)
    
    logger.info("[Phase 4] : R2 is UP Now ! >>>>>> ")
    # GR test case starts from here.
    input_dict = {
   	"r1": {
       	  "bgp": {
            "bgp_neighbors": {
               "r2": {
                       "graceful-restart": "graceful-restart-disable"
                }
       	     }
           }
         },
        "r2": {
          "bgp": {
            "bgp_neighbors": {
               "r1": {
                       "graceful-restart": "graceful-restart-helper"
                }
             }
           }
         }
    }

    # Verifying GR stats
    result = verify_graceful_restart('ipv4', input_dict, tgen, topo, 'r2')
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)


    # Verifying BGP RIB routes
    input_dict = topo['routers']
    dut = 'r1'
    next_hop = "192.168.1.10"
    input_dict = topo['routers']
    result = verify_bgp_rib('ipv4', dut, tgen, input_dict, next_hop, protocol = None)
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    # Verifying RIB routes
    protocol = 'bgp'
    result = verify_rib('ipv4', dut, tgen, input_dict, next_hop = next_hop, protocol = protocol)
    if result != True : assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)
        

    logger.info("[Phase 5] : R2 is UP now, so time to collect GR stats >>>>>> ")


    # GR test case starts from here.
    input_dict = {
   	"r1": {
       	  "bgp": {
            "bgp_neighbors": {
               "r2": {
                       "graceful-restart": "graceful-restart-disable"
                }
       	     }
           }
         },
        "r2": {
          "bgp": {
            "bgp_neighbors": {
               "r1": {
                       "graceful-restart": "graceful-restart-helper"
                }
             }
           }
         }
    }

    # Verifying GR stats
    result = verify_graceful_restart('ipv4', input_dict, tgen, topo, dut)
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    # Verifying BGP RIB routes
    input_dict = topo['routers']
    dut = 'r1'
    next_hop = "192.168.1.10"
    input_dict = topo['routers']
    result = verify_bgp_rib('ipv4', dut, tgen, input_dict, next_hop, protocol = None)
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    # Verifying RIB routes
    protocol = 'bgp'
    result = verify_rib('ipv4', dut, tgen, input_dict, next_hop = next_hop, protocol = protocol)
    if result != True : assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)
        

    logger.info("[Phase 6] : End of the Test >>>>>>")

    #tgen.mininet_cli()



def test_BGP_GR_UTP_35():
    logger.info(" Test Case : BGP_GR_UTP_35 >> BGP GR [Disable Mode]R1-----R2[Helper Mode] ")


    tgen = get_topogen()
    global bgp_convergence
    tc_name = "test_BGP_GR_UTP_35"
    
    if bgp_convergence != True:
        pytest.skip('skipped because of BGP Convergence failure')
   
    # redistribute static routes from r1 <--- r2 

    # GR test case starts from here.
    input_dict = {
   	   "r1": {
       	  "bgp": {
            "bgp_neighbors": {
               "r2": {
                       "graceful-restart": "graceful-restart-disable"
                }
       	     }
           }
         },
       "r2": {
          "bgp": {
            "bgp_neighbors": {
               "r1": {
                       "graceful-restart": "graceful-restart"
                }
             }
           }
         }
    }
    result = configure_graceful_restart('ipv4', input_dict, tgen, CWD, topo)
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    clear_bgp_and_verify('ipv4', tgen, "r1", topo)
    clear_bgp_and_verify('ipv4', tgen, "r2", topo)

    logger.info("[Phase 1] : Test Setup [Disable Mode]R1-----R2[Helper Mode] Initilized >>>>>> ")


    result = verify_graceful_restart('ipv4', input_dict, tgen, topo, dut = "r1")
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    
    # tgen.mininet_cli()

    # Verifying BGP RIB routes
    dut = 'r1'
    next_hop = "192.168.1.10"
    input_dict = topo['routers']
    result = verify_bgp_rib('ipv4', dut, tgen, input_dict, next_hop, protocol = None)
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    # Verifying RIB routes
    protocol = 'bgp'
    result = verify_rib('ipv4', dut, tgen, input_dict, next_hop = next_hop, protocol = protocol)
    if result != True : assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    logger.info("[Phase 2] : R1 goes for reload >>>>>> ")
   
    # we need to replace this api with restart. Right now the resatrte api is not working. Test team is working on it.
    # >>> clear_bgp_and_verify('ipv4', tgen, "r2", topo)
   
    send_SigTerm(tgen, CWD, "r1") 

    #sleep (10)

    #tgen.mininet_cli()

    logger.info("[Phase 3] : R2 is about to come up now >>>>>> ")
    start_router(tgen, CWD, "r1")
    sleep (5)
    
    logger.info("[Phase 4] : R2 is UP Now ! >>>>>> ")
    # GR test case starts from here.
    input_dict = {
   	"r1": {
       	  "bgp": {
            "bgp_neighbors": {
               "r2": {
                       "graceful-restart": "graceful-restart-disable"
                }
       	     }
           }
         },
        "r2": {
          "bgp": {
            "bgp_neighbors": {
               "r1": {
                       "graceful-restart": "graceful-restart"
                }
             }
           }
         }
    }

    # Verifying GR stats
    result = verify_graceful_restart('ipv4', input_dict, tgen, topo, 'r1')
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)


    # Verifying BGP RIB routes
    input_dict = topo['routers']
    dut = 'r1'
    next_hop = "192.168.1.10"
    input_dict = topo['routers']
    result = verify_bgp_rib('ipv4', dut, tgen, input_dict, next_hop, protocol = None)
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    # Verifying RIB routes
    protocol = 'bgp'
    result = verify_rib('ipv4', dut, tgen, input_dict, next_hop = next_hop, protocol = protocol)
    if result != True : assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)
        

    logger.info("[Phase 5] : R2 is UP now, so time to collect GR stats >>>>>> ")


    # GR test case starts from here.
    input_dict = {
   	"r1": {
       	  "bgp": {
            "bgp_neighbors": {
               "r2": {
                       "graceful-restart": "graceful-restart-disable"
                }
       	     }
           }
         },
        "r2": {
          "bgp": {
            "bgp_neighbors": {
               "r1": {
                       "graceful-restart": "graceful-restart"
                }
             }
           }
         }
    }

    # Verifying GR stats
    result = verify_graceful_restart('ipv4', input_dict, tgen, topo, dut)
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    # Verifying BGP RIB routes
    input_dict = topo['routers']
    dut = 'r1'
    next_hop = "192.168.1.10"
    input_dict = topo['routers']
    result = verify_bgp_rib('ipv4', dut, tgen, input_dict, next_hop, protocol = None)
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    # Verifying RIB routes
    protocol = 'bgp'
    result = verify_rib('ipv4', dut, tgen, input_dict, next_hop = next_hop, protocol = protocol)
    if result != True : assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)
        

    logger.info("[Phase 6] : End of the Test >>>>>>")

    #tgen.mininet_cli()



def test_BGP_GR_UTP_36():
    logger.info(" Test Case : BGP_GR_UTP_36 >> BGP GR [Disable Mode]R1-----R2[Helper Mode] ")


    tgen = get_topogen()
    global bgp_convergence
    tc_name = "test_BGP_GR_UTP_36"
    
    if bgp_convergence != True:
        pytest.skip('skipped because of BGP Convergence failure')
   
    # redistribute static routes from r1 <--- r2 

    # GR test case starts from here.
    input_dict = {
   	   "r1": {
       	  "bgp": {
            "bgp_neighbors": {
               "r2": {
                       "graceful-restart": "graceful-restart-disable"
                }
       	     }
           }
         },
       "r2": {
          "bgp": {
            "bgp_neighbors": {
               "r1": {
                       "graceful-restart": "graceful-restart"
                }
             }
           }
         }
    }
    result = configure_graceful_restart('ipv4', input_dict, tgen, CWD, topo)
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    clear_bgp_and_verify('ipv4', tgen, "r1", topo)
    clear_bgp_and_verify('ipv4', tgen, "r2", topo)

    logger.info("[Phase 1] : Test Setup [Disable Mode]R1-----R2[Helper Mode] Initilized >>>>>> ")


    result = verify_graceful_restart('ipv4', input_dict, tgen, topo, dut = "r2")
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    
    # tgen.mininet_cli()

    # Verifying BGP RIB routes
    dut = 'r1'
    next_hop = "192.168.1.10"
    input_dict = topo['routers']
    result = verify_bgp_rib('ipv4', dut, tgen, input_dict, next_hop, protocol = None)
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    # Verifying RIB routes
    protocol = 'bgp'
    result = verify_rib('ipv4', dut, tgen, input_dict, next_hop = next_hop, protocol = protocol)
    if result != True : assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    logger.info("[Phase 2] : R1 goes for reload >>>>>> ")
   
    # we need to replace this api with restart. Right now the resatrte api is not working. Test team is working on it.
    # >>> clear_bgp_and_verify('ipv4', tgen, "r2", topo)
   
    send_SigTerm(tgen, CWD, "r1") 

    #sleep (10)

    #tgen.mininet_cli()

    logger.info("[Phase 3] : R2 is about to come up now >>>>>> ")
    start_router(tgen, CWD, "r1")
    sleep (5)
    
    logger.info("[Phase 4] : R2 is UP Now ! >>>>>> ")
    # GR test case starts from here.
    input_dict = {
   	"r1": {
       	  "bgp": {
            "bgp_neighbors": {
               "r2": {
                       "graceful-restart": "graceful-restart-disable"
                }
       	     }
           }
         },
        "r2": {
          "bgp": {
            "bgp_neighbors": {
               "r1": {
                       "graceful-restart": "graceful-restart"
                }
             }
           }
         }
    }

    # Verifying GR stats
    result = verify_graceful_restart('ipv4', input_dict, tgen, topo, 'r2')
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)


    # Verifying BGP RIB routes
    input_dict = topo['routers']
    dut = 'r1'
    next_hop = "192.168.1.10"
    input_dict = topo['routers']
    result = verify_bgp_rib('ipv4', dut, tgen, input_dict, next_hop, protocol = None)
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    # Verifying RIB routes
    protocol = 'bgp'
    result = verify_rib('ipv4', dut, tgen, input_dict, next_hop = next_hop, protocol = protocol)
    if result != True : assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)
        

    logger.info("[Phase 5] : R2 is UP now, so time to collect GR stats >>>>>> ")


    # GR test case starts from here.
    input_dict = {
   	"r1": {
       	  "bgp": {
            "bgp_neighbors": {
               "r2": {
                       "graceful-restart": "graceful-restart-disable"
                }
       	     }
           }
         },
        "r2": {
          "bgp": {
            "bgp_neighbors": {
               "r1": {
                       "graceful-restart": "graceful-restart"
                }
             }
           }
         }
    }

    # Verifying GR stats
    result = verify_graceful_restart('ipv4', input_dict, tgen, topo, dut)
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    # Verifying BGP RIB routes
    input_dict = topo['routers']
    dut = 'r1'
    next_hop = "192.168.1.10"
    input_dict = topo['routers']
    result = verify_bgp_rib('ipv4', dut, tgen, input_dict, next_hop, protocol = None)
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    # Verifying RIB routes
    protocol = 'bgp'
    result = verify_rib('ipv4', dut, tgen, input_dict, next_hop = next_hop, protocol = protocol)
    if result != True : assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)
        

    logger.info("[Phase 6] : End of the Test >>>>>>")


def test_BGP_GR_Restarting_4():
    logger.info(" Test Case : BGP_GR_Restarting_4 >> BGP GR [Restart Mode]R1-----R2[Helper Mode] ")


    tgen = get_topogen()
    global bgp_convergence
    tc_name = "test_BGP_GR_Restarting_4"
    
    if bgp_convergence != True:
        pytest.skip('skipped because of BGP Convergence failure')
   
    # redistribute static routes from r1 <--- r2 

    # GR test case starts from here.
    input_dict = {
   	"r1": {
       	  "bgp": {
            "bgp_neighbors": {
               "r2": {
                       "graceful-restart": "graceful-restart"
                }
       	     }
           }
         },
        "r2": {
          "bgp": {
            "bgp_neighbors": {
               "r1": {
                       "graceful-restart": "graceful-restart-helper"
                }
             }
           }
         }
    }

    result = configure_graceful_restart('ipv4', input_dict, tgen, CWD, topo)
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    clear_bgp_and_verify('ipv4', tgen, "r1", topo)
    clear_bgp_and_verify('ipv4', tgen, "r2", topo)

    logger.info("[Phase 1] : Test Setup [Restart Mode]R1-----R2[Helper Mode] Initilized >>>>>> ")


    result = verify_graceful_restart('ipv4', input_dict, tgen, topo, dut = "r1")
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    
    # tgen.mininet_cli()

    # Verifying BGP RIB routes
    dut = 'r1'
    next_hop = "192.168.1.10"
    input_dict = topo['routers']
    result = verify_bgp_rib('ipv4', dut, tgen, input_dict, next_hop, protocol = None)
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    # Verifying RIB routes
    protocol = 'bgp'
    result = verify_rib('ipv4', dut, tgen, input_dict, next_hop = next_hop, protocol = protocol)
    if result != True : assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    logger.info("[Phase 2] : R2 goes for reload >>>>>> ")
   
    #tgen.mininet_cli()

    # we need to replace this api with restart. Right now the resatrte api is not working. Test team is working on it.
    #clear_bgp_and_verify('ipv4', tgen, "r2", topo)

    send_SigTerm(tgen, CWD, "r2") 

    #sleep (10)

    #tgen.mininet_cli()

    logger.info("[Phase 3] : R2 is still down, restart time 120 sec. So time verify the routes are present in BGP RIB and ZEBRA >>>>>> ")
    #Verifying BGP RIB routes
    input_dict = topo['routers']
    dut = 'r1'
    next_hop = "192.168.1.10"
    input_dict = topo['routers']
    result = verify_bgp_rib('ipv4', dut, tgen, input_dict, next_hop, protocol = None)
    if result == True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    #Verifying RIB routes
    protocol = 'bgp'
    result = verify_rib('ipv4', dut, tgen, input_dict, next_hop = next_hop, protocol = protocol)
    if result == True : assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)


    logger.info("[Phase 4] : sleep for 10 sec >>>>>> ")
    sleep (10)

    logger.info("[Phase 5] : R2 is about to come up now >>>>>> ")
    start_router(tgen, CWD, "r2")
    #sleep (5)
    
    logger.info("[Phase 5] : R2 is UP Now ! >>>>>> ")

    # GR test case starts from here.
    input_dict = {
   	"r1": {
       	  "bgp": {
            "bgp_neighbors": {
               "r2": {
                       "graceful-restart": "graceful-restart"
                }
       	     }
           }
         },
        "r2": {
          "bgp": {
            "bgp_neighbors": {
               "r1": {
                       "graceful-restart": "graceful-restart-helper"
                }
             }
           }
         }
    }

  #  tgen.mininet_cli()
    dut = 'r1'
    
    # Verifying GR stats
    result = verify_graceful_restart('ipv4', input_dict, tgen, topo, dut)
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)
   
    result = verify_r_bit('ipv4', input_dict, tgen, topo, dut)
    if result == True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)


    #tgen.mininet_cli()


def test_BGP_GR_Restarting_8():
    logger.info(" Test Case : BGP_GR_Restarting_8 >> BGP GR [Restart Mode]R1-----R2[Restart Mode] ")


    tgen = get_topogen()
    global bgp_convergence
    tc_name = "test_BGP_GR_Restarting_8"
    
    if bgp_convergence != True:
        pytest.skip('skipped because of BGP Convergence failure')
   
    # redistribute static routes from r1 <--- r2 

    # GR test case starts from here.
    input_dict = {
   	"r1": {
       	  "bgp": {
            "bgp_neighbors": {
               "r2": {
                       "graceful-restart": "graceful-restart"
                }
       	     }
           }
         },
        "r2": {
          "bgp": {
            "bgp_neighbors": {
               "r1": {
                       "graceful-restart": "graceful-restart"
                }
             }
           }
         }
    }

    result = configure_graceful_restart('ipv4', input_dict, tgen, CWD, topo)
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    clear_bgp_and_verify('ipv4', tgen, "r1", topo)
    clear_bgp_and_verify('ipv4', tgen, "r2", topo)

    logger.info("[Phase 1] : Test Setup [Restart Mode]R1-----R2[Restart Mode] Initilized >>>>>> ")


    result = verify_graceful_restart('ipv4', input_dict, tgen, topo, dut = "r1")
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    
    # tgen.mininet_cli()

    # Verifying BGP RIB routes
    dut = 'r1'
    next_hop = "192.168.1.10"
    input_dict = topo['routers']
    result = verify_bgp_rib('ipv4', dut, tgen, input_dict, next_hop, protocol = None)
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    # Verifying RIB routes
    protocol = 'bgp'
    result = verify_rib('ipv4', dut, tgen, input_dict, next_hop = next_hop, protocol = protocol)
    if result != True : assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    logger.info("[Phase 2] : R2 goes for reload >>>>>> ")
   
    #tgen.mininet_cli()

    # we need to replace this api with restart. Right now the resatrte api is not working. Test team is working on it.
    #clear_bgp_and_verify('ipv4', tgen, "r2", topo)

    send_SigTerm(tgen, CWD, "r2") 

    #sleep (10)

    #tgen.mininet_cli()

    logger.info("[Phase 3] : R2 is still down, restart time 120 sec. So time verify the routes are present in BGP RIB and ZEBRA >>>>>> ")
    #Verifying BGP RIB routes
    input_dict = topo['routers']
    dut = 'r1'
    next_hop = "192.168.1.10"
    input_dict = topo['routers']
    result = verify_bgp_rib('ipv4', dut, tgen, input_dict, next_hop, protocol = None)
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    #Verifying RIB routes
    protocol = 'bgp'
    result = verify_rib('ipv4', dut, tgen, input_dict, next_hop = next_hop, protocol = protocol)
    if result != True : assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)


    logger.info("[Phase 4] : sleep for 10 sec >>>>>> ")
    sleep (10)

    logger.info("[Phase 5] : R2 is about to come up now >>>>>> ")
    start_router(tgen, CWD, "r2")
    #sleep (5)
    
    logger.info("[Phase 5] : R2 is UP Now ! >>>>>> ")

    # GR test case starts from here.
    input_dict = {
   	"r1": {
       	  "bgp": {
            "bgp_neighbors": {
               "r2": {
                       "graceful-restart": "graceful-restart"
                }
       	     }
           }
         },
        "r2": {
          "bgp": {
            "bgp_neighbors": {
               "r1": {
                       "graceful-restart": "graceful-restart"
                }
             }
           }
         }
    }

    dut = 'r1'
    
    # Verifying GR stats
    result = verify_graceful_restart('ipv4', input_dict, tgen, topo, dut)
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)
   
    result = verify_r_bit('ipv4', input_dict, tgen, topo, dut)
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)


    #tgen.mininet_cli()
    result = verify_f_bit('ipv4', input_dict, tgen, topo, dut)
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    #tgen.mininet_cli()


def test_BGP_GR_Restarting_9():
    logger.info(" Test Case : BGP_GR_Restarting_9 >> BGP GR [Restart Mode]R1-----R2[Helper Mode] ")


    tgen = get_topogen()
    global bgp_convergence
    tc_name = "test_BGP_GR_Restarting_9"
    
    if bgp_convergence != True:
        pytest.skip('skipped because of BGP Convergence failure')
   
    # redistribute static routes from r1 <--- r2 

    # GR test case starts from here.
    input_dict = {
   	"r1": {
       	  "bgp": {
            "bgp_neighbors": {
               "r2": {
                       "graceful-restart": "graceful-restart"
                }
       	     }
           }
         },
        "r2": {
          "bgp": {
            "bgp_neighbors": {
               "r1": {
                       "graceful-restart": "graceful-restart-helper"
                }
             }
           }
         }
    }

    result = configure_graceful_restart('ipv4', input_dict, tgen, CWD, topo)
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    clear_bgp_and_verify('ipv4', tgen, "r1", topo)
    clear_bgp_and_verify('ipv4', tgen, "r2", topo)

    logger.info("[Phase 1] : Test Setup [Restart Mode]R1-----R2[Helper Mode] Initilized >>>>>> ")


    result = verify_graceful_restart('ipv4', input_dict, tgen, topo, dut = "r1")
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    
    # tgen.mininet_cli()

    # Verifying BGP RIB routes
    dut = 'r1'
    next_hop = "192.168.1.10"
    input_dict = topo['routers']
    result = verify_bgp_rib('ipv4', dut, tgen, input_dict, next_hop, protocol = None)
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    # Verifying RIB routes
    protocol = 'bgp'
    result = verify_rib('ipv4', dut, tgen, input_dict, next_hop = next_hop, protocol = protocol)
    if result != True : assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    logger.info("[Phase 2] : R2 goes for reload >>>>>> ")
   
    #tgen.mininet_cli()

    # we need to replace this api with restart. Right now the resatrte api is not working. Test team is working on it.
    #clear_bgp_and_verify('ipv4', tgen, "r2", topo)

    send_SigTerm(tgen, CWD, "r2") 

    #sleep (10)

    #tgen.mininet_cli()

    logger.info("[Phase 3] : R2 is still down, restart time 120 sec. So time verify the routes are present in BGP RIB and ZEBRA >>>>>> ")
    #Verifying BGP RIB routes
    input_dict = topo['routers']
    dut = 'r1'
    next_hop = "192.168.1.10"
    input_dict = topo['routers']
    result = verify_bgp_rib('ipv4', dut, tgen, input_dict, next_hop, protocol = None)
    if result == True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

    #Verifying RIB routes
    protocol = 'bgp'
    result = verify_rib('ipv4', dut, tgen, input_dict, next_hop = next_hop, protocol = protocol)
    if result == True : assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)


    logger.info("[Phase 4] : sleep for 10 sec >>>>>> ")
    sleep (10)

    logger.info("[Phase 5] : R2 is about to come up now >>>>>> ")
    start_router(tgen, CWD, "r2")
    #sleep (5)
    
    logger.info("[Phase 5] : R2 is UP Now ! >>>>>> ")

    # GR test case starts from here.
    input_dict = {
   	"r1": {
       	  "bgp": {
            "bgp_neighbors": {
               "r2": {
                       "graceful-restart": "graceful-restart"
                }
       	     }
           }
         },
        "r2": {
          "bgp": {
            "bgp_neighbors": {
               "r1": {
                       "graceful-restart": "graceful-restart-helper"
                }
             }
           }
         }
    }

  #  tgen.mininet_cli()
    dut = 'r1'
    
    # Verifying GR stats
    result = verify_graceful_restart('ipv4', input_dict, tgen, topo, dut)
    if result != True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)
   
    result = verify_r_bit('ipv4', input_dict, tgen, topo, dut)
    if result == True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)


    result = verify_f_bit('ipv4', input_dict, tgen, topo, dut)
    if result == True : 
        assert False, "Testcase " + tc_name + " :Failed \n Error: {}".format(result)

if __name__ == '__main__':
    args = ["-s"] + sys.argv[1:]
    sys.exit(pytest.main(args))
