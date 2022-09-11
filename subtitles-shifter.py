import argparse
import pathlib
import sys
from collections import namedtuple


class Timestamp:

    def __init__(self, h, m, s, ms):
        self.h = h
        self.m = m
        self.s = s
        self.ms = ms

    @staticmethod
    def from_str(encoded):
        h, m, s, ms = encoded[:2], encoded[3:5], encoded[6:8], encoded[9:]
        h, m, s, ms = int(h), int(m), int(s), int(ms)
        return Timestamp(h, m, s, ms)

    def to_str(self):
        h, m, s, ms = str(self.h), str(self.m), str(self.s), str(self.ms)
        h, m, s, ms = h.rjust(2, '0'), m.rjust(2, '0'), s.rjust(2, '0'), ms.rjust(3, '0')
        return f"{h}:{m}:{s},{ms}"

    def shift(self, h, m, s, ms):
        self.h += h
        self.m += m
        self.s += s
        self.ms += ms
        if self.ms >= 1000:
            self.s += 1
            self.ms -= 1000
        elif self.ms < 0:
            self.s -= 1
            self.ms += 1000
        if self.s >= 60:
            self.m += 1
            self.s -= 60
        elif self.s < 0:
            self.m -= 1
            self.s += 60
        if self.m >= 60:
            self.h += 1
            self.m -= 60
        elif self.m < 0:
            self.h -= 1
            self.m += 60
        if self.h < 0:
            print("Warning: too big shift!")
            self.h = 0
            self.m = 0
            self.s = 0
            self.ms = 0


class Subtitle:

    def __init__(self, ix: int, start: Timestamp, end: Timestamp, text: str):
        self.ix = ix
        self.start, self.end = start, end
        self.text = text

    @staticmethod
    def from_str(encoded):
        ix, time, text = encoded.split('\n', maxsplit=2)
        start, end = time.split(" --> ")
        start, end = Timestamp.from_str(start), Timestamp.from_str(end)
        return Subtitle(int(ix), start, end, text)

    def to_str(self):
        return f"{self.ix}\n" \
               f"{self.start.to_str()} --> {self.end.to_str()}\n" \
               f"{self.text}"

    def shift(self, h, m, s, ms):
        self.start.shift(h, m, s, ms)
        self.end.shift(h, m, s, ms)

    def __str__(self):
        return self.to_str()


def get_source(source):
    if source is None:
        return get_source_from_stdin()
    return get_source_from_file(source)


def get_source_from_stdin():
    sys.stdin.reconfigure(encoding="utf-8-sig")
    result = sys.stdin.read().replace('\r', '')
    sys.stdin.reconfigure(encoding="utf-8")
    return result


def get_source_from_file(file_name):
    with open(file_name, encoding="utf-8-sig") as f:
        return f.read()


def read_srt(source: str) -> list[Subtitle]:
    parts = [p.strip() for p in source.strip().split("\n\n")]
    return [Subtitle.from_str(p) for p in parts]


def dump_srt(srt: list[Subtitle]):
    return "\n\n".join([s.to_str() for s in srt]) + "\n\n"


def write_to_dest(result, dest):
    if dest is None:
        write_to_stdin(result)
    else:
        write_to_file(result, dest)


def write_to_stdin(result):
    sys.stdout.reconfigure(encoding="utf-8-sig")
    sys.stdout.write(result)
    sys.stdout.reconfigure(encoding="utf-8")


def write_to_file(result, file_name):
    with open(file_name, 'w', encoding="utf-8-sig") as f:
        f.write(result)



def parse_arguments(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=pathlib.Path, nargs='?')
    parser.add_argument("dest", type=pathlib.Path, nargs='?')
    parser.add_argument("-hours", type=int, nargs='?', default=0)
    parser.add_argument("-m", type=int, nargs='?', default=0)
    parser.add_argument("-s", type=int, nargs='?', default=0)
    parser.add_argument("-ms", type=int, nargs='?', default=0)
    args = parser.parse_args(argv[1:])
    shift = {"h": args.hours, "m": args.m, "s": args.s, "ms": args.ms}
    return args.source, args.dest, shift


def main(argv):
    source, dest, shift = parse_arguments(argv)
    if not (-1000 < shift["ms"] < 1000 \
            and -60 < shift["s"] < 60 \
            and -60 < shift["m"] < 60):
        print("Too big shift, please use convinient measures")
        return
    srt = read_srt(get_source(source))
    for subtitle in srt:
        subtitle.shift(**shift)
    write_to_dest(dump_srt(srt), dest)


if __name__ == "__main__":
    main(sys.argv)

