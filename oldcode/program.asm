
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
