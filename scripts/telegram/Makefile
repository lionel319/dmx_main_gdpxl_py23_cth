# TEL
# https://thecodersblog.com/sending-the-message-on-telegram-using-cUrl/


ENVVAR := env -i https_proxy=proxy.fm.intel.com:911 
CURL := curl -skm 5
TOKEN := 1273562660:AAGts8oZrTNsfTBDk3FctRuf7NHVetm5Ysk
BOT := test1
# @lionel_test1bot
ID := -1001451312344
BASEURL := https://api.telegram.org/bot$(TOKEN)

get_message:
	$(ENVVAR) $(CURL) $(BASEURL)/getUpdates 

MSG := 
send_message:
	$(ENVVAR) $(CURL) -X POST \
		-H 'Content-Type: application/json' \
		-d '{"chat_id": "$(ID)", "text": "$(MSG)", "disable_notification": false}' \
		$(BASEURL)/sendMessage




send_icm_chart: download_icm_chart
	env -i https_proxy=proxy.fm.intel.com:911 curl -X POST -F chat_id=1223897566 -F photo='@a.jpg' https://api.telegram.org/bot1273562660:AAGts8oZrTNsfTBDk3FctRuf7NHVetm5Ysk/sendPhoto

download_icm_chart:
	wget -v -O a.jpg --no-check-certificate --user=guest --password=guest 'https://sj-mon.altera.com/nagios/pnp/index.php?host=sjicm02&srv=MySQL_Threads_Queries&source=1&view=0&display=image'

