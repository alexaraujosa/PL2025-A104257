import os
import sys
import argparse
import traceback
from compiler.lexer import lexer
from compiler.synanaler import parser
import compiler.semanaler as semanal
import compiler.codegen as codegen
from util.cli import CLI, CLICommand

g_debugMode = False

def traceTokensSnippet(snippet, tracelex = True, tracesyn = False, tracediag = False):
    if (not snippet.endswith(".pas")): snippet += ".pas"
    with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), "cases", snippet)) as sf:
        inp = sf.read()

        if (tracelex):
            lexer.options["printDiags"] = True
            lexer.input(inp)
            while tok := lexer.token():
                print(f"\x1b[36mTOKEN:\x1b[0m {tok}")
            
            lexer.finish()
            print("LEXSTAT:", len(lexer.lineLens), lexer.lineLens, lexer._lastLineLexPos)
            print("LEXDIAG:")
            if (len(lexer.diagnostics) != 0):
                for diag in lexer.diagnostics:
                    print("  -", diag.toString(lexer))
            else:
                print("  - N/A")
        
        if (tracesyn):
            lexer.options["printDiags"] = False
            # lexer.diagnostics = []
            lexer.reset()
            
            pout = parser.parse(inp, lexer, g_debugMode, False, lexer.getExtendedToken)
            print(f"\x1b[32mPARSED:\x1b[0m {pout}")
            print("SYNANALDIAG:")
            if (len(parser.diagnostics) != 0):
                for diag in parser.diagnostics:
                    print("  -", diag.toString(lexer))
            else:
                print("  - N/A")

            if (tracediag):
                print("SYNANALTRACEDIAG:")
                if (len(parser._diagnosticTrace) != 0):
                    for diag in parser._diagnosticTrace:
                        print("  -", diag.toString(lexer))
                else:
                    print("  - N/A")

def dumpAST(snippet, outFile, tracelex = True, tracesyn = False, tracediag = False, verbose = False):
    if (not snippet.endswith(".pas")): snippet += ".pas"
    with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), "cases", snippet)) as sf:
        inp = sf.read()

        if (tracelex):
            lexer.options["printDiags"] = True
            lexer.input(inp)
            while tok := lexer.token():
                print(f"\x1b[36mTOKEN:\x1b[0m {tok}")
            
            lexer.finish()
            print("LEXSTAT:", len(lexer.lineLens), lexer.lineLens, lexer._lastLineLexPos)
            print("LEXDIAG:")
            if (len(lexer.diagnostics) != 0):
                for diag in lexer.diagnostics:
                    print("  -", diag.toString(lexer))
            else:
                print("  - N/A")
        
        lexer.options["printDiags"] = False
        lexer.reset()
        
        pout = parser.parse(inp, lexer, g_debugMode, False, lexer.getExtendedToken)
        if (tracesyn):
            print(f"\x1b[32mPARSED:\x1b[0m {pout}")
            print("SYNANALDIAG:")
            if (len(parser.diagnostics) != 0):
                for diag in parser.diagnostics:
                    print("  -", diag.toString(lexer))
                    if (verbose): print("  --", diag)
            else:
                print("  - N/A")

            if (tracediag):
                print("SYNANALTRACEDIAG:")
                if (len(parser._diagnosticTrace) != 0):
                    for diag in parser._diagnosticTrace:
                        print("  -", diag.toString(lexer))
                        if (verbose): print("  --", diag)
                else:
                    print("  - N/A")

        if (pout != None):
            jsonstr = pout.toJSONString()
            outFilePath = os.path.join(os.getcwd(), outFile)
            try:
                with open(outFilePath, "w") as of:
                    of.write(jsonstr)
                print(f"\x1b[32mSuccessfully dumped AST to:\x1b[0m", outFilePath)
            except BaseException as e:
                print(f"\x1b[31mCould not dump AST: Unable to open output file:\x1b[0m", outFilePath)
                # traceback.print_stack(file=sys.stderr)
                print('  '.join(traceback.format_exception(e)))
        else:
            print(f"\x1b[31mCould not dump AST: Parser output is nil.\x1b[0m")

def fullTest(snippet, traceall = False, tracediag = False, verbose = False, dumpAST = False, outFile = None):
    if (not snippet.endswith(".pas")): snippet += ".pas"
    with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), "cases", snippet)) as sf:
        inp = sf.read()

        # Lexical Analysis
        if (traceall):
            lexer.options["printDiags"] = True
            lexer.input(inp)
            while tok := lexer.token():
                print(f"\x1b[36mTOKEN:\x1b[0m {tok}")
            
            lexer.finish()
            print("LEXDIAG:")
            if (len(lexer.diagnostics) != 0):
                for diag in lexer.diagnostics:
                    print("  -", diag.toString(lexer))
            else:
                print("  - N/A")

        if (len(lexer.diagnostics) != 0):
            print(f"\x1b[31mInvalid program: Lexical analysis errored out.\x1b[0m")
            return
        
        lexer.options["printDiags"] = False
        lexer.reset()
        
        # Syntatic Analysis
        pout = parser.parse(inp, lexer, g_debugMode, False, lexer.getExtendedToken)
        if (tracediag):
            print(f"\x1b[32mPARSED:\x1b[0m {pout}")
            print("SYNANALDIAG:")
            if (len(parser.diagnostics) != 0):
                for diag in parser.diagnostics:
                    print("  -", diag.toString(lexer))
                    if (verbose): print("  --", diag)
            else:
                print("  - N/A")

            if (traceall):
                print("SYNANALTRACEDIAG:")
                if (len(parser._diagnosticTrace) != 0):
                    for diag in parser._diagnosticTrace:
                        print("  -", diag.toString(lexer))
                        if (verbose): print("  --", diag)
                else:
                    print("  - N/A")
        
        if (pout == None):
            print(f"\x1b[31mInvalid program: Syntatic analysis errored out with critical error.\x1b[0m")
            return

        # Optional AST dump
        if (dumpAST):
            jsonstr = pout.toJSONString()
            outFilePath = os.path.join(os.getcwd(), outFile)
            try:
                with open(outFilePath, "w") as of:
                    of.write(jsonstr)
                print(f"\x1b[32mSuccessfully dumped AST to:\x1b[0m", outFilePath)
            except BaseException as e:
                print(f"\x1b[31mCould not dump AST: Unable to open output file:\x1b[0m", outFilePath)
                print('  '.join(traceback.format_exception(e)))

        
        # Prevent the Semantic Analyser from attempting to process fuck all
        if (len(parser.diagnostics) != 0):
            print(f"\x1b[31mInvalid program: Syntatic analysis errored out.\x1b[0m")
            return

        # Semantic Analysis
        semanal.SA_STATE["debug"] = g_debugMode
        semVeredict = semanal.analyzeSemantics(pout)
        if (semVeredict == False):
            print(f"\x1b[31mInvalid program: Semantic analysis errored out.\x1b[0m")
            # Allow fallthrough here in order to allow warns to still be printed.
            
        semDiags = semanal.getDiagnostics()
        if (tracediag):
            print("SEMANALDIAG:")
            if (len(semDiags) != 0):
                for diag in semDiags:
                    print("  -", diag.toString(lexer))
                    if (verbose): print("  --", diag)
            else:
                print("  - N/A")

        if (len(semDiags) != 0):
            print(f"\x1b[31mInvalid program: Semantic analysis errored out.\x1b[0m")
            return

        outFilePath = os.path.join(os.getcwd(), "out", f"{snippet.split(os.path.sep)[-1].replace('.pas', '.ewvm')}")
        codegen.emitCode(pout, outFilePath)
        print(f"\x1b[32mSuccessfully wrote output to:\x1b[0m", outFilePath)

def makeCLI():
    caseCmd = CLICommand(name="case", description="Runs a specific test suite case")
    caseCmd.addArgument("target", type=str, help="The name of a test suite target to run.")
    caseCmd.addArgument(
        "--debug", "-d", 
        action=argparse.BooleanOptionalAction, 
        help="Whether additional information should be presented while running the test suite."
    )
    caseCmd.addArgument(
        "--dumpAST", 
        action=argparse.BooleanOptionalAction, 
        help="Whether an AST dump should be emmited if the semantic analyser returns a valid structure."
    )
    caseCmd.addArgument(
        "--out", "-o", 
        help="The output file to dump the AST.",
        required=False
    )
    caseCmd.addArgument(
        "--traceall", 
        action=argparse.BooleanOptionalAction, 
        help="Whether all stages should be traced individually."
    )
    caseCmd.addArgument(
        "--tracediag", 
        action=argparse.BooleanOptionalAction, 
        help="Whether intermediate diagnostics should be output to the STDOUT."
    )
    caseCmd.addArgument(
        "--verbose", "-v", 
        action=argparse.BooleanOptionalAction, 
        help="Whether additional debug information should be presented while running the test suite, including some " \
            "internal state."
    )

    traceLexCmd = CLICommand(name="tracelex", description="Traces the lexer output for specific test suite target")
    traceLexCmd.addArgument("target", type=str, help="The name of a test suite target to run.")
    traceLexCmd.addArgument(
        "--debug", "-d", 
        action=argparse.BooleanOptionalAction, 
        help="Whether additional information should be presented while running the test suite."
    )

    traceSynCmd = CLICommand(
        name="tracesyn", 
        description="Traces the syntatic analyser output for a specific test suite target"
    )
    traceSynCmd.addArgument("target", type=str, help="The name of a test suite target to run.")
    traceSynCmd.addArgument(
        "--tracelex", "-l", 
        action=argparse.BooleanOptionalAction, 
        help="Whether the trace should include lexer output."
    )
    traceSynCmd.addArgument(
        "--tracediag", 
        action=argparse.BooleanOptionalAction, 
        help="Whether intermediate diagnostics should be output to the STDOUT."
    )
    traceSynCmd.addArgument(
        "--debug", "-d", 
        action=argparse.BooleanOptionalAction, 
        help="Whether additional information should be presented while running the test suite."
    )

    dumpASTCmd = CLICommand(
        name="dumpast", 
        description="Dumps the resulting AST for a specific test suite target"
    )
    dumpASTCmd.addArgument("target", type=str, help="The name of a test suite target to run.")
    dumpASTCmd.addArgument(
        "--tracelex", "-l", 
        action=argparse.BooleanOptionalAction, 
        help="Whether the lexer output should be output to the STDOUT."
    )
    dumpASTCmd.addArgument(
        "--tracesyn", "-s", 
        action=argparse.BooleanOptionalAction, 
        help="Whether the syntatic analyser output should be output to the STDOUT."
    )
    dumpASTCmd.addArgument(
        "--tracediag", 
        action=argparse.BooleanOptionalAction, 
        help="Whether intermediate diagnostics should be output to the STDOUT."
    )
    dumpASTCmd.addArgument(
        "--out", "-o", 
        help="The output file to dump the AST.",
        required=True
    )
    dumpASTCmd.addArgument(
        "--debug", "-d", 
        action=argparse.BooleanOptionalAction, 
        help="Whether additional information should be presented while running the test suite."
    )
    dumpASTCmd.addArgument(
        "--verbose", "-v", 
        action=argparse.BooleanOptionalAction, 
        help="Whether additional debug information should be presented while running the test suite, including some " \
            "internal state."
    )

    cli = CLI(name="Test", description="A test suite for the Standard Pascal compiler.")
    cli.addCommand(caseCmd)
    cli.addCommand(traceLexCmd)
    cli.addCommand(traceSynCmd)
    cli.addCommand(dumpASTCmd)

    return cli

if __name__ == "__main__":
    cli = makeCLI()

    print(sys.argv)
    args = cli.parse()

    g_debugMode = args.debug
    
    match (args.switch()):
        case "case":
            fullTest(args.target, args.traceall, args.tracediag, args.verbose, args.dumpAST, args.out)
        case "tracelex":
            traceTokensSnippet(args.target)
        case "tracesyn":
            traceTokensSnippet(args.target, args.tracelex, True, args.tracediag)
        case "dumpast":
            dumpAST(args.target, args.out, args.tracelex, True, args.tracediag, args.verbose)
