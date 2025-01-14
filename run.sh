docker build -t table_analyzer2 .
docker run -v ./tmp/:/app/tmp -e HTTP_PROXY="http://10.177.44.113:7890" -e HTTPS_PROXY="http://10.177.44.113:7890"   -e NO_PROXY="localhost,127.0.0.1" -e OPENAI_API_KEY=$OPENAI_API_KEY --rm table_analyzer2