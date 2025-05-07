import os
memoryAddress = 5000
rRegister = 0
vars = dict()
def getInstructionLine(varName):
    global memoryAddress, rRegister
    rRegisterName = f"%r{rRegister}"
    setVariableRegister(varName, rRegisterName)
    returnText = f"    ldim 0,{rRegisterName} \n    cmbi {rRegisterName},{memoryAddress}, {rRegisterName} "
    rRegister += 1
    memoryAddress += 4
    return returnText

def setVariableRegister(varName, rRegister):
    global vars
    vars[varName] = rRegister

def getVariableRegister(varName):
    global vars
    if varName in vars:
        return vars[varName]
    else:
        return "ERROR"

def getAssignmentLinesImmediateValue(val, varName):
    global rRegister
    outputText = f"""    ldim {val},%r{rRegister}\n    srwd %r{rRegister}, 0({getVariableRegister(varName)})"""
    rRegister += 1
    return outputText


def getAssignmentLinesVariable(varSource, varDest):
    global rRegister
    outputText = ""
    registerSource = getVariableRegister(varSource)
    outputText += f"    ldwd 0({registerSource}), %r{rRegister}" + "\n"

    rRegister += 1

    registerDest = getVariableRegister(varDest)

    outputText += f"    srwd %r{rRegister-1}, 0({registerDest})"
    # rRegister += 1
    return outputText

def evaluatingCondition(line, methods, indent):
    global vars
    indentSpace = ""
    for i in range(indent*4):
        indentSpace+=" "
    output = ""
    if("%" in line):
        _, numbers = line.split("%")
        num1,num2 = numbers.split(" == ")
        num2 = num2[0]
        output+=f"{indentSpace}cmbi %r{rRegister},{num1}, %r{rRegister}\n"
        rRegister1 = rRegister+1
        rRegister2 = rRegister+2
        output+=f"{indentSpace}mdlo %r{vars['iteration']},%r{rRegister}, %r{rRegister1}\n"
        
        output+=f"{indentSpace}ldim {num2},%r{rRegister2}\n"
        for method in methods:
            output+=f"{indentSpace}ife %r{rRegister1},%r{rRegister2},{method}\n"
        
    return output
def determineIterations(line):
    arr = []
    words = line.split(" ")
    # print(words)
    for word in words:
        # print(word)
        if word.strip(";").isnumeric():
            
            arr.append((int)(word.strip(";")))

    if arr[0] < arr[1]:
        return(arr[1]-arr[0])
    else:
        return(arr[0]-arr[1])

f = open("/mnt/c/code/CS 240/240FinalProject/Compiler/program8.c", "r")

lines = f.readlines()

outputText = ""
outputText += "data: \n"
for line in lines:
    if "\"" in line and not("%d" in line):
        _,string,_ = line.split("\"")
        name = string.strip("n").strip("\\")
        vars[name] = string
        outputText += f"    {name}: \"{string}\"\n"

    
    
outputText += "instructions: \n"
for line in lines:
    if ("int" in line)  and ("main()" not in line) and ("for" not in line) and ("print" not in line):
        print(line)
        print("here")
        _, var = line.split()
        var = var.strip(";")
        outputText += getInstructionLine(var) + "\n"
    # assignments   
    elif " = " in line and ("for" not in line):
        varName, _, val = line.split()
        val = val.strip(";")
        if val.isdigit():
            # immediately value assignments
            outputText += getAssignmentLinesImmediateValue(val, varName) + "\n"
        else:
            # variable assignments
            outputText += getAssignmentLinesVariable(val, varName) + "\n"
for line in lines:
    if "printf(\"" in line:
        
        if "%d" in line:
            break

        _,name= line.split("printf(\"")
        methodName = name.replace("\\n\");\n","")
        outputText += f"    {methodName}:\n"
        outputText += f"        ldad {methodName}, %r{rRegister}\n"
        outputText += f"        pstr  0(%r{rRegister})\n"
        outputText += f"        jmp Loop\n"
for i  in range( len(lines)):
    if "for" in lines[i]:
        rRegister+=1
        outputText += f"    cmbi %r{rRegister},1, %r{rRegister}\n"
        vars["iteration"] = rRegister
        rRegister+=1
        numIterations = determineIterations(lines[i])
        outputText += f"    cmbi %r{rRegister},{numIterations}, %r{rRegister}\n"
        vars["end"] = rRegister
        rRegister+=1
        outputText += f"    cmbi %r{rRegister},1, %r{rRegister}\n"
        outputText += f"    for  %r{rRegister},Loop\n"
        outputText += f"    Loop:\n"
        
        
        outputText += f"        cmbi %r{vars['iteration']},1,%r{vars['iteration']}\n"
        outputText += f"        ife %r{vars['iteration']},%r{vars['end']},End\n"
    if "if" in lines[i]:
        j= i
        methods = []
        while ("}" not in lines[j]):
            j+=1
            if "printf" in lines[j]:
                _,strg,_ = lines[j].split("\"")
                met,_ = strg.split("\\")
                methods.append(met)

        outputText+=evaluatingCondition(lines[i],methods,2)
    if "else {" in lines[i]:
        j = i+1
        while ("}" not in lines[j]):
            if ("printf" in lines[j]) and ("i" in lines[j]):
               outputText+= f"        pint %r{vars['iteration']}\n"
            j+=1
    if(i == len(lines)-1):
        outputText += "    End:\n"
        outputText += "        end\n"
                


outputFile = open("/mnt/c/code/CS 240/240FinalProject/Compiler/program8.mpsm", "w")

outputFile.write(outputText)
