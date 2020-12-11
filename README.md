# web-scraping-at-edge

How to use Web Scraping @edge with Raspberry PI, AWS Kinesis Data Firehose and AWS Glue.

<img src="https://github.com/vittorio-nardone/web-scraping-at-edge/blob/master/img/architecture.png" width="80%" />

About this project:
- Run a Docker container on Raspberry PI to perform web scraping of a [Paradox](https://www.paradox.com/) IP150 web interface to get motion detectors status
- Push captured data to a AWS Kinesis Data Firehose stream
- Perform ETL with a AWS Glue job
- Use a Notebook to view detected Events and Vectors

Please read blog post at https://www.vittorionardone.it/en/digital-transformation-blog/

NOTICE: scraping is tested on Italian version of IP150 UI. To add support to other language, please edit "paradox.py".

## Docker setup (on Raspberry PI)

Please install Docker and Docker-Compose first on your Raspberry PI.

1) Create ".env" file and provide these variables:

```
PARADOX_IPADDRESS=192.168.1.x
PARADOX_USERCODE=xxxxxx
PARADOX_PASSWORD=yyyyyyyyyy
KINESIS_STREAM=paradox-stream
KEYPRESS_CHECK=1
```

2) Create ".aws-credentials" file to provide you access key:

```
[default]
aws_access_key_id=AAAAAAAAAAAAAAAAA
aws_secret_access_key=XXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

3) Build image and run container
```
docker-compose up
```

## Vectors detection

<img src="https://github.com/vittorio-nardone/web-scraping-at-edge/blob/master/img/vectors.png"  width="40%" />

## Heatmap

<img src="https://github.com/vittorio-nardone/web-scraping-at-edge/blob/master/img/heatmap.png"  width="40%" />


