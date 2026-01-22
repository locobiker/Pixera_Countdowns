# Pixera_Countdowns
During Live Production events, there are many hard cues to capture on camera.  For example: drum solo, lead switch, etc.  The goal of this application is to increase production quality by providing countdowns to selected critical cues.  The goal was to have a single backend script polling Pixera for cues while having multiple frontends utilizing that data and displaying countdowns. 

Credit: This application was primarily vibe-coded using cursor.  I did a lot of modification and cleaning, but cursor did most of the hard work.  

Requirements:
 - Pixera (The free version works fine.  See the Pixera section below for more information.)
 - Docker

How to set up:
 - Install Python - The scripts will download other dependencies as needed.
 - Download Pixera - On a different computer on the network is more realistic
 - Update the PIXERA_HOST variable in start_production.sh to the actual IP.
 - Update the PIXERA_PORT variable in start_production.sh (default is 4023)

How to Run:
 - Execute the Start_PixCountdowns_Prod file
 - Go to the website::port indicated by the script (default is http://localhost:3000).
 - See section for Front End Operation for more details.
 - To stop the backend, go to the Docker UI and click stop for the Pixera_Countdowns
 - If you update any of the source files, you will need to run the Update_PixCountdowns_Prod if the docker has been generated at any time before.

 Other Utilities:
 - Start_Pixcountdowns_Dev command will enable hot-reload.  So you can modify the source files and it will automatically reload.
   + To update the source files, just edit it as you normally would.  Docker looks at the original files instead of making an image.

Pixera:
 - See the website:  https://help.pixera.one/api/api-quick-start-guide
   + For this application to work, select HTTP/TCP(dl) Protocol, recommend to use port 4023 to match script default.
 - Note: If Pixera is also connected to StreamDeck, you need to supply a HTTP/TCP connection also.  Streamdeck doesn't seem to support the (dl) option.
 - The script will find all Play cues.  So insert a play cue at the time you want a timer to count down to.
 - If desired, prefix the cue name with "A_" and you can filter to see only those cues in the timers.  
 - Cue Notes work as well and will be displayed in the countdowns.

Pixera Polling Discussion:
This needed its own section since there are a few strategies that were thought of, thought I would document them for reference.  The goal was to not overwhelm Pixera with too many API calls, and only really care about specific time windows.  We dont need the backend polling every time pixera was used during show programming.  So we needed an on/off polling switch.  In an abundance of caution, there is also a 6 hour timeout to the polling in case someone forgets to disable it manually.

Some strategies that were tried:
 - Searching + fast: Slow polling to find changes, then fast polling once changes occurred.  Decided against this because there was already an on/off switch.
 - Pixera emitted signals (setMonitoringEventMode).  It doesnt work.  I made a ticket and they confirmed that it only partially works.  I was trying to capture every event.  I think it would have been too many events anyway.
 - 100ms Polling.  This is the solution I landed on.  Since we already have an on/off window, it doesnt hurt that much to just poll every 100ms.  That way, we get single-decimal accuracy on timers.

There are actually two pollings occurring when enabled. 
1) 10 second Project/Timeline check.  Since Projects and Timelines are not created/changed very often, we check this every 10s
    - Pixera.Timelines.getTimelines
    - Pixera.Timelines.Timeline.getTimelineInfosAsJsonString
2) 100ms Cue check
    - Pixera.Timelines.Timeline.getCueInfosAsJsonString


Front End Operation:
1) Enable Polling.  This should update the Project Information and the current playlist's cues
2) Timeline Selection.  You can select the timeline to view instead of the currently playing one.
3) Cue Filter.  Filter on cues that start with "A_" only.
4) Timers: List of the 10 next upcoming cues.  The timers re-sync every 100ms, the frontend doesnt do any counting.
 
Notes:
There are some interesting behaviors with countdowns and timeline display.
 - Once the timeline playhead reaches past all the cues, the timeline will no longer be shown.
 - Countdowns may display strange times when the timeline is not playing.
 - If you have many timelines and they jump back and forth a lot, it could be difficult to keep track where you are and whats next.  The application doesnt follow jump cues to find the upcoming cues on a different timeline.

 Example:
 Timeline 1  ------- Cue 1 ---- Cue 2 (jump to timeline 2, Cue 1)---- Cue 3
 Timeline 2  ------- Cue 1 ---- Cue 2 ---- Cue 3

So, the timers will initially display Timeline 1 Cues 1, 2, and 3.
Then, after the jump cue, it will display Timeline 2 Cues 2 and 3.

Ideally, it would notice the jump cue and display the Timeline 2 cues in the actual order they will occur.  That can be a feature for a later date.