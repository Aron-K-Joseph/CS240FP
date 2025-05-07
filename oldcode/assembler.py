import sys
import os


op_codes = {
    "add": "000000",
    "sub": "000000",
    "and:": "000000",
    "or:": "000000",
    "slt": "000000",
    "lw": "100011",
    "sw": "101011",
    "beq": "000100",
    "bne": "000100",
}
func_codes = {
    "add": "100000",
    "sub": "100010",
    "and:": "100100",
    "or:": "100101",
    "slt": "101010",
}
registers = {
    "$zero": "00000",
    "$t1": "01001",
    "$t2": "01010",
    "$t3": "01011",
    "$t4": "01100",
    "$t5": "01101",
    "$t6": "01110",
    "$t7": "01111",
    "$s0": "10000",
    "$s1": "10001",
    "$s2": "10010",
    "$s3": "10011",
    "$s4": "10100",
    "$s5": "10101",
    "$s6": "10110",
    "$s7": "10111",
}
shift_logic_amount = "00000"


def interpret_line(mips_file: str):
    input_file = open(mips_file, "r")
    output_file = open("program1.bin", "w")
    for instruction in input_file:
        bin = assemble(instruction)
        output_file.write(bin)


def assemble(line):
    line = line.split("#")[0].strip()

    if not line:
        return

    parts = line.split(" ")
    op_code = parts[0]

    if op_code in func_codes:
        rd, rs, rt = (
            parts[1].replace(",", ""),
            parts[2].replace(",", ""),
            parts[3].replace(",", ""),
        )
        return (
            op_codes[op_code]
            + registers[rs]
            + registers[rt]
            + registers[rd]
            + shift_logic_amount
            + func_codes[op_code]
        )
    if op_code in ["lw", "sw", "beq"]:
        if op_code == "lw" or op_code == "sw":
            rt = parts[1].replace(",", "")
            offset, rs = parts[2].replace(")", "").split("(")
            offset_bin = bin(int(offset)).replace("0b", "").zfill(16)
            return op_codes[op_code] + registers[rs] + registers[rt] + offset_bin
        else:
            rs, rt, offset = (
                parts[1].replace(",", ""),
                parts[2].replace(",", ""),
                parts[3].replace(",", ""),
            )
            offset_bin = bin(int(offset)).replace("0b", "").zfill(16)
            return op_codes[op_code] + registers[rs] + registers[rt] + offset_bin


if __name__ == "__main__":
    # mips_file = sys.argv[1]
    mips_file = "program1.mips"
    interpret_line(mips_file)
