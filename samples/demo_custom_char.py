import asyncio
from apig_charlcd import LcdScreen
import apigpio as apig

# Define GPIO to LCD mapping
LCD_RS = 22
LCD_E = 27

LCD_D4 = 19
LCD_D5 = 13
LCD_D6 = 6
LCD_D7 = 5


@asyncio.coroutine
def create_custom_char(lcd_screen):

    heart = [0x0, 0x0, 0xa, 0x15, 0x11, 0xa, 0x4, 0x0]
    yield from lcd_screen.create_char(0, heart)

    arrow_up = [0x0, 0x0, 0x4, 0xe, 0x1f, 0x4, 0x4, 0x0]
    yield from lcd_screen.create_char(1, arrow_up)
    arrow_down = [0x0, 0x4, 0x4, 0x4, 0x1f, 0xe, 0x4, 0x0]
    yield from lcd_screen.create_char(2, arrow_down)

    note = [0x0, 0x3, 0x2, 0x2, 0xe, 0x1e, 0xc, 0x0]
    yield from lcd_screen.create_char(3, note)

    note2 = [0x0, 0x3, 0x12, 0xa, 0xe, 0x1e, 0xd, 0x0]
    yield from lcd_screen.create_char(4, note2)

    note3 = [0x2, 0x3, 0x2, 0x2, 0xe, 0x1e, 0xc, 0x0]
    yield from lcd_screen.create_char(5, note3)

    hp = [0x1, 0x3, 0xf, 0xf, 0xf, 0x3, 0x1, 0x0]
    yield from lcd_screen.create_char(6, hp)

    bell = [0x4, 0xe, 0xe, 0xe, 0x1f, 0x0, 0x4, 0x0]
    yield from lcd_screen.create_char(7, bell)


@asyncio.coroutine
def write_custom_char(lcd_screen):

    # Write anywhere on the screen
    yield from lcd_screen.move_to(2, 1)
    yield from lcd_screen.write_char(0x00)
    yield from lcd_screen.write_at(3, 1, " Custom ")
    yield from lcd_screen.write_char(0x00)

    yield from lcd_screen.move_to(2, 2)
    yield from lcd_screen.write_char(0x00)
    yield from lcd_screen.write_at(3, 2, " characters  ")
    yield from lcd_screen.write_char(0x00)

    yield from lcd_screen.move_to(0, 1)
    yield from lcd_screen.write_char(0x01)
    yield from lcd_screen.move_to(0, 2)
    yield from lcd_screen.write_char(ord('|'))
    yield from lcd_screen.move_to(0, 3)
    yield from lcd_screen.write_char(0x02)

    yield from lcd_screen.move_to(5, 3)
    yield from lcd_screen.write_char(0x02)
    yield from lcd_screen.write_char(0x03)
    yield from lcd_screen.write_char(0x04)
    yield from lcd_screen.write_char(0x05)
    yield from lcd_screen.write_char(0x06)
    yield from lcd_screen.write_char(0x07)


@asyncio.coroutine
def demo(pi, address):

    yield from pi.connect(address)
    lcd_screen = LcdScreen(pi, LCD_E, LCD_RS, LCD_D4, LCD_D5,
                                      LCD_D6, LCD_D7)
    yield from lcd_screen.init()

    yield from create_custom_char(lcd_screen)
    while True:

        yield from write_custom_char(lcd_screen)
        yield from asyncio.sleep(5)

        yield from lcd_screen.clear()
        yield from lcd_screen.enable(False)
        yield from asyncio.sleep(2)
        yield from lcd_screen.enable(True)


if __name__ == '__main__':

    try:
        loop = asyncio.get_event_loop()
        p = apig.Pi(loop)
        a = ('192.168.1.3', 8888)
        loop.run_until_complete(demo(p, a))
    except KeyboardInterrupt:
        pass
    finally:
        pass
