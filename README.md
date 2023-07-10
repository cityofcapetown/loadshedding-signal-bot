# loadshedding-signal-bot

Simple AWS SNS to Signal Group relay

## Getting Started

### Signal CLI Server
You probably don't want to expose this to the wild Internet, so use a SSH tunnel when setting up on a remote server.

1. Run signal-cli-rest-api in `normal` mode first.

```bash
docker run --rm -p 8080:8080 \
    -v $(PWD)/signal-cli-config:/home/.local/share/signal-cli \
    -e 'MODE=native' bbernhard/signal-cli-rest-api
```

2. Open http://127.0.0.1:8080/v1/qrcodelink?device_name=local to link your account with the signal-cli-rest-api server

3. In your Signal app, open settings and scan the QR code. The server can now receive and send messages. The access key
   will be stored in `$(PWD)/signal-cli-config`.

4. The logs should show something like this. You can also confirm that the server is running in the correct mode by
   visiting http://127.0.0.1:8080/v1/about.

```
...
time="2022-03-07T13:02:22Z" level=info msg="Found number +491234567890 and added it to jsonrpc2.yml"
...
time="2022-03-07T13:02:24Z" level=info msg="Started Signal Messenger REST API"
```

5. The bot needs to send to a group. Use the following snippet to get a group's `id`:

```bash
curl -X GET 'http://127.0.0.1:8080/v1/groups/<your number, e.g. +49123456789>' | python -m json.tool
```

### Running the server
1. Run the service with the command line utils configured:

```bash
docker run --rm -p <port number for the service you wish to expose, e.g. 5001>:5000 \
    -e "SIGNAL_HOST=`hostname`:8080" -e "SIGNAL_PHONE_NUMBER=<phone number of bot, e.g. +271234567890>" \
    -e "SIGNAL_GROUP_ID=<group name of Signal Group, e.g. group.UzBpZ0tQbHU5eU4wcWdLS1JoTGNKOWRIVkVwM83d42swcmFyVXdj1234z0=>", \
    -e "SNS_TOPIC_ARN=<ARN of SNS topic to forward on to group e.g. arn:aws:sns:af-south-1:566800947500:loadshedding>" \
    cityofcapetown/loadshedding-signal-bot:dev
```

2. Subscribe to the SNS Topic. Probably easiest to do this using the AWS CLI:

```bash
aws sns subscribe \
  --topic-arn <ARN of SNS topic to forward on to group e.g. arn:aws:sns:af-south-1:566800947500:loadshedding> \
  --protocol https \
  --notification-endpoint <the endpoint of your service, e.g. http://my-domain.co.za/sns>
```

you should get back the following response:
```json
{
    "SubscriptionArn": "pending confirmation"
}
```

3. Check the bot's logs for the confirmation URL, there should be a message that looks like:
```
Visit 'https://sns.us-west-2.amazonaws.com/?Action=ConfirmSubscription&TopicArn=arn:aws:sns:us-west-2:123456789012:MyTopic&Token=2336412f37...' to confirm subscription
```

4. Follow the link in the log, and you should get the response:

```xml
<ConfirmSubscriptionResponse>
    <ConfirmSubscriptionResult>
        <SubscriptionArn>
            arn:aws:sns:af-south-1:566800947500:loadshedding:0f7219ab-cc3d-4aa5-85de-6264c6d8131b
        </SubscriptionArn>
    </ConfirmSubscriptionResult>
    <ResponseMetadata>
        <RequestId>2c3893de-5d67-5ccc-8cc8-cefba8834559</RequestId>
    </ResponseMetadata>
</ConfirmSubscriptionResponse>
```

### Running a SSL Proxy
(this is necessary if the SNS topic uses https to communicate)

1. Use [EFF's certbot](https://certbot.eff.org/) to acquire a SSL certificates for your server
2. Customise the [Nginx config template](./static/nginx_config.conf)
3. Run the nginx docker image, using your config and SSL certs:

```bash
docker run -d --restart always \
  -v /etc/letsencrypt:/etc/nginx/certs:z \
  -v $PWD/nginx_config.conf:/etc/nginx/conf.d/default.conf \
  --name signal-bot-proxy \
  -p <port you want to listen for SSL connections on, e.g. 10443>:443 \
  nginx
```
