DB := TNRTEST
CMD := /usr/intel/bin/mysql -h maria3512-us-fm-in.icloud.intel.com -P 3306 -u PSGINFRA1_so -pPSGINFRA1so -D PSGINFRA1
CMD := mysql -ukillim -pkillim -h pg-icesql1.altera.com $(DB)
TABLE :=



shell:
	$(CMD)

.PHONY: shell


create_certificate_table:
	$(CMD) -e "CREATE TABLE certificate (id	INT NOT NULL AUTO_INCREMENT, PRIMARY KEY (id), thread VARCHAR(50), milestone VARCHAR(20), project VARCHAR(50), variant VARCHAR(50), config VARCHAR(150) );"
.PHONY: create_certificate_table

create_goldenarc_table:
	$(CMD) -e "CREATE TABLE goldenarc (id INT NOT NULL AUTO_INCREMENT, PRIMARY KEY (id), thread VARCHAR(50), milestone VARCHAR(20), flow VARCHAR(50), subflow VARCHAR(50), tool VARCHAR(150), version VARCHAR(150) );"

droptable:
	$(CMD) -e "drop table if exists $(TABLE);"
.PHONY: droptable

showtables:
	$(CMD) -e "show tables;"
.PHONY: showtables

showcolumns:
	$(CMD) -e "show columns from $(TABLE);"
.PHONY: showcolumns

showrows:
	$(CMD) -e 'select * from $(TABLE) order by flow asc, subflow asc, tool asc;'
.PHONY: showcolumns

