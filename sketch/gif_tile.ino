#include <AnimatedGIF.h>
#include <User_Setup.h>

#define DEFAULT_STORAGE_TYPE_ESP8266 STORAGE_LITTLEFS

#include "SPI.h"
#include <ESP8266WiFi.h>
#include <WiFiManager.h>
#include <SimpleFTPServer.h>

FtpServer ftpSrv;   //set #define FTP_DEBUG in ESP8266FtpServer.h to see ftp verbose on serial

AnimatedGIF gif;

#include <SPI.h>
#include <TFT_eSPI.h>
#include <FS.h>
#include <LittleFS.h>
TFT_eSPI tft = TFT_eSPI();

#define DISPLAY_WIDTH tft.width()
#define DISPLAY_HEIGHT tft.height()
#define BUFFER_SIZE 256  // Optimum is >= GIF width or integral division of width

Dir root = LittleFS.openDir("/");
WiFiManager wifiManager;

void setup() {
  wifiManager.setConfigPortalTimeout(60);
  wifiManager.setAPCallback(printOnConfigMode);
  tft.begin();
  wifiManager.autoConnect();
  
  if (!LittleFS.begin()) {
    Serial.println("LittleFS Mount Failed");
    return;
  }
  
  gif.begin(BIG_ENDIAN_PIXELS);
  while (WiFi.status() != WL_CONNECTED) {delay(500);}
  WiFi.hostname(WiFi.hostname()+","+DISPLAY_WIDTH+"x"+DISPLAY_HEIGHT);
  ftpSrv.begin(wifi_station_get_hostname());
  ftpSrv.setCallback(_callback);
  ftpSrv.setTransferCallback(_transferCallback);
  printInfo();
}
// GIFDraw is called by AnimatedGIF library frame to screen


uint16_t usTemp[1][BUFFER_SIZE];  // Global to support DMA use
bool dmaBuf = 0;
static int iXOff, iYOff;  // centering values
uint32_t bgcolor = 0;
File f;
void *GIFOpenFile(const char *fname, int32_t *pSize) {
  f = LittleFS.open(fname, "r");
  if (f) {
    *pSize = f.size();
    return (void *)&f;
  }
  return NULL;
} /* GIFOpenFile() */

void GIFCloseFile(void *pHandle) {
  File *f = static_cast<File *>(pHandle);
  if (f != NULL)
    f->close();
} /* GIFCloseFile() */


int32_t GIFReadFile(GIFFILE *pFile, uint8_t *pBuf, int32_t iLen) {
  int32_t iBytesRead;
  iBytesRead = iLen;
  File *f = static_cast<File *>(pFile->fHandle);
  // Note: If you read a file all the way to the last byte, seek() stops working
  if ((pFile->iSize - pFile->iPos) < iLen)
    iBytesRead = pFile->iSize - pFile->iPos - 1;  // <-- ugly work-around
  if (iBytesRead <= 0)
    return 0;
  iBytesRead = (int32_t)f->read(pBuf, iBytesRead);
  pFile->iPos = f->position();
  return iBytesRead;
} /* GIFReadFile() */

int32_t GIFSeekFile(GIFFILE *pFile, int32_t iPosition) {
  File *f = static_cast<File *>(pFile->fHandle);
  f->seek(iPosition);
  pFile->iPos = (int32_t)f->position();
  return pFile->iPos;
} /* GIFSeekFile() */

// Draw a line of image directly on the LCD
void GIFDraw(GIFDRAW *pDraw) {
  uint8_t *s;
  uint16_t *d, *usPalette;
  int x, y, iWidth, iCount;


  // Display bounds check and cropping
  iWidth = pDraw->iWidth;
  if (iWidth + pDraw->iX > DISPLAY_WIDTH)
    iWidth = DISPLAY_WIDTH - pDraw->iX;
  usPalette = pDraw->pPalette;
  y = pDraw->iY + pDraw->y;  // current line
  if (y >= DISPLAY_HEIGHT || pDraw->iX >= DISPLAY_WIDTH || iWidth < 1)
    return;

  //Old image disposal
  s = pDraw->pPixels;
  if (pDraw->ucDisposalMethod == 2)  // restore to background color
  {
    for (x = 0; x < iWidth; x++) {
      if (s[x] == pDraw->ucTransparent)
        s[x] = pDraw->ucBackground;
    }
    pDraw->ucHasTransparency = 0;
  }

  // Apply the new pixels to the main image
  if (pDraw->ucHasTransparency)  // if transparency used
  {
    uint8_t *pEnd, c, ucTransparent = pDraw->ucTransparent;
    pEnd = s + iWidth;
    x = 0;
    iCount = 0;  // count non-transparent pixels
    while (x < iWidth) {
      c = ucTransparent - 1;
      d = &usTemp[0][0];
      while (c != ucTransparent && s < pEnd && iCount < BUFFER_SIZE) {
        c = *s++;
        if (c == ucTransparent)  // done, stop
        {
          s--;  // back up to treat it like transparent
        } else  // opaque
        {
          *d++ = usPalette[c];
          iCount++;
        }
      }            // while looking for opaque pixels
      if (iCount)  // any opaque pixels?
      {
        // DMA would degrtade performance here due to short line segments
        tft.setAddrWindow(pDraw->iX + iXOff + x, iYOff + y, iCount, 1);
        tft.pushPixels(usTemp, iCount);
        yield();
        x += iCount;
        iCount = 0;
      }
      // no, look for a run of transparent pixels
      c = ucTransparent;
      while (c == ucTransparent && s < pEnd) {
        c = *s++;
        if (c == ucTransparent)
          x++;
        else
          s--;
      }
    }
  } else {
    s = pDraw->pPixels;

    // Unroll the first pass to boost DMA performance
    // Translate the 8-bit pixels through the RGB565 palette (already byte reversed)
    if (iWidth <= BUFFER_SIZE)
      for (iCount = 0; iCount < iWidth; iCount++) usTemp[dmaBuf][iCount] = usPalette[*s++];
    else
      for (iCount = 0; iCount < BUFFER_SIZE; iCount++) usTemp[dmaBuf][iCount] = usPalette[*s++];

    tft.setAddrWindow(pDraw->iX + iXOff, iYOff + y, iWidth, 1);
    tft.pushPixels(&usTemp[0][0], iCount);

    iWidth -= iCount;
    // Loop if pixel buffer smaller than width
    while (iWidth > 0) {
      // Translate the 8-bit pixels through the RGB565 palette (already byte reversed)
      if (iWidth <= BUFFER_SIZE)
        for (iCount = 0; iCount < iWidth; iCount++) usTemp[dmaBuf][iCount] = usPalette[*s++];
      else
        for (iCount = 0; iCount < BUFFER_SIZE; iCount++) usTemp[dmaBuf][iCount] = usPalette[*s++];

      tft.pushPixels(&usTemp[0][0], iCount);
      yield();
      iWidth -= iCount;
    }
  }
} /* GIFDraw() */

void printOnConfigMode(WiFiManager *myWiFiManager){
  tft.setCursor(0,DISPLAY_HEIGHT/2-50);
  tft.setTextColor(0xFFFFFF,0x000000, true);
  tft.setTextSize(3);
  tft.fillScreen(0);
  tft.println("No Wifi.");
  tft.println("Connect to\nAccesspoint\nplease.");
}

void printInfo(void){
  tft.setCursor(15,DISPLAY_HEIGHT/2-30);
  tft.setTextColor(0xFFFFFF,0x000000, true);
  tft.setTextSize(3);
  tft.fillScreen(0);
  if(WiFi.status() == WL_CONNECTED){
    tft.println(WiFi.hostname().substring(0,10));
    tft.println(WiFi.localIP());
  }
  else
    tft.println("Currently not Connected.");
}

bool receiving = false;
bool fs_changed = false;

void _callback(FtpOperation ftpOperation, unsigned int freeSpace, unsigned int totalSpace){
  switch (ftpOperation) {
    case FTP_CONNECT:
      receiving = true;
      printInfo();
      break;
    case FTP_DISCONNECT:
      receiving = false;
      break;
    default:
      break;
  }
};

void _transferCallback(FtpTransferOperation ftpOperation, const char* name, unsigned int transferredSize){
  switch (ftpOperation) {
    case FTP_UPLOAD_START:
      fs_changed = true;
      break;
    default:
      break;
  }
};

void partial_fill_screen(uint32_t color){
  //sets the background color without overwriting the drawn gif, so that on single gifs the screen doesn't flash when the gif is reloaded.
  int gifWidth = gif.getCanvasWidth();
  int gifHeight = gif.getCanvasHeight();
  int width = 240;
  int height = 280;
  int heightDiff = (height-gifHeight)/2;
  int widthDiff = (width-gifWidth)/2;


  tft.setAddrWindow(0, 0, width, heightDiff);
  tft.fillRect(0, 0, width, heightDiff, color);
  tft.setAddrWindow(0, heightDiff+gifHeight, width, heightDiff);
  tft.fillRect(0, heightDiff+gifHeight, width, heightDiff+1, color);
  tft.setAddrWindow(0, heightDiff, widthDiff, gifHeight);
  tft.fillRect(0, heightDiff, widthDiff, gifHeight, color);
  tft.setAddrWindow(widthDiff+gifWidth, heightDiff, widthDiff+1, gifHeight);//+1 in case the gif width is odd
  tft.fillRect(widthDiff+gifWidth, heightDiff, widthDiff+1, gifHeight, color);
}

char colorStr[] ="0x000000";
bool bgDrawn = false;
void loop() {
  int time = millis();
  while (root.next()) {
    bgDrawn = true;
    while ((millis() - time) < 15000) {
      if (gif.open(root.fileName().c_str(), GIFOpenFile, GIFCloseFile, GIFReadFile, GIFSeekFile, GIFDraw)) {

        tft.startWrite();  // The TFT chip select is locked low
        if(bgDrawn){
          partial_fill_screen(tft.color24to16(strtol(root.fileName().substring(0,8).c_str(), NULL, 16)));
          bgDrawn = false;
        }
        iXOff = (DISPLAY_WIDTH - gif.getCanvasWidth()) / 2;
        if (iXOff < 0) iXOff = 0;
        iYOff = (DISPLAY_HEIGHT - gif.getCanvasHeight()) / 2;
        if (iYOff < 0) iYOff = 0;

        while (gif.playFrame(true, NULL)) {
          yield();
          ftpSrv.handleFTP(); 
          while(receiving)
            ftpSrv.handleFTP(); 
          if(fs_changed){
            fs_changed = false;
            break;
          }
        }

        gif.close();
        tft.endWrite();  // Release TFT chip select for other SPI devices
      } else {
        break; 
      }
    }
      if(!LittleFS.openDir("/").next())
        printInfo();
    time = millis();
  }
  ftpSrv.handleFTP(); 
  while(receiving)
    ftpSrv.handleFTP();
  if(fs_changed)
    fs_changed = false;

  root = LittleFS.openDir("/");
  
}
