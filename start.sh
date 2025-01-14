docker build -t table_analyzer .
docker run -e HTTP_PROXY="http://10.177.44.113:7890" -e HTTPS_PROXY="http://10.177.44.113:7890"   -e NO_PROXY="localhost,127.0.0.1" -p 5000:5000 -it -e OPENAI_API_KEY=$OPENAI_API_KEY  -e SERVER_IP="http://106.15.170.182:9210" table_analyzer > ./log/1.log 2>&1