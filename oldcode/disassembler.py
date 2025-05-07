import sys


op_codes = {
    "000000": "add",
    "000000": "sub",
    "000000": "and",
    "000000": "or",
    "000000": "slt",
    "100011": "lw",
    "101011": "sw",
    "000100": "beq",
    "000101": "bne",
}
func_codes = {
    "100000": "add",
    "100010": "sub",
    "100100": "and",
    "100101": "or",
    "101010": "slt",
}
registers = {
    "00000": "$zero",
    "01001": "$t1",
    "01010": "$t2",
    "01011": "$t3",
    "01100": "$t4",
    "01101": "$t5",
    "01110": "$t6",
    "01111": "$t7",
    "10000": "$s0",
    "10001": "$s1",
    "10010": "$s2",
    "10011": "$s3",
    "10100": "$s4",
    "10101": "$s5",
    "10110": "$s6",
    "10111": "$s7",
}


def handle_lines(bin_file: str):
    input_file = open(bin_file, "r")
    line = input_file.readlines()[0].strip()
    mips_instructions = bin_to_mips(line)
    output_file = open("BACK_TO_MIPS.txt", "w")
    for instruction in mips_instructions:
        output_file.write(instruction)
        output_file.write("\n")


def bin_to_mips(line):
    mips = []
    bit_string = ""
    for i in range(0, len(line)):
        bit_string += line[i]
        if len(bit_string) == 32:
            op_code = bit_string[0:6]
            print(op_code)
            if op_code == "000000":
                rs, rt, rd, shift, func_code = (
                    bit_string[6:11],
                    bit_string[11:16],
                    bit_string[16:21],
                    bit_string[21:26],
                    bit_string[26:32],
                )
                mips.append(
                    f"{func_codes[func_code]} {registers[rd]}, {registers[rs]}, {registers[rt]}"
                )
            elif op_code in ["100011", "101011"]:
                rs, rt, offset = bit_string[6:11], bit_string[11:16], bit_string[16:32]
                mips.append(
                    f"{op_codes[op_code]} {registers[rt]}, {int(offset, 2)}({registers[rs]})"
                )
            else:
                rs, rt, offset = bit_string[6:11], bit_string[11:16], bit_string[16:32]
                mips.append(
                    f"{op_codes[op_code]} {registers[rs]}, {registers[rt]}, {int(offset, 2)}"
                )

            bit_string = ""
    return mips


if __name__ == "__main__":
    handle_lines(sys.argv[1])
