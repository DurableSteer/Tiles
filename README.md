![single_tile](https://github.com/DurableSteer/tiles/assets/140595465/330805dd-f951-40a7-80c1-63ac52a086ab) ![two_tiles](https://github.com/DurableSteer/tiles/assets/140595465/c17181ee-2853-4c1f-89c7-32e10b81e5ae)

(excuse my crappy phone camera)

# tiles
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
6. Replace the User_Setup.h in the TFT_eSPI library folder (normally saved at C:\Users\[username]\Documents\Arduino\libraries\TFT_eSPI\User_Setup.h ) with the one from this repository at  sketch/[your display driver]/User_Setup.h (if you have problems with your display you may change settings here, depending on your display changes may be necessary. You can find additional information in the file or at the wiring section of the building guide at printables.)
7. Done. Upload the sketch to your board. The display should show text and the tile should be emitting a WiFi access point with a name similiar to "ESP-5FCA28".
