## Data Enrichment API

This project is a generic API to enrich any input contact details.

If leverages following APIs for Data enrichment:

1) Google AutoComplete
2) Google Places
3) Geo Geolocation
4) Facebook Graph
5) Twilio

Soon, support will be added for Wikipedia.

Other Features:
* As part of data enrichment API, it removes wrong email addresses. 
* It supports multiple keys, which will be automatically changed in case first key is failed.
* Wrong Contact numbers will be automatically removed
* Default image will be automatically added in case no image is available.

Note:
* Though contact number API is made to cater to India, it can easily be extended to other countries.
* Currently City State data is only for India. To make it extendible, add your own data
* Working Hours are serialized in PHP Serialization Format.


## Usage :
In Frontend: 
    python main.py

In Background: 
* Specifically tested on linux systems
* In our case substitute \<filename> with main
* For substituting {datetime} with actual date time:
    python main.py > $(date -d "today" +"%Y%m%d%H%M").log 2>&1 &

### For Installing requirements:

```python
pip install -r requirements.txt
```
If there is <b>InsecurePlatformWarning</b>:

```python
pip install pyopenssl ndg-httpsclient pyasn1
```

## Utilities

### Finding phone number patterns in file

```python
python findNoPat.py
```
* It will work on all processed files and save the output to ./output/PatMatch

### Add RowId

To add Row Id, run 
```python
python util/addUniqueId.py
```


## Running Process in a separate 'tmux' session

This prevents the running job from getting terminated in case you loose your ssh connection.
Create a new tmux session:

    $  tmux new -s <session_name>

It logs you in a new session in tmux server.
This session will keep running until you exit all the windows in it, or kill it manually.
When any problem with ssh connection happens, you get detached to this session.
Still the started jobs keeps running in it.

Once detached, you can re-attach to the started session:

    $ tmux a -t <session_name>

In case you forget the session name, you can check out the active sessions in the main terminal:

    $ tmux ls

All the terminal properties are preserved, and will happen relative to the session you start the jobs in.
So running the script is same as described below.
