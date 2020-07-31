# Hey Google... talk to Train Alarm!

Create reminder and get a notification when your train is approaching your destination station!

Train Alarm is an Indian train assistant. Tell your 'PNR Number' and you are all set. Be informed when your train is about to reach your destination station within a radius of 10 km to 35 km, so you'll never miss your stop.

## Getting Started

Just ask your Google Assistant: "*Talk to Train Alarm*" and follow through the instructions.

[Here](https://github.com/tusharsoni08/alert_cron_job) is the cron job code, which will send a notification to user when their train is about to reach their destination station.

## API interactions
![API Flow](https://user-images.githubusercontent.com/5249024/89019114-74d68080-d33a-11ea-8eed-65db0fd5745a.png)

1. The end-user types or speaks an expression.
2. Your service sends this end-user expression to Dialogflow in a detect intent request message.
3.  Dialogflow sends a detect intent response message to your service. This message contains information about the matched intent, the action, the parameters, and the response defined for the intent.
4. Your service performs actions as needed, like database queries or external API calls.
5. Your service sends a response to the end-user.
6. The end-user sees or hears the response.

This is how user will have notification: 

<img src="https://user-images.githubusercontent.com/5249024/50975439-97643700-1513-11e9-99bb-d20de82f42c1.jpg" width="400" height="830">

And here is the T-shirt which i have received from Google after publishing my first action for Google Assistant :)
![google-t-shirt](https://user-images.githubusercontent.com/5249024/50989538-a825a480-1535-11e9-89df-54a64ef89dcc.jpg)
