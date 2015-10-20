import asyncio
import apigpio as apig


# This library can be used to drive a character LCD screen.
# The screen must use an HD44780 driver (on any other chip compatible with
# the same protocol, which virtually any lcd character screen).
# see. https://www.sparkfun.com/datasheets/LCD/HD44780.pdf


# Wiring for the LCD
# Generally from left to right, when looking at the screen with the
# connection at the top.
#
# 1 : GND
# 2 : 5V
# 3 : Contrast (0-5V)        - a potentiometer should be used here to control
#                              contrast, other connect to +3.3
# 4 : RS (Register Select)   - Any GPIO, rs arg in constructor
# 5 : R/W (Read Write)       - GND (write-only)
# 6 : Enable                 - Any GPIO, e arg in constructor
# 7 : Data Bit 0             - NOT USED
# 8 : Data Bit 1             - NOT USED
# 9 : Data Bit 2             - NOT USED
# 10: Data Bit 3             - NOT USED
# 11: Data Bit 4             - Any GPIO, d4 arg in constructor
# 12: Data Bit 5             - Any GPIO, d5 arg in constructor
# 13: Data Bit 6             - Any GPIO, d6 arg in constructor
# 14: Data Bit 7             - Any GPIO, d7 arg in constructor
# 15: LCD Backlight          - 5V or 3.3V
# 16: LCD Backlight          - GND


# LCD RAM address for the lines
# to set the cursor position, these must be added with
# _CMD_DDRAM_MASK
_LCD_LINES = [0x0, 0b1000000, 0b10100, 0b1010100]


# Styles when writting full lines
STYLE_LEFT = 1
STYLE_CENTERED = 2
STYLE_RIGHT = 3

# Timing constants:
# according to HD44780 datasheet the pulse must be at least 230ns 0.000000230
# and the data should be available during 80ns after the pulse. Of course,
# this timing is way to fast to be achieved with time.sleep, so just try
# something very small here.
E_DELAY = 1/1000000

# Modes when sending byte
_LCD_CHR = 1
_LCD_CMD = 0

# Masks for commands
_CMD_CLEAR = 0b00000001
_CMD_HOME = 0b00000010
_CMD_DDRAM_MASK = 0b10000000
_CMD_CGRAM_MASK = 0b01000000
_CMD_DISPLAY_MASK = 0b00001000

# display : enable, cursor, cursor mode
_DISPLAY_ON = 0b0100
_DISPLAY_CURSOR_ON = 0b0010
_DISPLAY_CURSOR_BLINK = 0b001


class LcdScreen(object):
    """
    LcdScreen uses the pigpiod daemon to drive a character lcd screen.
    It is meant to be used with an asyncio loop and is based on apigpio,
    an asyncio client for pigpiod.

    Most methods are coroutines and must be called using `yield from`.

    """

    def __init__(self, pi, e=None, rs=None, d4=None, d5=None, d6=None, d7=None):
        self._pi = pi

        self._d = [d4, d5, d6, d7]
        self._rs = rs
        self._e = e
        self._lock = asyncio.Lock()

        # TODO: manage 2 lines displays
        self._lines = 4
        self._rows = 20

    @asyncio.coroutine
    def init(self):
        with (yield from self._lock):
            # Only use output pins:
            for pin in (self._d + [self._e, self._rs]):
                yield from self._pi.set_mode(pin, apig.OUTPUT)

            # ATM, script is not used for pulsing e, as it seems to be less
            # stable yield from self._create_pulse_script()

            # Initialise display
            yield from self._send_byte(0x33, _LCD_CMD)  # 110011 Initialise
            yield from self._send_byte(0x32, _LCD_CMD)  # 110010 Initialise

            # Cursor move direction
            yield from self._send_byte(0x06, _LCD_CMD)  # 000110

            # Display control : Display On,Cursor Off, Blink Off
            display = _CMD_DISPLAY_MASK | _DISPLAY_ON
            yield from self._send_byte(display, _LCD_CMD)  # 001100

            # 4 bit input, 2 lines and 5x8 dots font : 0b101000
            # Even though the display has 4 lines, it is set as having 2 lines,
            # it is probably using two controllers internally and it is somehow
            # setup to make it work that way.
            yield from self._send_byte(0b101000, _LCD_CMD)

            # Start afresh.
            yield from self._clear()

    def _create_pulse_script(self):
        # create pigpio script for pulse on e
        # pigs proc w <e> 1 mics 20 w<e> 0

        script = 'w {e} 0 mics 10 w {e} 1 mics 10 w {e} 0 mics 10'.format(e=self._e)
        self._sc_id = yield from self._pi.store_script(script)
        # FIXME must delete script at end otherwise we might running out of room

    @asyncio.coroutine
    def _send_byte(self, bits, mode):
        """
        Send a byte to the display, in two 4-bits nibbles.
        This implementation uses the set/unset bank method from pigpio for better
        performance.
        :param bits:
        :param mode: command or character ( _LCD_CMD, _LCD_CHR)
        """

        # Using pigpio set_bank_1() and clear_bank_1() to set all gpio in one
        # call.
        # Another, more complex, option, would be to use a pigpio script !
        # see. http://abyz.co.uk/rpi/pigpio/pigs.html#Scripts
        # with this method, I can fill the whole screen in 0.2s on average,
        # compared to 0.3 with the naive approach.
        # 200 ms for 20*4 characters : 2.5 ms for each character

        # set_bank: a bit mask with 1 set if the corresponding gpio is to be
        # set.
        # clear_bank: a bit mask with 1 set if the corresponding gpio is to be
        # cleared.

        # Example 0x33
        # bin(0x35) : '0b110101' : 0011 0101
        # which means I must send two nibbles : 0011 0101
        # 7 : 0x35 >> 7 & 1 => 0 => written to D7
        # 6 : 0x35 >> 6 & 1 => 0 => written to D6
        # 5 : 0x35 >> 5 & 1 => 1 => written to D5
        # 4 : 0x35 >> 4 & 1 => 1 => written to D4
        # 3 : 0x35 >> 3 & 1 => 0 => written to D7
        # 2 : 0x35 >> 2 & 1 => 1 => written to D6
        # 1 : 0x35 >> 1 & 1 => 0 => written to D5
        # 0 : 0x35 >> 0 & 1 => 1 => written to D4

        # value ot the nth bit : `<bits> >> <nth> & 1`

        # Now, if the bit n must be written on gpio gn
        #   `(<bits> >> <nth> & 1 )<< <gn>`
        # And if the bit n must be cleared on gpio gn
        #   `(<bits> >> <nth> & 1 ^ 1)<< <gn>`

        # for example, to write the bit 6 of <bits> on pin 13 :
        # `<bits> >> 6 & 1 << 13`
        set_mask = 0
        unset_mask = 0

        # bit for mode :
        if mode == _LCD_CMD:
            unset_mask += 1 << self._rs
        else:
            set_mask += 1 << self._rs

        # build bit masks for high bits
        for i in range(4, 8):
            set_mask += (bits >> i & 1) << self._d[i % 4]
            unset_mask += (bits >> i & 1 ^ 1) << self._d[i % 4]

        yield from self._pi.clear_bank_1(unset_mask)
        yield from self._pi.set_bank_1(set_mask)

        # Toggle 'Enable' pin
        yield from self._toggle_enable()

        # same thing for low bits
        set_mask = 0
        unset_mask = 0
        for i in range(0, 4):
            set_mask += (bits >> i & 1) << self._d[i % 4]
            unset_mask += (bits >> i & 1 ^ 1) << self._d[i % 4]

        yield from self._pi.clear_bank_1(unset_mask)
        yield from self._pi.set_bank_1(set_mask)

        # Toggle 'Enable' pin
        yield from self._toggle_enable()

    @asyncio.coroutine
    def _toggle_enable_script(self):
        # Toggle enable
        # with the script version : 0.18s to fill the whole screen, but not very
        #  stable :(
        # with the simple version : 0.20s to fill the whole screen

        yield from self._pi.run_script(self._sc_id)
        while True:
            status = yield from self._pi.script_status(self._sc_id)
            if status == apig.PI_SCRIPT_RUNNING:
                #yield from asyncio.sleep(0.00001)
                #yield from []
                #continue
                pass
            else:
                return
        return

    def _toggle_enable(self):
        import time
        yield from self._pi.write(self._e, 0)
        end = time.time() + (E_DELAY/1000000.0)
        while time.time() < end:
            pass

        yield from self._pi.write(self._e, 1)
        end = time.time() + (E_DELAY/1000000.0)
        while time.time() < end:
            pass

        yield from self._pi.write(self._e, 0)
        end = time.time() + (E_DELAY/1000000.0)
        while time.time() < end:
            pass

    @asyncio.coroutine
    def write_line(self, message, line, style):
        """
        Write a full line of text.
        :param message: the text to display, will be truncated if too long.
        The message can be either an ascii string or an array of 2-bytes
        character codes (which are specific to the display and the ROM used
        in the display).
        :param line: the line (0, ...3)
        :param style: STYLE_xxx constant
        """

        # TODO : optimization, do not write ' ' to align when not necessary
        # might be solved when using a screen buffer
        data = []
        if isinstance(message, str):
            if style == STYLE_LEFT:
                message = message.ljust(self._rows, ' ')
            elif style == STYLE_CENTERED:
                message = message.center(self._rows, ' ')
            elif style == STYLE_RIGHT:
                message = message.rjust(self._rows, ' ')
            data = [ord(c) for c in message]
        else:
            pad = [ord(' ')] * (self._rows-len(message))
            if style == STYLE_LEFT:
                data = message + pad
            elif style == STYLE_RIGHT:
                data = pad+message
            elif style == STYLE_CENTERED:
                l = int(len(pad)/2)
                data = pad[:l] + message + pad[:l+1]

        with (yield from self._lock):
            yield from self._move_to(0, line)

            for i in range(self._rows):
                yield from self._send_byte(data[i], _LCD_CHR)

    @asyncio.coroutine
    def clear(self):
        """
        Clear the screen
        """
        with (yield from self._lock):
            yield from self._clear()

    def _clear(self):
        yield from self._send_byte(_CMD_CLEAR, _LCD_CMD)
        yield from asyncio.sleep(0.003)

    @asyncio.coroutine
    def home(self):
        with (yield from self._lock):
            yield from self._send_byte(_CMD_HOME, _LCD_CMD)
            yield from asyncio.sleep(0.003)

    @asyncio.coroutine
    def move_to(self, col, row):
        """
        Move the cursor to (col, row)
        :param col:
        :param row:
        :return:
        """
        with (yield from self._lock):
            yield from self._move_to( col, row)

    @asyncio.coroutine
    def _move_to(self, col, row):
        if row > (self._lines-1):
            row = self._lines - 2
        # Set location.
        ddram_address = _CMD_DDRAM_MASK | col + _LCD_LINES[row]
        yield from self._send_byte(ddram_address, _LCD_CMD)

    @asyncio.coroutine
    def write_char(self, char):
        """
        Write a character at the current position on the screen.

        :param char: a character code as given by ord(c)
        :return:
        """
        with (yield from self._lock):
            yield from self._send_byte(char, _LCD_CHR)

    @asyncio.coroutine
    def write_at(self, col, row, text):
        """

        :param text:
        :param col:
        :param row:
        :return:
        """
        yield from self.move_to(col, row)
        if isinstance(text, str):
            data = [ord(c) for c in text]
        else:
            data = text

        m = min(self._rows, len(data))
        with (yield from self._lock):
            yield from self._move_to(col, row)
            for i in range(m):
                yield from self._send_byte(data[i], _LCD_CHR)

    @asyncio.coroutine
    def enable(self, enabled):
        pass
        if enabled:
            display = _CMD_DISPLAY_MASK | _DISPLAY_ON
        else:
            display = _CMD_DISPLAY_MASK

        with (yield from self._lock):
            yield from self._send_byte(display, _LCD_CMD)

    @asyncio.coroutine
    def create_char(self, location, pattern):
        """
        Fill one of the first 8 CGRAM locations with custom characters.
        The location parameter should be between 0 and 7 and pattern should
        provide an array of 8 bytes containing the pattern.

        See http://www.quinapalus.com/hd44780udg.html to design your own
        character.

        To show your custom character use eg. lcd.message('\x01')
        """
        # only position 0..7 are allowed
        location &= 0x7
        with (yield from self._lock):
            yield from self._send_byte(_CMD_CGRAM_MASK | (location << 3), _LCD_CMD)
            for i in range(8):
                yield from self._send_byte(pattern[i], _LCD_CHR)
