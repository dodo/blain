
# all letters are 3x5

def space():
    return [" "*3]*5

def plus():
    return [
        "   ",
        " # ",
        "###",
        " # ",
        "   "]

def zero():
    return [
        "###",
        "# #",
        "# #",
        "# #",
        "###"]

def one():
    return [
        " # ",
        "## ",
        " # ",
        " # ",
        "###"]

def two():
    return [
        "###",
        "  #",
        "###",
        "#  ",
        "###"]

def three():
    return [
        "###",
        "  #",
        " ##",
        "  #",
        "###"]

def four():
    return [
        "# #",
        "# #",
        "###",
        "  #",
        "  #"]

def five():
    return [
        "###",
        "#  ",
        "###",
        "  #",
        "###"]

def six():
    return [
        "###",
        "#  ",
        "###",
        "# #",
        "###"]

def seven():
    return [
        "###",
        "  #",
        "  #",
        "  #",
        "  #"]

def eight():
    return [
        "###",
        "# #",
        "###",
        "# #",
        "###"]

def nine():
    return [
        "###",
        "# #",
        "###",
        "  #",
        "###"]

number = [zero,one,two,three,four,five,six,seven,eight,nine]


def get_number(n, char="#"):
    n = abs(n)
    if n > 99:
        res = zip(plus(),space())
    elif n < 10:
        res = zip(space(),number[n]())
    else:
        res = zip(number[int(n/10)](),number[n-int(n/10)*10]())
    return list(map(lambda s:s.replace("#", char), [a+b for a,b in res]))


def get_logo(n = None, dark=True):
    header = ["16 16 5 1"]
    chars = ["#","x","o","."]
    color = ["black",
        "gray25",
        "gray50",
        "white"]
    if not dark: color.reverse()
    color = ["  c None"] + [char+" c "+col for char,col in zip(chars,color)]
    background = [
        "                ",
        "      xxxx      ",
        "    xx####xx    ",
        "   x##xxxx##x   ",
        "  x#xx    xx#x  ",
        "  x#x      x#x  ",
        " x#x        x#x ",
        " x#x        x#x ",
        " x#x        x#x ",
        " x#x        x#x ",
        "  x#x      x#x  ",
        "  x#xx    xx#x  ",
        "   x##xxxx##x   ",
        "    xx####xx    ",
        "      xxxx      ",
        "                "]
    if n is None:
        foreground = [
            " o    ",
            "o.o   ",
            "o.ooo ",
            "o....o",
            "o.oo.o",
            "o....o",
            " oooo "]
    else:
        foreground = [" "*6] + get_number(n, ".") + [" "*6]

    for y, line in enumerate(foreground):
        for x, char in enumerate(line):
            if char != " ":
                s = background[y+4]
                background[y+4] = s[:x+5] + char + s[x+6:]
    return header + color + background


if __name__ == "__main__":
    print "\n".join(get_number(5))
    print
    print "\n".join(get_number(42))
    print
    print "\n".join(get_number(123))
    print
    print "\n".join(get_logo())
    print
    print "\n".join(get_logo(42,False))
