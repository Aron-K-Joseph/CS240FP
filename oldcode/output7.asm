addi $t0, $zero, 5000
addi $t1, $zero, 5004
addi $t2, $zero, 5008
addi $t3, $zero, 7
sw $t3, 0($t0)
addi $t4, $zero, 18
sw $t4, 0($t1)
lw $t5, 0($t0)
sw $t5, 0($t2)
a == c
addi $t6, $zero, 19
sw $t6, 0($t1)
addi $t7, $zero, 13
sw $t7, 0($t2)
AFTER:
addi $t8, $zero, 1
sw $t8, 0($t0)
addi $t9, $zero, 2
sw $t9, 0($t1); 