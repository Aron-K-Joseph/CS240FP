memoryAddress = 5000
tRegister = 0
vars = dict()

def getInstructionLine(varName):
    global memoryAddress, tRegister
    tRegisterName = f"$t{tRegister}"
    setVariableRegister(varName, tRegisterName)
    returnText = f"addi {tRegisterName}, $zero, {memoryAddress}"
    tRegister += 1
    memoryAddress += 4
    return returnText

def setVariableRegister(varName, tRegister):
    global vars
    vars[varName] = tRegister

def getVariableRegister(varName):
    global vars
    if varName in vars:
        return vars[varName]
    else:
        return "ERROR"

def getAssignmentLinesImmediateValue(val, varName):
    global tRegister
    outputText = f"""addi $t{tRegister}, $zero, {val}
sw $t{tRegister}, 0({getVariableRegister(varName)})"""
    tRegister += 1
    return outputText


def getAssignmentLinesVariable(varSource, varDest):
    global tRegister
    outputText = ""
    registerSource = getVariableRegister(varSource)
    outputText += f"    lw $t{tRegister}, 0({registerSource})" + "\n"

    tRegister += 1

    registerDest = getVariableRegister(varDest)

    outputText += f"sw $t{tRegister-1}, 0({registerDest})"
    # tRegister += 1
    return outputText

f = open("program7.c", "r")

lines = f.readlines()

outputText = ""

for line in lines:
    outputText += "data:"
    if "\"" in line:
        _,string,_ = line.split("\"")
        name = string.strip("\n")
        vars[name] = string
        outputText += f"{name}: {string}"
    
    
    
    
    if line.startswith("if "):
        _, expr = line.split("if ")
        expr = expr.replace("(","").replace(")","").replace("{","")
        outputText += expr
    elif line.startswith("}"):
        outputText += "AFTER:" + "\n"
    # int declarations
    elif line.startswith("int "):
        _, var = line.split()
        var = var.strip(";")
        outputText += getInstructionLine(var) + "\n"
    # assignments
    elif "=" in line:
        varName, _, val = line.split()
        val = val.strip(";")
        if val.isdigit():
            # immediately value assignments
            outputText += getAssignmentLinesImmediateValue(val, varName) + "\n"
        else:
            # variable assignments
            outputText += getAssignmentLinesVariable(val, varName) + "\n"
    else:
        pass

outputFile = open("output7.asm", "w")

outputFile.write(outputText)