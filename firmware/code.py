import time
import board
import busio
import digitalio

# -----------------------------
# MAX7219 Pin Configuration
# -----------------------------

spi = busio.SPI(
    clock=board.D1,  # CLK
    MOSI=board.D0  # DIN
)

load = digitalio.DigitalInOut(board.D2)  # LOAD
load.direction = digitalio.Direction.OUTPUT
load.value = True


# -----------------------------
# MAX7219 Communication
# -----------------------------

def write_register(address: int, data: int):
    """
    Write a byte of data to a specific register address on the MAX7219.
    :param address: The register address to write to. (4 bits)
    :param data: The data to write to the register. (8 bits)
    :return: None
    """
    while not spi.try_lock():
        pass

    try:
        spi.configure(
            baudrate=1000000,
            polarity=0,
            phase=0
        )

        load.value = False
        spi.write(bytes([address, data]))
        load.value = True

    finally:
        spi.unlock()


# -----------------------------
# MAX7219 Register Addresses
# -----------------------------

DECODE_MODE = 0x09
INTENSITY = 0x0A
SCAN_LIMIT = 0x0B
SHUTDOWN = 0x0C
DISPLAY_TEST = 0x0F


# -----------------------------
# MAX7219 Initialization
# -----------------------------

def initialize_max7219():
    # Disable display while configuring
    write_register(SHUTDOWN, 0x00)

    # No display test mode
    write_register(DISPLAY_TEST, 0x00)

    # Decode mode: no BCD decoding
    write_register(DECODE_MODE, 0x00)

    # Scan all 8 digits
    write_register(SCAN_LIMIT, 0x07)

    # Medium brightness (0-15)
    write_register(INTENSITY, 0x08)

    # Clear all digits
    for digit in range(1, 9):
        write_register(digit, 0x00)

    # Enable display
    write_register(SHUTDOWN, 0x01)


# -----------------------------
# Segment Mapping for Characters
# -----------------------------

SEGMENTS_BY_CHAR = {
    '0': 0b01111110, '1': 0b00110000, '2': 0b01101101, '3': 0b01111001,
    '4': 0b00110011, '5': 0b01011011, '6': 0b01011111, '7': 0b01110000,
    '8': 0b01111111, '9': 0b01111011,
    'A': 0b01110111, 'B': 0b00011111, 'C': 0b01001110, 'D': 0b00111101,
    'E': 0b01001111, 'F': 0b01000111, 'G': 0b01011110, 'H': 0b00110111,
    'I': 0b00110000, 'J': 0b00111100,
    # No 'K'
    'L': 0b00001110,
    # No 'M'
    'N': 0b01110110, 'O': 0b01111110, 'P': 0b01100111, 'Q': 0b01110011,
    'R': 0b00000101, 'S': 0b01011011, 'T': 0b00001111, 'U': 0b00111110,
    # No 'V', 'W', 'X'
    'Y': 0b00111011, 'Z': 0b01101101
}


# -----------------------------
# MAX7219 Display Functions
# -----------------------------

def clear_digit(digit: int):
    if 1 <= digit <= 8:
        write_register(digit, 0x00)


def clear_display():
    for digit in range(1, 9):
        clear_digit(digit)


def set_digit_segments(digit: int, data: int):
    """
    Set a specific digit to display a custom segment pattern.
    :param digit: The digit position (1-8).
    :param data: The segment data (8 bits).
    :return: None
    """
    if not (1 <= digit <= 8):
        raise ValueError("Digit must be between 1 and 8")
    write_register(digit, data)


def set_digit_char(digit: int, char: str):
    """
    Set a specific digit to display a character.
    :param digit: The digit position (1-8).
    :param char: The character to display (0-9, A-F).
    :return: None
    """
    if not (1 <= digit <= 8):
        raise ValueError("Digit must be between 1 and 8")
    data = SEGMENTS_BY_CHAR.get(char.upper(), 0x00)  # Default to blank if char not found
    write_register(digit, data)


# -----------------------------
# Display Helper Functions
# -----------------------------

def show_text(text: str):
    """
    Display text on the 8-digit display. If the text is longer than 8 characters, it will be truncated.
    :param text: The text to display (up to 8 characters).
    :return: None
    """
    for i in range(1, 9):
        if i <= len(text):
            set_digit_char(i, text[i - 1])
        else:
            clear_digit(i)

def slide_text(
        text: str,
        delay: float = 0.5,
        slide_in: bool = True,
        slide_out: bool = True
):
    """
    Slide text across the display.
    :param text: The text to slide (can be more than 8 characters).
    :param delay: Delay between updates in seconds.
    :param slide_in: Whether to slide in from the right.
    :param slide_out: Whether to slide out to the left.
    :return: None
    """
    # Prepare the text to slide
    padded_text = " " * 8 + text + " " * 8
    length = len(padded_text)

    # Slide in
    if slide_in:
        for i in range(length - 7):
            for digit in range(1, 9):
                char_index = i + digit - 1
                if char_index < length:
                    set_digit_char(digit, padded_text[char_index])
                else:
                    clear_digit(digit)
            time.sleep(delay)

    # Slide out
    if slide_out:
        for i in range(length - 7, -1, -1):
            for digit in range(1, 9):
                char_index = i + digit - 1
                if char_index < length:
                    set_digit_char(digit, padded_text[char_index])
                else:
                    clear_digit(digit)
            time.sleep(delay)

# -----------------------------
# Example Usage
# -----------------------------

def main():
    initialize_max7219()

    show_text("Hello")
    time.sleep(5)
    slide_text("Hello world", delay=0.5)

if __name__ == "__main__":
    main()
