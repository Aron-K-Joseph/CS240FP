import sys
import os

# --- Configuration for SimplyMiply Assembly Language ---

# Reverse mapping: Opcode (binary string) -> Mnemonic (string)
# Updated based on the assembler logic and fixes
opcodes_to_mnemonics = {
    "000000": "clr",
    "000001": "cmb",
    "000010": "mns",
    "000011": "mlt",
    "000100": "dvd",
    "000101": "cmbi",
    "000110": "ldwd",
    "000111": "srwd",
    "001000": "jmp",
    "001001": "pint",
    "001010": "pstr",
    "001011": "mnsi",
    "001100": "mlti",
    "001101": "dvdi",
    "001110": "for",
    "001111": "sqrt",
    "010000": "mdlo",
    "010001": "sqr",
    "010010": "ife",
    "010011": "ifne",
    "010100": "ldad",
    "010101": "ldim",
    "111111": "end" # Assuming all 1s is end based on assembler output
}

# Reverse mapping: Register code (binary string) -> Name (string)
registers_to_names = {format(i, '05b'): f"%r{i}" for i in range(32)}
# Add special names if needed, e.g.:
# registers_to_names["00000"] = "%zero" # Or keep as %r0

# --- Helper Functions ---

def bin_to_int(bin_str):
    """Converts a binary string to an integer."""
    if not bin_str:
        return 0
    return int(bin_str, 2)

def bin_to_signed_int(bin_str):
    """Converts a two's complement binary string to a signed integer."""
    if not bin_str:
        return 0
    value = int(bin_str, 2)
    bits = len(bin_str)
    if (value & (1 << (bits - 1))) != 0: # Check if sign bit is set
        value = value - (1 << bits)      # Compute negative value
    return value

def get_register_name(reg_bin):
    """Looks up register name, returns binary string if not found."""
    return registers_to_names.get(reg_bin, f"INVALID({reg_bin})")

# --- Disassembler Core Logic ---

def disassemble_instruction(binary_string, address):
    """
    Disassembles a single 32-bit binary instruction string.
    'address' is the line number/address of this instruction, potentially useful
    for label generation in the future.
    """
    if len(binary_string) != 32:
        return f"; Error: Invalid instruction length ({len(binary_string)} bits) at address {address}: {binary_string}"

    opcode_bin = binary_string[0:6]

    # Handle special full-width opcodes first
    if binary_string == "11111111111111111111111111111111":
        return "end"
    # clr might be all zeros except opcode - check this specifically
    if binary_string == "00000000000000000000000000000000":
         # Verify opcode just in case
         if opcode_bin == "000000":
              return "clr"
         else:
              # Fall through if it's not the 'clr' opcode but still all zeros
              pass

    if opcode_bin not in opcodes_to_mnemonics:
        return f"; Error: Unknown opcode {opcode_bin} at address {address}: {binary_string}"

    mnemonic = opcodes_to_mnemonics[opcode_bin]

    # --- Decode based on mnemonic/opcode ---

    # R-type style: cmb, mns, mlt, dvd, mdlo (Op rs rt rd Unused)
    # Format: Op(6) rs(5) rt(5) rd(5) Unused(11)
    if mnemonic in ["cmb", "mns", "mlt", "dvd", "mdlo"]:
        rs_bin = binary_string[6:11]
        rt_bin = binary_string[11:16]
        rd_bin = binary_string[16:21]
        rs_name = get_register_name(rs_bin)
        rt_name = get_register_name(rt_bin)
        rd_name = get_register_name(rd_bin)
        return f"{mnemonic} {rs_name}, {rt_name}, {rd_name}"

    # Immediate Arith: cmbi, mnsi, mlti, dvdi (Op rs Imm rd)
    # Format: Op(6) rs(5) Imm(15) rd(5)
    elif mnemonic in ["cmbi", "mnsi", "mlti", "dvdi"]:
        rs_bin = binary_string[6:11]
        imm_bin = binary_string[11:26] # 15 bits
        rd_bin = binary_string[26:31] # Next 5 bits (total 31) - Hmm, check assembler output format
        # Let's re-check assembler code for these:
        # return opcode_bin + rs + imm + rd -> 6 + 5 + 15 + 5 = 31 bits. Needs fix in assembler!
        # Assuming assembler was fixed to make rd 5 bits and something else padded:
        # Let's assume format is Op(6) rs(5) rd(5) Imm(16) like MIPS? -> 6+5+5+16 = 32 NO
        # Let's assume format is Op(6) rs(5) Imm(15) rd(5) Unused(1) -> 6+5+15+5+1 = 32 YES - let's try this
        rd_bin = binary_string[26:31]
        # If format IS Op(6) rs(5) imm(15) rd(5), the last bit (31) is unused?
        rs_name = get_register_name(rs_bin)
        rd_name = get_register_name(rd_bin)
        imm_val = bin_to_int(imm_bin) # Assuming unsigned immediate for arith
        return f"{mnemonic} {rs_name}, {imm_val}, {rd_name}"
        # !!! If the assembler *wasn't* fixed for these immediate types, this disassembler part is wrong !!!
        # !!! Based on output bin, cmbi isn't used, let's ignore this potential issue for now. !!!


    # Load Word: ldwd offset(%rs), rt
    # Format: Op(6) rs(5) rt(5) offset(16) (Based on corrected assembler)
    elif mnemonic == "ldwd":
        rs_bin = binary_string[6:11]
        rt_bin = binary_string[11:16]
        offset_bin = binary_string[16:32]
        rs_name = get_register_name(rs_bin)
        rt_name = get_register_name(rt_bin)
        offset_val = bin_to_signed_int(offset_bin) # Offsets should be signed
        return f"{mnemonic} {offset_val}({rs_name}), {rt_name}"

    # Store Word: srwd rt, offset(%rs)
    # Format: Op(6) rs(5) rt(5) offset(16) (Based on corrected assembler)
    elif mnemonic == "srwd":
        rs_bin = binary_string[6:11]  # Base register
        rt_bin = binary_string[11:16] # Source register to store
        offset_bin = binary_string[16:32]
        rs_name = get_register_name(rs_bin)
        rt_name = get_register_name(rt_bin)
        offset_val = bin_to_signed_int(offset_bin) # Offsets should be signed
        return f"{mnemonic} {rt_name}, {offset_val}({rs_name})" # Note order matches assembly syntax

    # Jump: jmp Label (or address)
    # Format: Op(6) Address(26)
    elif mnemonic == "jmp":
        address_bin = binary_string[6:32]
        target_address = bin_to_int(address_bin)
        # Basic: Output numeric address. Advanced: map address to generated label (e.g., L14)
        return f"{mnemonic} {target_address}" # Simple version for now

    # Print Int: pint %rs
    # Format: Op(6) rs(5) Unused(21)
    elif mnemonic == "pint":
        rs_bin = binary_string[6:11]
        rs_name = get_register_name(rs_bin)
        return f"{mnemonic} {rs_name}"

    # Print String: pstr offset(%rs)
    # Format: Op(6) Offset(21) rs(5)
    elif mnemonic == "pstr":
        offset_bin = binary_string[6:27] # 21 bits
        rs_bin = binary_string[27:32]    # 5 bits
        rs_name = get_register_name(rs_bin)
        offset_val = bin_to_signed_int(offset_bin) # Offset could potentially be signed
        return f"{mnemonic} {offset_val}({rs_name})"

    # For loop: for %rs, Label (or address)
    # Format: Op(6) rs(5) Address(21)
    elif mnemonic == "for":
        rs_bin = binary_string[6:11]
        address_bin = binary_string[11:32] # 21 bits
        rs_name = get_register_name(rs_bin)
        target_address = bin_to_int(address_bin)
        # Basic: Output numeric address. Advanced: map address to generated label
        return f"{mnemonic} {rs_name}, {target_address}"

    # Sqrt / Square: sqrt/sqr %rs, %rd
    # Format: Op(6) rs(5) rd(5) Unused(16)
    elif mnemonic in ["sqrt", "sqr"]:
        rs_bin = binary_string[6:11]
        rd_bin = binary_string[11:16] # Next 5 bits
        rs_name = get_register_name(rs_bin)
        rd_name = get_register_name(rd_bin)
        return f"{mnemonic} {rs_name}, {rd_name}"

    # If Equal/Not Equal: ife/ifne %rs, %rt, Label (or address)
    # Format: Op(6) rs(5) rt(5) Address(16)
    elif mnemonic in ["ife", "ifne"]:
        rs_bin = binary_string[6:11]
        rt_bin = binary_string[11:16]
        address_bin = binary_string[16:32] # 16 bits
        rs_name = get_register_name(rs_bin)
        rt_name = get_register_name(rt_bin)
        # Branch addresses are often relative PC+offset+1 or absolute.
        # Assuming absolute address based on assembler label handling.
        target_address = bin_to_int(address_bin)
        # Basic: Output numeric address. Advanced: map address to generated label
        return f"{mnemonic} {rs_name}, {rt_name}, {target_address}"

    # Load Address: ldad var(address), %rd
    # Format: Op(6) Address(21) rd(5)
    elif mnemonic == "ldad":
        address_bin = binary_string[6:27] # 21 bits
        rd_bin = binary_string[27:32]     # 5 bits
        rd_name = get_register_name(rd_bin)
        address_val = bin_to_int(address_bin) # Address is likely unsigned
        # Disassembler doesn't know the original variable name, just the address
        return f"{mnemonic} {address_val}, {rd_name}"

    # Load Immediate: ldim imm, %rd
    # Format: Op(6) Imm(21) rd(5)
    elif mnemonic == "ldim":
        imm_bin = binary_string[6:27] # 21 bits
        rd_bin = binary_string[27:32] # 5 bits
        rd_name = get_register_name(rd_bin)
        imm_val = bin_to_signed_int(imm_bin) # Immediate could be signed
        return f"{mnemonic} {imm_val}, {rd_name}"

    # --- Fallback/Error ---
    else:
        # Should not be reached if opcode is known, but good practice
        return f"; Error: Disassembly logic not implemented for opcode {opcode_bin} ({mnemonic})"


def run_disassembler(input_filename, output_filename):
    """Reads binary file, disassembles instructions, writes assembly file."""
    print(f"Disassembling {input_filename} to {output_filename}...")
    disassembled_lines = []
    try:
        with open(input_filename, "r") as infile:
            # Read all lines at once
            binary_lines = infile.readlines()

            # --- Main Disassembly Pass ---
            print("Starting Disassembly Pass...")
            for address, binary_line in enumerate(binary_lines):
                binary_line = binary_line.strip() # Remove newline characters
                if not binary_line:
                    continue # Skip empty lines

                print(f"  Disassembling line {address}: {binary_line}")
                if len(binary_line) != 32:
                     print(f"Warning: Skipping line {address} due to invalid length ({len(binary_line)} bits). Content: '{binary_line}'")
                     disassembled_lines.append(f"; Error: Invalid length at address {address}")
                     continue

                assembly_instruction = disassemble_instruction(binary_line, address)
                disassembled_lines.append(assembly_instruction)

    except FileNotFoundError:
        print(f"Error: Input file '{input_filename}' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred during disassembly: {e}")
        sys.exit(1)

    # --- Write Output ---
    try:
        with open(output_filename, "w") as outfile:
            print(f"Writing {len(disassembled_lines)} lines to {output_filename}...")
            for asm_line in disassembled_lines:
                outfile.write(asm_line + "\n")
        print("Disassembly complete.")
    except IOError as e:
        print(f"Error writing output file '{output_filename}': {e}")
        sys.exit(1)


# --- Main Execution ---
if __name__ == "__main__":
    # Basic argument handling like the MIPS example
    if len(sys.argv) != 3:
        print("Usage: python disassembler.py <input_binary_file> <output_assembly_file>")
        # Provide default filenames for easier testing
        print("Running with default filenames: program.bin -> program_disassembled.asm")
        input_file = "program.bin"     # Name of the binary file to disassemble
        output_file = "program_disassembled.asm"
        # Check if default input exists, give warning if not
        if not os.path.exists(input_file):
             print(f"Warning: Default input file '{input_file}' not found. Disassembler might produce empty output.")
             # Optional: exit if default input is required
             # sys.exit(1)
    else:
        input_file = sys.argv[1]
        output_file = sys.argv[2]

    run_disassembler(input_file, output_file)