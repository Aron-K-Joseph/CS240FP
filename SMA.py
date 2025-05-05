import sys
import os
import re # For parsing memory addresses like offset(%register)

# --- Configuration for SimplyMiply Assembly Language ---

# Map instruction mnemonics to their 6-bit opcode
opcodes = {
    "clr":    "000000",
    "cmb":    "000001",  # Add the opcode for the 'cmb' instruction
    "mns":    "000010",
    "mlt":    "000011",
    "dvd":    "000100",
    "cmbi":   "000101",
    "ldwd":   "000110",
    "srwd":   "000111",
    "jmp":    "001000",
    "pint":   "001001",
    "pstr":   "001010",
    "mnsi":   "001011",
    "mlti":   "001100",
    "dvdi":   "001101",
    "for":    "001110",
    "sqrt":   "001111",
    "mdlo":   "010000",
    "sqr":    "010001",
    "ife":    "010010",
    "ifne":   "010011",
    "ldad":   "010100",
    "ldim":   "010101",
    "end":    "111111" # Special case, but good to have here
}

# Define register names and their 5-bit binary representation
# Assuming 32 registers like MIPS (%r0 to %r31)
registers = {f"%r{i}": format(i, '05b') for i in range(32)}
# Add a special case for %zero maybe, if needed? Assuming %r0 is the zero register.
# registers["%zero"] = "00000" # Uncomment if you use %zero explicitly

# --- Helper Functions ---

def parse_register(reg_str):
    """Converts register string like '%r5' to its 5-bit binary representation."""
    reg_str = reg_str.replace(',', '') # Remove trailing comma if present
    if reg_str in registers:
        return registers[reg_str]
    else:
        raise ValueError(f"Invalid register name: {reg_str}")

def parse_immediate(imm_str, bits):
    """Converts an immediate value string to its binary representation, padded to 'bits' length."""
    imm_str = imm_str.replace(',', '') # Remove trailing comma
    try:
        value = int(imm_str)
        # Basic range check (assuming unsigned or two's complement fits)
        min_val = -(2**(bits-1)) if bits > 0 else 0 # Rough lower bound for signed
        max_val = (2**bits) - 1 if bits > 0 else 0 # Upper bound for unsigned
        # More precise checks might be needed depending on signed/unsigned interpretation
        # For simplicity, let's assume non-negative for now based on example '15'
        if value < 0: # Allow negative for potential future use, but example is positive
             # Handle two's complement if needed
             if value < min_val:
                 raise ValueError(f"Immediate value {value} too small for {bits} bits.")
             # Convert negative to two's complement binary string of 'bits' length
             return format(value & ((1 << bits) - 1), f'0{bits}b')

        if value > max_val:
             raise ValueError(f"Immediate value {value} too large for {bits} bits.")
        # Convert positive to binary string
        return format(value, f'0{bits}b')

    except ValueError as e:
        raise ValueError(f"Invalid immediate value: {imm_str}. {e}")


def parse_memory_address(mem_str):
    """Parses memory address string like 'offset(%reg)' into offset and register string."""
    mem_str = mem_str.replace(',', '') # Remove trailing comma
    match = re.match(r"(-?\d+)\((%r\d+)\)", mem_str) # Allow negative offset
    if match:
        offset = int(match.group(1))
        reg = match.group(2)
        return offset, reg
    else:
        # Handle case like 'var' for ldad? No, ldad is handled separately.
        # Handle case where offset might be zero and omitted? e.g., (%r0)
        match_no_offset = re.match(r"\((%r\d+)\)", mem_str)
        if match_no_offset:
            return 0, match_no_offset.group(1)
        raise ValueError(f"Invalid memory address format: {mem_str}")

# --- Assembler Core Logic ---

def assemble_line(line, label_table, current_address):
    """Assembles a single line of assembly code into binary."""
    parts = line.split(maxsplit=1) # Split only the mnemonic from the rest
    op = parts[0].lower() # Use lower case for consistency

    if not op:
        return None # Skip empty lines

    if op == "clr":
        return "000000" + "0" * 26 # Opcode + 26 zeros

    if op == "end":
        return "1" * 32 # Special end instruction

    if op not in opcodes:
        raise ValueError(f"Unknown instruction: {op}")

    opcode_bin = opcodes[op]
    operands_str = parts[1] if len(parts) > 1 else ""
    operands = [p.strip() for p in operands_str.split(',')] # Split remaining operands by comma


    # --- Instruction Format Handling ---

    # R-type style: cmb, mns, mlt, dvd, mdlo (op rs rt rd unused)
    if op in ["cmb", "mns", "mlt", "dvd", "mdlo"]:
        if len(operands) != 3:
            raise ValueError(f"Instruction '{op}' requires 3 register operands. Got: {operands_str}")
        rs = parse_register(operands[0])
        rt = parse_register(operands[1])
        rd = parse_register(operands[2])
        unused = "0" * 11
        return opcode_bin + rs + rt + rd + unused

    # Immediate Arith: cmbi, mnsi, mlti, dvdi (op rs imm rd)
    elif op in ["cmbi", "mnsi", "mlti", "dvdi"]:
        if len(operands) != 3:
            raise ValueError(f"Instruction '{op}' requires register, immediate, register. Got: {operands_str}")
        rs = parse_register(operands[0])
        imm = parse_immediate(operands[1], 15) # 15 bits for immediate
        rd = parse_register(operands[2])
        return opcode_bin + rs + imm + rd

    # Load Word: ldwd offset(%rs), rt (op imm rs rt) -> Matches example binary breakdown
    # Example: 000110 000000000000000 00000 00001 => op | offset(17) | rs(5) | rt(5)  <-- REVISED based on example binary
    elif op == "ldwd":
         if len(operands) != 2:
            raise ValueError(f"Instruction '{op}' requires 'offset(%rs), rt'. Got: {operands_str}")
         offset_val, rs_str = parse_memory_address(operands[0])
         rt = parse_register(operands[1])
         rs = parse_register(rs_str)
         offset_bin = parse_immediate(str(offset_val), 16) # 17 bits for offset
         return opcode_bin + rs + rt + offset_bin # Rearranged to match example binary 000110 offset(17) rs(5) rt(5)

    # Store Word: srwd rt, offset(%rs) (op imm rs rt) -> Matches example binary breakdown
    # Example: 000111 00000 000000000000000 00001 => op | rt(5) | offset(17) | rs(5) <-- REVISED based on example binary
    elif op == "srwd":
        if len(operands) != 2:
           raise ValueError(f"Instruction '{op}' requires 'rt, offset(%rs)'. Got: {operands_str}")
        rt = parse_register(operands[0])
        offset_val, rs_str = parse_memory_address(operands[1])
        rs = parse_register(rs_str)
        offset_bin = parse_immediate(str(offset_val), 16) # 17 bits for offset
        # Note: The example binary 000111 00000 000000000000000 00001 suggests: op | rs | offset | rt
        # Let's stick to the example binary layout: op(6) rs(5) offset(17) rt(5)
        # Example: 000111 00000 000000000000000 00001 - %r0, 0(%r1) => op=%srwd rs=%r0 offset=0 rt=%r1
        return opcode_bin + rs + rt + offset_bin # Matches example binary structure 000111 rt(5) offset(17) rs(5)


    # Jump: jmp Label (op address)
    elif op == "jmp":
        if len(operands) != 1:
            raise ValueError(f"Instruction '{op}' requires 1 label operand. Got: {operands_str}")
        label = operands[0]
        if label not in label_table:
            raise ValueError(f"Undefined label: {label}")
        address = label_table[label]
        address_bin = format(address, f'0{26}b') # 26 bits for address/offset
        return opcode_bin + address_bin

    # Print Int: pint %rs (op rs unused)
    elif op == "pint":
        if len(operands) != 1:
            raise ValueError(f"Instruction '{op}' requires 1 register operand. Got: {operands_str}")
        rs = parse_register(operands[0])
        unused = "0" * 21
        return opcode_bin + rs + unused

    # Print String: pstr offset(%rs) (op offset rs) -> Matches example binary
    # Example: 001010 00000000000000000000 00000 => op | offset(21) | rs(5)
    elif op == "pstr":
        if len(operands) != 1:
           raise ValueError(f"Instruction '{op}' requires 'offset(%rs)'. Got: {operands_str}")
        offset_val, rs_str = parse_memory_address(operands[0])
        rs = parse_register(rs_str)
        offset_bin = parse_immediate(str(offset_val), 21) # 21 bits for offset
        return opcode_bin + offset_bin + rs

    # For loop: for %rs, Label (op rs address)
    elif op == "for":
        if len(operands) != 2:
           raise ValueError(f"Instruction '{op}' requires register, label. Got: {operands_str}")
        rs = parse_register(operands[0])
        label = operands[1]
        if label not in label_table:
           raise ValueError(f"Undefined label: {label}")
        address = label_table[label]
        address_bin = format(address, f'0{21}b') # 21 bits for address/offset
        return opcode_bin + rs + address_bin

    # Sqrt: sqrt %rs, %rd (op rs rd unused)
    elif op == "sqrt":
        if len(operands) != 2:
            raise ValueError(f"Instruction '{op}' requires 2 register operands. Got: {operands_str}")
        rs = parse_register(operands[0])
        rd = parse_register(operands[1])
        unused = "0" * 16
        return opcode_bin + rs + rd + unused

    # Square: sqr %rs, %rd (op rs rd unused)
    elif op == "sqr":
        if len(operands) != 2:
            raise ValueError(f"Instruction '{op}' requires 2 register operands. Got: {operands_str}")
        rs = parse_register(operands[0])
        rd = parse_register(operands[1])
        unused = "0" * 16
        return opcode_bin + rs + rd + unused

    # If Equal/Not Equal: ife/ifne %rs, %rt, Label (op rs rt address)
    elif op in ["ife", "ifne"]:
        if len(operands) != 3:
            raise ValueError(f"Instruction '{op}' requires 2 registers and a label. Got: {operands_str}")
        rs = parse_register(operands[0])
        rt = parse_register(operands[1])
        label = operands[2]
        if label not in label_table:
            raise ValueError(f"Undefined label: {label}")
        address = label_table[label]
        address_bin = format(address, f'0{16}b') # Only 16 bits left based on example: 6+5+5 = 16. 32-16 = 16.
                                                 # Let's re-check example: 010010 00000 00001 000000000000000
                                                 # Op(6) rs(5) rt(5) addr(16) - Yes, 16 bits.
        return opcode_bin + rs + rt + address_bin

    # Load Address: ldad var, %rd (op address rd) -> Matches example
    # Example: 010100 00000000000000000000 00000 => op | address(21) | rd(5)
    elif op == "ldad":
        if len(operands) != 2:
           raise ValueError(f"Instruction '{op}' requires label/var, register. Got: {operands_str}")
        label = operands[0] # Should be a label defined elsewhere (e.g., in a .data section conceptually)
        rd = parse_register(operands[1])
        # How is 'var' resolved? Assuming it's a label like jump targets.
        if label not in label_table:
            # This might indicate a variable in a data segment, not a code label.
            # For now, we treat it like a code label. Needs clarification on how 'var' addresses are determined.
            # Let's assume it must be a known label for this assembler.
            raise ValueError(f"Undefined label/variable for ldad: {label}")
        address = label_table[label]
        address_bin = format(address, f'0{21}b') # 21 bits for address
        return opcode_bin + address_bin + rd

    # Load Immediate: ldim imm, %rd (op imm rd) -> Matches example
    # Example: 010101 00000000000000000000 00000 => op | imm(21) | rd(5)
    elif op == "ldim":
        if len(operands) != 2:
           raise ValueError(f"Instruction '{op}' requires immediate, register. Got: {operands_str}")
        imm = parse_immediate(operands[0], 21) # 21 bits for immediate
        rd = parse_register(operands[1])
        return opcode_bin + imm + rd

    # --- Fallback/Error ---
    else:
        # This case should ideally not be reached if all opcodes are handled above
        raise NotImplementedError(f"Assembly rule for instruction '{op}' not implemented.")

def run_assembler(input_filename, output_filename):
    """Runs the two-pass assembler."""
    print(f"Assembling {input_filename} to {output_filename}...")
    label_table = {}
    cleaned_lines = []
    current_address = 0

    # --- Pass 1: Build Label Table & Clean Lines ---
    print("Starting Pass 1...")
    try:
        with open(input_filename, "r") as infile:
            for line_num, line in enumerate(infile, 1):
                original_line_content = line.strip() # Get raw line content for comparison
                print(f"\nDEBUG: === Processing Line {line_num} ===")
                print(f"DEBUG: Original content: '{original_line_content}'")

                # 1. Remove comments
                line_no_comment = line.split('#')[0]
                print(f"DEBUG: After comment split: '{line_no_comment}'")
                line_stripped = line_no_comment.strip()
                print(f"DEBUG: After strip(): '{line_stripped}' (Length: {len(line_stripped)})")

                # Check if the line is now effectively empty
                if not line_stripped:
                    print("DEBUG: Line is empty after cleaning, skipping.")
                    continue # Skip to the next line

                # 2. Check for label definitions
                label_match = re.match(r"^([a-zA-Z_][a-zA-Z0-9_]*):$", line_stripped)
                instruction_part = line_stripped # Assume it's an instruction unless it's only a label

                if label_match:
                    label = label_match.group(1)
                    if label in label_table:
                        raise ValueError(f"Duplicate label '{label}' found at line {line_num}")
                    print(f"DEBUG: Found label '{label}' at address {current_address}")
                    label_table[label] = current_address
                    instruction_part = "" # Line only contained a label
                    print(f"DEBUG: Instruction part set to '' because it was a label.")
                # No else needed here, instruction_part remains line_stripped if no label match

                # 3. Prepare line for Pass 2 if it contains an instruction
                # We already have instruction_part from above
                print(f"DEBUG: Checking instruction part for Pass 2: '{instruction_part}' (Length: {len(instruction_part)})")

                if instruction_part: # Check if the string is non-empty
                    print(f"DEBUG: *** ADDING instruction to cleaned_lines (Address: {current_address}) ***")
                    cleaned_lines.append({'line': instruction_part, 'addr': current_address, 'orig_line': line_num})
                    current_address += 1
                else:
                     # Only print skip message if it wasn't just a blank/comment line initially
                    if original_line_content and not label_match:
                         print("DEBUG: Skipping line (instruction part is empty, not a label).")
                    elif label_match:
                         print("DEBUG: Skipping line (was a label definition).")
                    # No message needed if it started as a blank/comment line

    except FileNotFoundError:
        print(f"Error: Input file '{input_filename}' not found.")
        sys.exit(1)
    except ValueError as e:
        print(f"Error during Pass 1: {e}")
        sys.exit(1)

    print("\nPass 1 complete. Label Table:")
    print(label_table)
    print("DEBUG: Final cleaned_lines list:") # Added label for clarity
    print(cleaned_lines) # Print the list that Pass 2 will use

    # --- Pass 2: Assemble Instructions ---
    print("Starting Pass 2...")
    assembled_code = []
    # Need to add a variable to track line number for error reporting in pass 2
    current_processed_line_num = 0
    try:
        # Check if cleaned_lines is empty before proceeding
        if not cleaned_lines:
            print("DEBUG: cleaned_lines is empty. No instructions to assemble in Pass 2.")

        for item in cleaned_lines:
            line = item['line']
            addr = item['addr']
            orig_line_num = item['orig_line']
            current_processed_line_num = orig_line_num # Store for potential error message
            print(f"  Assembling line {orig_line_num} (Addr {addr}): {line}")
            binary_code = assemble_line(line, label_table, addr)
            if binary_code:
                if len(binary_code) != 32:
                     raise ValueError(f"Internal Error: Assembled code for '{line}' is not 32 bits long! ({len(binary_code)} bits)")
                assembled_code.append(binary_code)
            # Removed the 'else' warning here, as assemble_line should either return code or raise error

    except (ValueError, NotImplementedError) as e:
        # Use the stored line number for better error context
        print(f"\n!!! Error during Pass 2 (Processing input line {current_processed_line_num}) !!!")
        print(f"Error details: {e}")
        sys.exit(1)

    # --- Write Output ---
    print(f"DEBUG: Number of binary instructions generated: {len(assembled_code)}")
    try:
        with open(output_filename, "w") as outfile:
            # Check if there's anything to write
            if not assembled_code:
                 print("DEBUG: No assembled code to write to output file.")
            for binary_line in assembled_code:
                outfile.write(binary_line + "\n")
        # Confirmation message comes after the writing block
        print(f"Assembly complete. Output written to {output_filename}")

    except IOError as e:
        print(f"Error writing output file '{output_filename}': {e}")
        sys.exit(1)

# --- Main Execution ---
if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python assembler.py <input_assembly_file> <output_binary_file>")
        # Provide default filenames for easier testing if none are given
        print("Running with default filenames: program.asm -> program.bin")
        input_file = "program.asm"  # Name of the input assembly file
        output_file = "program.bin"
        # Create a dummy input file for testing if it doesn't exist
        if not os.path.exists(input_file):
            print(f"Creating dummy input file: {input_file}")
            with open(input_file, "w") as f:
                f.write("""
# Example Program
start:
    ldim 10, %r1      # Load 10 into r1
    ldim 5, %r2       # Load 5 into r2
    cmb %r1, %r2, %r3 # r3 = r1 + r2 (15)
    pint %r3          # Print value in r3

    # Branching example
    ife %r1, %r2, skip_sub # If r1 == r2 (false), jump to skip_sub
    mns %r1, %r2, %r4 # r4 = r1 - r2 (5)
    pint %r4          # Print 5
skip_sub:
    cmbi %r3, 100, %r5 # r5 = r3 + 100 (115)
    pint %r5

    jmp end_program    # Jump to the end

    # Some other code maybe
    ldwd 0(%r1), %r6   # Example load

end_program:
    clr               # Clear registers
    end               # End program
""")
    else:
        input_file = sys.argv[1]
        output_file = sys.argv[2]

    run_assembler(input_file, output_file)