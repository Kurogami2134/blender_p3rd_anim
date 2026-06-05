from struct import pack, unpack
from genericpath import exists
from os import mkdir
from os.path import dirname, basename, join as joinpath, isdir
from sys import argv

def extract_anim(path: str) -> None:
    if isdir(path):
        print("Not a dir.")
        return
    work_dir = joinpath(dirname(path), basename(path).split(".")[0])
    if not exists(work_dir):
        mkdir(work_dir)
    with open(path, "rb") as file, open(joinpath(work_dir, "Info.txt"), "w", encoding="utf-8") as info:
        Header = unpack("8i", file.read(0x20))
        info.write(f'Header: {", ".join([str(x) for x in Header])}\n')

        count = int(Header[-1] / 4) - 9
        for offset_idx in range(count):
            file.seek(0x24 + offset_idx * 4)
            offset = unpack("i", file.read(4))[0]
            if offset != -1:
                file.seek(offset + 4)
                size = unpack("i", file.read(4))[0]
                file.seek(offset)

                with open(joinpath(work_dir, f'Anim_{offset_idx:0>3}.p3a'), "wb") as anim_file:
                    anim_file.write(file.read(size))

def rebuild_anim(path: str) -> None:
    if not isdir(path):
        print("Not a file.")
        return
    with open(path + ".anim", "wb") as out, open(joinpath(path, "Info.txt"), "r", encoding="utf-8") as info:
        Header = list(map(int, info.readline().split(": ")[1].split(", ")))
        out.write(pack("9i", *Header, -1))
        
        count = int(Header[-1] / 4) - 9
        offset = Header[-1]
        for idx in range(count):
            out.seek(idx * 4 + 0x24)
            if exists(joinpath(path, f'Anim_{idx:0>3}.p3a')):
                out.write(pack("i", offset))
                out.seek(offset)
                with open(joinpath(path, f'Anim_{idx:0>3}.p3a'), "rb") as anim_file:
                    offset += out.write(anim_file.read())
            else:
                out.write(b'\xFF\xFF\xFF\xFF')
        
        out.seek(offset)
        out.truncate()


if __name__ == "__main__":
    while argv and "py" == argv[0][-2:]:
        argv.pop(0)
    if len(argv) >= 2 and argv[0] == "-r":
        rebuild_anim(argv[1])
    elif len(argv) >= 2 and  argv[0] == "-e":
        extract_anim(argv[1])
    else:
        print("Invalid option. Use: py <option> <path>\n\t-r\tRebuild animation file.\n\t-e\tExtract animations from file.")
