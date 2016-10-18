# Usage :
In Frontend: python main.py

In Background: python main.py > $(date -d "today" +"%Y%m%d%H%M").log 2>&1 &


# Superlist Bulk import Preprocessor

This project is a part of Step 2 of our Directory Listing project. Here we pre process all the scrapped entry to make it meaningful for us. 

This pre processing script that will run before data is fed inside WP All Import plugin. This pre processing script will convert input data into a format that is compatible with Superlist.

Also this script will help us in decreasing manual effort of our Operations team, thus saving a lot of time and causing less number of errors.

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

## Running Python script in background:

```python
python <filename>.py &

```
## Running Python script in background and directing the console messages to log file:

```python
python <filename>.py > {datetime}.log 2>&1 &
```

* Specifically tested on linux systems
* In our case substitute \<filename> with main
* For substituting {datetime} with actual date time:

 ```$(date -d "today" +"%Y%m%d%H%M")```

### Finding phone number patterns in file

```python
python findNoPat.py
```
* It will work on all processed files and save the output to ./output/PatMatch
