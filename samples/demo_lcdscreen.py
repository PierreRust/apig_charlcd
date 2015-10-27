import asyncio
import apig_charlcd
import apigpio as apig

# Define GPIO to LCD mapping
LCD_RS = 22
LCD_E = 27

LCD_D4 = 19
LCD_D5 = 13
LCD_D6 = 6
LCD_D7 = 5


@asyncio.coroutine
def fill_screen(lcd_screen):
    import time

    # line = '01234567890123456789ABC'

    # This will produce a left and right arrow on a device with A00 Rom code,
    # that is a japan alphabet device. Unfortunately, my display is A00..
    line = [0b01111110,
            0b01111111,
            0b11111100
            ]
    # This should produce up and dow arrows with a A02 rom code.
    # line = [0b00010000,
    #         0b00010001,
    #         0b00010100,
    #         0b00010101]
    s = 0
    for i in range(100):
        before = time.time()
        style = (i % 3) + 1
        yield from lcd_screen.write_line(line, 0, style)
        yield from lcd_screen.write_line(line, 1, style)
        yield from lcd_screen.write_line(line, 2, style)
        yield from lcd_screen.write_line(line, 3, style)
        after = time.time()
        t = after-before
        print('Filling screen in {} '.format(t))
        s += t
        yield from lcd_screen.clear()

    avg = s / 100
    print('Average filling screen in {} '.format(avg))


@asyncio.coroutine
def simulate_list_scroll(lcd_screen):

    items = ['Media Library', 'Radio', 'Bluetooth audio', 'Airplay', 'UPnP',
             'Pulse audio sink', 'Deezer', 'Spotify']
    m = len(items)

    # simulate list scrolling
    for i in range(80):
        yield from lcd_screen.write_line(items[i % m], 1,
                                         apig_charlcd.STYLE_LEFT)
        yield from lcd_screen.write_line(items[(i+1) % m], 2,
                                         apig_charlcd.STYLE_LEFT)
        yield from lcd_screen.write_line(items[(i+2) % m], 3,
                                         apig_charlcd.STYLE_LEFT)
        yield from asyncio.sleep(0.5)


@asyncio.coroutine
def demo(pi, address):

    yield from pi.connect(address)
    lcd_screen = apig_charlcd.LcdScreen(pi, LCD_E, LCD_RS, LCD_D4, LCD_D5,
                                        LCD_D6, LCD_D7)
    yield from lcd_screen.init()

    while True:

        #yield from fill_screen(lcd_screen)

        #yield from simulate_list_scroll(lcd_screen)

        yield from lcd_screen.write_line("<------------------>", 0,
                                         apig_charlcd.STYLE_CENTERED)
        yield from lcd_screen.write_line("Rasbperry Pi", 1,
                                         apig_charlcd.STYLE_CENTERED)
        yield from lcd_screen.write_line(" (tested with v2)", 2,
                                         apig_charlcd.STYLE_CENTERED)
        yield from lcd_screen.write_line("<------------------>", 3,
                                         apig_charlcd.STYLE_CENTERED)

        yield from asyncio.sleep(3)

        yield from lcd_screen.write_line("LDC Screen ", 0,
                                         apig_charlcd.STYLE_RIGHT)
        yield from lcd_screen.write_line("with asyncio", 1,
                                         apig_charlcd.STYLE_RIGHT)
        yield from lcd_screen.write_line("and pigpio", 2,
                                         apig_charlcd.STYLE_RIGHT)
        yield from lcd_screen.write_line("20x4 LCD screen", 3,
                                         apig_charlcd.STYLE_RIGHT)

        yield from asyncio.sleep(3)

        yield from lcd_screen.clear()
        yield from asyncio.sleep(3)


if __name__ == '__main__':

    pi = None
    loop = asyncio.get_event_loop()
    try:
        pi = apig.Pi(loop)
        address = ('192.168.1.12', 8888)
        loop.run_until_complete(demo(pi, address))
    except KeyboardInterrupt:
        pass
    finally:
        if pi is not None:
            loop.run_until_complete(pi.stop())
