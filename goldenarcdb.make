mongo := /nfs/site/disks/da_infra_1/users/yltan/depot/da/infra/dmx/main/bin/mongo
host := ppgdacron03.png.intel.com
exe := ssh -t $(host) 

prod:
	$(exe) "$(mongo) 'mongodb://GOLDENARC_so:lMbS1PiFqBiKaVe@p1fm1mon152.amr.corp.intel.com:8150,p2fm1mon152.amr.corp.intel.com:8150,dr1ormon152fm1.amr.corp.intel.com:8150/GOLDENARC?replicaSet=mongo8150' "
dev:
	$(exe) "$(mongo) 'mongodb://GOLDENARC_TEST_so:zXqZm7b05UkFfZg@p1fm1mon152.amr.corp.intel.com:8150,p2fm1mon152.amr.corp.intel.com:8150,dr1ormon152fm1.amr.corp.intel.com:8150/GOLDENARC_TEST?replicaSet=mongo8150' "
	

.PHONY: prod dev
