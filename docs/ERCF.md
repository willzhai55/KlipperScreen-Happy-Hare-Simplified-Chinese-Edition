# KlipperScreen Panels for ERCF - Happy Hare

## Introduction
KlipperScreen ERCF Happy Hare edition is quite a mouthful!  It is a forked version of KlipperScreen designed to run/manage ERCF using the Happy Hare driver software.

KlipperScreen is an amazing piece of software but unfortunally lacks the level of plugin integration I needed for this project.  I hope in the future to have changes integrated so that this becomes a layered install at most.  Until then you must follow these install directions closely:

## Installation
Install and setup a base KlipperScreen from the original source. Get it working. Don't skip this step because I cannot help with basic KlipperScreen and system setup.

    > cd ~/KlipperScreen
    > git remote set-url origin https://github.com/moggieuk/KlipperScreen.git
    > ...
   
    > cd ~/KlipperScreen/happy_hare
    > ./install_ks -g <num_gates>
   
(where <num_gates> is the number of selectors you built with, e.g. 9)
   
KlipperScreen will be restarted and hopefully you are now running the enhanced version!

Expert tip: The last step of running './install_ks -g <num_gates>' can be run many times.. if you customize the ERCF part of the KlipperScreen menu and want to make use of the "replicator" function that will automatically replicate menu options for the configured number of gates, you can edit menus.conf and reference the templating there.

Note that the base KlipperScreen is fully up-to-date (as of March 10th, 2023) with the master but includes extra functionality that can be used in the creation of custom menus.  See the generated ercf_klipperscreen.conf for clues!

## Request
Remember that this is current a Beta release.  I need/want your help in finding corner cases, bugs or ideas for improvement.  I can offer limited help on the Discord channels but I would prefer if you submit an issue report via github so I can manage them.  This project and Happy Hare itself have taken a lot of time. I have a lot more planned so I need your help in organizing my work.

Also, some folks have asked about making a donation to cover the cost of the all the coffee I'm drinking.  I'm not doing this for any financial reward but it you feel inclined a donation to PayPal https://www.paypal.me/moggieuk will certainly be spent making your life with ERCF more enjoyable.

Thank you!

## Caveats
I have only tested on a single screen.  A 640x480 resolution BTT TFT5.0.   I am not a UI programming expert and it is possible that you might find layout problems on other (likely smaller) displays.  Also, I have only tested in and optimized for horizonal orientation.  I doubt it will be effective in vertical but I don't know of any Voron owners with vertically mounted panels. 

*All screen shots are taken with the "Colorize" theme.  The default is z-bolt and looks slightly different (which I actually prefer)*

## Main Panel

![ercf_panel_non_printing](img/ercf/ercf_main.png)

This is the main screen and is accessed by clicking on the little carrot on the left navbar.   Note that you can turn off this carrot in settings in whch case buttons will automatically be added to the KlipperScreen home and print pages.  Personally I think ERCF deserves this first class link.

The philosopy behind this screen is that it works with the concept of 'Tool' which is really a virtual entity in Happy Hare because of the Tool-To-Gate mapping.  When you are actually printing the panel will look a little different:

![ercf_panel_printing](img/ercf/ercf_main_printing.png)

The top left button is replaced with a live monitor of Happy Hare clog/runout detection.  This 'thermonitor' usually will sit at the bottom of the scale.  As the difference between extruder and encoder measured movement increases the 'temperature' will rise.  If it hits the top a runout condition will be triggered.  The configurable check mark on the side is the 'headroom' used by the automatic tuning option and represents a safe gap to avoid accidental firing.  The detection length (and headroom) are all tunable, but with automatic, they will be updated at least every tool change.

_Perhaps someone can help me... now you can visualize when clog detection is triggered, can you figure out what is being done in the wipe tower -- I'll let you see for yourselves..._

If you have a bypass (aka passthrough) installed, and I think they are very useful, then clicking "to the left of T0" will bring you to the bypass selector:

![ercf_panel_bypass](img/ercf/ercf_main_bypass.png)

When bypass is selected, the 'Colors...' button and Eject button change to 'Load (Bypass)' and 'Unload (Bypass)' respectively.  Unloading and selecting a tool will restore the buttons.

Oh, the "text" representation mirrors that you see in the Klipper console, but this one dynamically updates!

_Expert Tip: With this new level of visualization I would recommend you put Happy Hare persistence level to the maximum of '4'...  Turn on, check KlipperScreen and go..._

## Manage Panel

![ercf_manage](img/ercf/ercf_manage.png)

This screen is accessed by the top right button when not in print (you shouldn't be doing anything here while printing anyway).  Conceptually it is working in the physical space with the concept of Gate (and not Tool).  That distinction is important.   I think most functions are obvious, but the 'Load Extruder' and 'Unload Extruder' may be new to you.  These do exactly as there names suggest and are designed to help sort out the ERCF when it is enraged and you need to do some manual operations.

There is one very important button: 'Recover State...'. Since Happy Hare is stateful and will refuse to do things if it doesn't think you should do them, you might need to correct it's state before continuing.

## Recover Panel

![ercf_recover](img/ercf/ercf_recover.png)

This is what the 'Recover State...' button reveals.  It shows what Happy Hare thinks the current state is, allows you to manuall reset on the right side of the screen or 'Auto Recover' just the filament LOADED/UNLOADED state.

You can also reset all the persisted state that Happy Hare records across restarts (useful if you are running with persistence level of '4' or have messed with Tool-To-Gate maps, EndlessSpool groups or got completely confused).

One note: If you move the selector on the Manage panel you will change the gate state to another postion. This is physical are real.  Because of TTG mapping the Tool will be reset to 'unknown'.  Why?  Well, because a tool can be mapped to many gates with EndlessSpool.  A gate might not even have a tool mapped to it or it might have more that one tool.

## Tool Picker Panel

![ercf_picker](img/ercf/ercf_picker.png)

Ooops, did I include that?!? ;-)  Check back later, but rest assured, Bambu Labs AMS will not have the advantage for long!

## User extensible management panel

![ercf_manage_menu](img/ercf/ercf_user_manage_menu.png)

The bottom left 'More...' button brings up this panel.  This one is not custom but uses the KlipperScreen menu concept. Therefore it is extensible by users. If included a lot of useful stuff and have replicated some functionality found elsewhere as individual descrete buttons (like load tool or select gate).  Some might prefer this but feel free to comment it out if you don't like duplication.  Also you can use the menu logic that is there as a guide to add you own special macros.

## User extensible calibration/test panel

![ercf_klipperscreen](img/ercf/klipperscreen_config.png)

If you really don't like typing on the Klipper console, all the important calibration and test macros can be accessed under 'ERCF Settings' via the KlipperScreen 'Configuration' page.

![ercf_calibration_menu](img/ercf/ercf_user_calibration_menu.png)

Here is the set that is included by default.


    (\_/)
    ( *,*)
    (")_(") ERCF Ready
