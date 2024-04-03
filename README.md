![single_tile](https://github.com/DurableSteer/tiles/assets/140595465/330805dd-f951-40a7-80c1-63ac52a086ab) ![two_tiles](https://github.com/DurableSteer/tiles/assets/140595465/c17181ee-2853-4c1f-89c7-32e10b81e5ae)

(excuse my crappy phone camera)

# Tiles
Gif tiles are small modular displays that can play animated gifs. The tiles share a common usb power source and connect magnetically so they can be rearranged as one likes and multiple tiles only use one power cable. The tiles use an esp8266 module and gifs are uploaded easily from any computer in the WiFi network via a basic GUI i called tileman.

This is going to cover the software side of this project. If you are looking for the hardware side and building instructions they can be found at [insert link] .

## dependencies
The tileman script uses PyQt6, and ftplib. 
It also uses my convert.py script.

The convert script uses Pillow, and the colorthief module.
All of those libraries can be installed via pip easily.

Furthermore the convert script uses gifscicle by kohler (https://github.com/kohler/gifsicle) which can be downloaded from https://www.lcdf.org/gifsicle/ . 
The convert script requires the gifscicle.exe to be in the same working directory as convert.py!

The gif_tile sketch uses the following libraries:
- AnimatedGIF by bitbank2(Larry Bank) (https://github.com/bitbank2/AnimatedGIF)
- WiFiManager by tzapu (https://github.com/tzapu/WiFiManager)
- SimpleFTPServer by xreef(Renzo Mischianti) (https://github.com/xreef/SimpleFTPServer)
- TFT_eSPI by Bodmer (https://github.com/Bodmer/TFT_eSPI)
  
These libraries can be simply installed from the library manager in the arduino ide.

## How to Install
### "installing" the scripts
Currently the scripts are only tested and developed under Windows 10.
1. Install python and pip (i used python3) from https://www.python.org/downloads/ .
   (Make sure that you check the "Add python.exe to PATH" option on the first page of the installation.)
3. Install the following dependencies in the terminal via pip:
   - PyQt6 via `pip install PyQt6`
   - Pillow via `pip install pillow`
   - colorthief via `pip install colorthief`
5. Download "convert.py", "start_tileman.bat" and "tileman.py" and place them in an empty folder of your choice.
6. Download the precompiled gifscicle zip from https://www.lcdf.org/gifsicle/ and unpack into the same folder.
7. Make sure that "convert.py", "start_tileman.bat", "tileman.py" and "gifsicle.exe" are in the same folder and named that.
8. Done. You can now start tileman with doubleclicking start_tileman.bat or directly starting the tileman.py script from the terminal.
   (if no tiles are found check if the firewall is disallowing access to the network)

### installing the sketch onto an esp8266 board
1. Install the Arduino IDE from https://www.arduino.cc/en/software
2. Install AnimatedGIF by Larry Bank, WiFiManager by tzapu, SimpleFTPServer by Renzo Mischianti and TFT_eSPI by Bodmer in the Arduino IDE with the IDEs library manager.
3. Download the "gif_tile.ino" from the sketch folder and open it with the Arduino IDE.
4. Make sure that your esp8266 board is set up and selected.
5. Change the flash table in the IDE under Tools->Flash Size . Most common esp8266 boards come with 4MB Flash. If your esp8266 board has 4MB too choose 4MB(FS:3MB OTA:512KB). If your board has less or more flash choose the highest FS for your flash size with OTA. (FS is going to be the amount of space you will have to save gifs to the tile!) If you have the option change Tools->CPU Frequency to 160MHz as well.
6. Replace the User_Setup.h in the TFT_eSPI library folder (normally saved at C:\Users\[username]\Documents\Arduino\libraries\TFT_eSPI\User_Setup.h ) with the one from this repository at  sketch/[your display driver]/User_Setup.h (if you have problems with your display you may change settings here, depending on your display changes may be necessary. You can find additional information in the file or at the wiring section of the building guide at printables. This file will be automatically overwritten on each update of the TFT_eSPI library so keep a copy!)
7. Upload the sketch to your board. The display should show text and the tile should be emitting a WiFi access point with a name similiar to "ESP-5FCA28".
8. Connect to the emitted WiFi access point and connect the tile to your local WiFi network via the landing page.(if the landing page isn't opened automatically it is available at 192.168.4.1 via your browser.)(If you connect with your fone you may need to disconnect your mobile data before you can access the landing page.)
9. Done. You can now find your tile with the tileman or an ftp client from the same network.

## How to use
### Tileman 
![image](https://github.com/DurableSteer/Tiles/assets/140595465/cb5b67de-3096-4a8d-876f-23caceef3844)

The tileman GUI allows easy upload of any gif you want a gif tile in the same WiFi to display. It also converts gifs before upload via the convert.py script as later explained and allows for deleting files off the gif tiles. 
### Tileman functions
#### Upload
Gifs can be simply dragged and dropped onto the tile you want it to be uploaded to. You can upload one or multiple files with one drag and drop. Currently only gif files can be handled by the GUI. The gif will then be converted based on the tiles current settings for upload. (See _Convert_) The upload percentage during a files upload is displayed on the progress bar.
If there isn't enough free storage on the tile a message will be printed to the terminal and the file won't be uploaded.
#### Deletion
Files present on a tile are displayed on the right behind the delete all button. Each file can be deleted individually with the 'x' button to the right of the filename. Additionally all files on the tile can be deleted with the delete all button.
#### Convert
Dropped files will first be converted with the convert.py script based on the settings in the leftmost panel for each tile. Settings can be changed for each file uploaded and only affect the file later uploaded. No settings on the tile will be changed. 
-The following options are available from top to bottom:-
##### orientation
The orientation combobox lets you choose the orientation of the gif/gifs uploaded. A tiny triangle on top of the tile will be the top of the standard portrait orientation. Each of the following options turns the image by 90° clockwise.
##### just upload
If the 'just upload' tickbox is checked files will be uploaded to the tile without any conversion the file will also not be rotated.
##### resize and remove transparency
This tickbox will resize the file to fit the tiles displays resolution, rotate it based on the orientation setting and replace the files transparent pixels with black.
##### convert with custom bgcolor
When chosen this option will resize, rotate and replace the gifs transparent pixels with the color chosen. The color can be picked by clicking the 'pick color' button directly underneath the button will then display the chosen color.
##### convert with auto bgcolor
This option will resize, rotate and replace all transparent pixels by a fitting color to be chosen automatically by the convert script. This is the default option and it is recommended to use.
#### refresh tile contents & scan for tiles again
These buttons are generally not necessary to use. The script will only update the view when an action is taken that would change the element in question. If you for some reason expect that not all the tiles contents are displayed you may use the 'refresh tile contents' button to force a manual update for all found tiles files. 
Similarly if the script doesn't find all tiles in the network or you restart a tile or add a new tile to the network you may press the 'scan for tiles again' button to manually scan for tiles in the network. Due to a high timeout this option can only be used after about 30 seconds from the last scan. If the button is pressed before the last scan is finished no action will be taken and a message will be printed to the terminal.
##### The terminal
When starting the start_tileman.bat a terminal will open with the GUI, if starting the tileman.py directly from the terminal that terminal is going to function as the tilemans terminal.
The tileman will give comprehensive information about it's current workings in the terminal. Errors and progress information can be gathered there, though it is not necessary to read or pay attention to in normal use.

### The Tiles
The Tiles try to display any file in their local filesystem on the connected screen. Tiles have to be connected to a local WiFi network to be set up and they host a basic ftp server through which files can be uploaded and deleted. Updates can be applied wirelessly. I will give a brief description on how each of the parts work and how you may interact with them.
#### The Filesystem
The tiles use the inbuild implementation of LittleFS to store files in the esp8266s flash. The most common variants of the esp8266 have 4MB of flash of which ~3MB are available as storage to save gifs in. If you get a version of the esp8266 with more storage you have to adjust the flash partition table in the Arduino IDE otherwise you will still end up with 3MB of usable storage.(3MB seem to be plenty of space for gifs during my testing. I don't recommend going out of your way to increase storage though adding an SD card or spi flash is certainly possible.)
#### The WiFi 
The Wifi connection is handled by the WifiManager library. Once a tile goes online it will try to connect to the local WiFi. If no wifi credentials have been set up or no known network is available on powerup tiles will start an access point named after the host name of the esp8266 e.g. something like "ESP-5FCA28". On connection a landing page will be automatically opened giving the user information about the library and the tile as well as an option to 'configure WiFi' and upload updates(see _Updates_). Once a connection is set up the tile will automatically connect to that network on startup and no access point is started. 

If no WiFi is available and the accesspoint is started the tiles screen will display: "No WiFi. Connect to access point please.".

The access point is started for 1min only so that in case of a loss of connection the tile won't be locked. After 1min the normal working routine will be started and gifs on the tile will be displayed. (If you can't find the access point on setting a tile up try reconnecting the powersource.)

#### Updates
![image](https://github.com/DurableSteer/Tiles/assets/140595465/5adc76e7-c949-4058-88fb-a1e299cbf895)

Updates or different sketches may be uploaded to an assembled tile wirelessly through the WiFiManager library by the following process:
1. Use the verify button to compile the updated sketch in the Arduino IDE.(Make sure that the File->Preferences->"Show verbose output during 'compile'" checkbox is ticked!)
2. In the Output terminal you should see the "Creating BIN file"(see image above) message followed by a path to the compiled update file.
3. Copy the .bin file to the device you want to use to update the tile.
4. Disable the WiFi network saved to the tile or bring the tile to a place where it cannot connect to it.
5. Power the tile. "No WiFi. Connect to access point please." should be displayed.
6. Connect to the tiles access point and open the WiFiManager landing page.
7. Press the 'update' button and select the compiled sketch.bin in the file upload dialog.
8. Press 'update' and wait for the landing page to display the update successfull message.
9. Done. Your tile is now updated.

#### The FTP Server
Tiles use the SimpleFTPServer library to host a ftp server to the WiFi network. Through this server files on the tile can be managed via anonymous unprotected access by default. If you want to use login credentials you may add them as parameters to the following line in the setup function: ftpSrv.begin("[username]","[password]",wifi_station_get_hostname()); Be adviced that the tileman currently does not use login credentials and will therefore fail to find any tile modified in this way. The library has some limitations that you need to take into account if you want to use an ftp client to access the tiles. 
1. The library owner states that it only works in passive mode. I was only able to connect in active mode though and suggest doing the same.
2. The client may only use one connection per tile at a time.

#### The Display
Handling the tiles display is done via the TFT_eSPI library. Any display driver supported by that library may be used with the tiles, therefore it is necessary to provide a setup file to set the Pins used, speed of the spi connection, color order and so on to the library before compiling the sketch. I will provide setup files for the most common cheap displays available on Aliexpress. My setup file for the driver types can be found in this repo at sketch/[your driver name]/User_Setup.h . (If you have issues with your display the setup file may be a good starting point.)

#### The Gif Decoder
Gifs are decoded and drawn to the display with the AnimatedGIF library. The main loop will cycle through all files in the filesystem displaying each for about 15 seconds before loading the next file. Therefore if multiple gifs are uploaded they will be displayed as a slideshow. The Gifs names are used to transport a background color in the form: '0xFFFFFF_[gif name]' manually uploaded files or non gif files may cause errors in the background color if this naming scheme isn't used but shouldn't crash the system.

# Thanks
I wish to thank everyone mentioned in the dependencies section for their generous contribution to the diy community and their hard work in creating the librarys that allowed me to make this project possible. Stay awesome.
