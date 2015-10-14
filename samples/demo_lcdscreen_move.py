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
def write_diag(lcd_screen):

    yield from lcd_screen.move_to(0, 0)
    yield from lcd_screen.write_char(ord('A'))

    yield from lcd_screen.move_to(1, 1)
    yield from lcd_screen.write_char(ord('B'))

    yield from lcd_screen.move_to(2, 2)
    yield from lcd_screen.write_char(ord('C'))

    yield from lcd_screen.move_to(3, 3)
    yield from lcd_screen.write_char(ord('D'))


@asyncio.coroutine
def write_at(lcd_screen):

    yield from lcd_screen.write_at(0, 0, 'T-L')
    yield from lcd_screen.write_at(17, 0, 'T-R')
    yield from lcd_screen.write_at(0, 3, 'B-L')
    yield from lcd_screen.write_at(17, 3, 'B-R')


@asyncio.coroutine
def write_move_home(lcd_screen):

    # Write anywhere on the screen
    yield from lcd_screen.move_to(10, 2)
    yield from lcd_screen.write_char(0b01111111)
    yield from lcd_screen.move_to(11, 2)
    yield from lcd_screen.write_char(0b01111110)

    # get back to 0,0 and write again
    yield from lcd_screen.home()
    yield from lcd_screen.write_char(ord('a'))


@asyncio.coroutine
def demo(pi, address):

    yield from pi.connect(address)
    lcd_screen = LcdScreen(pi, LCD_E, LCD_RS, LCD_D4, LCD_D5, LCD_D6, LCD_D7)
    yield from lcd_screen.init()

    while True:

        yield from asyncio.sleep(1)

        yield from write_diag(lcd_screen)
        yield from asyncio.sleep(1)

        yield from lcd_screen.clear()
        yield from asyncio.sleep(1)

        yield from write_move_home(lcd_screen)
        yield from asyncio.sleep(1)

        yield from lcd_screen.clear()
        yield from asyncio.sleep(1)

        yield from write_at(lcd_screen)
        yield from asyncio.sleep(1)

        yield from lcd_screen.clear()
        yield from asyncio.sleep(1)


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
