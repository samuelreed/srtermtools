# srtermtools

This is a collection of terminal tools, usually triggered as part of a chain of .*rc files in order to display a few reminders and checks. 

Example of outputs:
![Example Terminal Screenshot](images/example.png)

* daycounter - gives a console output for the # of days since or before an upcoming event. Nice to keep track of accomplishments, upcoming events, or check how long since something has happened such as accidents on the factory floor.
* sitecheck - performs quick fuzzy hashes of websites and can check up on the hashes to identify various degrees of bit changes. Intended as a lightweight tripwire for changes or if the site is unavailable.
* routerrebooter - performs quick resets and port forwarding changes for the ancient Technicolor brand TC8305C router. It is pretty janky, and the whole request/resp flow was reverse engineered with a proxy since there is no API. 
* aqicheck - checks air quality index for a zipcode, defaulting to the author's home. You will need an API key by signing up for one at https://docs.airnowapi.org/login and dropping it in a .dirty-aqi-api-key file.aq