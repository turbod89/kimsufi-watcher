# Kimsufi watcher

Watch for the changes of Kimsufi servers and send a telegram when a change raise.

## Env variables

Need to setup two enviorement variables to run it:

```bash
    export API_TOKEN=<your telegram bot api token>
    export CHAT_ID=<chat id where messages will be sent>
```

After that just `python main.py`.
