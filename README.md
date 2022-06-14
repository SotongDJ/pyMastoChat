# pyMastoChat

Chatbot that base on Mastodon.py for Mastodon instance

## Installation

* clone repo and submodule

```bash
git clone https://github.com/SotongDJ/pyMastoChat.git
cd pyMastoChat
git submodule init
git submodule update --init --recursive
# future submodule update
git submodule update --remote --recursive
```

* setup virtual environment (use whatever you want) and activate

* install Mastodon.py

```bash
pip install Mastodon.py
# if python2 exist
pip3 install Mastodon.py
```

## Configuration

* set [bot_name] in self.bot_name

* prepare secret/token file

    * secret-[bot_name].json

    ```JSON
    {
        "access_token": "API token",
        "hostname" : "https://insert your mastodon instance"
    }
    ```
