import re
import argparse

class _CLIArgumentParser(argparse.ArgumentParser):
    def format_help(self):
        orig = super().format_help()
        return re.sub(r"\n.+\$DELETE.*$", "", orig, 0x7fffffff, re.MULTILINE)

class CLICommandArgs:
    def __init__(self):
        self.args = {}
        self._commandPath = []
        self._commandPathDiff: list[str] = None

    def __repr__(self):
        ret = f"CLICommandArgs{{{'.'.join(self._commandPath)}}}" \
            + f"[{', '.join(map(lambda a: f'{a}={repr(self.args[a])}', self.args))}]"
        return ret

    def setArg(self, name, value):
        self.args[name] = value
        setattr(self, name, value)
    
    def nest(self, subCmd):
        self._commandPath.append(subCmd)

    def merge(self, args: "CLICommandArgs"):
        if (len(self._commandPath) < len(args._commandPath)): self._commandPath = args._commandPath
        self.args = {**self.args, **args}

    def switch(self):
        if (self._commandPathDiff == None): self._commandPathDiff = [*self._commandPath]

        return self._commandPathDiff.pop(0)

class CLICommand:
    def __init__(self, **kwargs):
        self.name = kwargs.get("name", "unknown")
        self.description = kwargs.get("description", "N/A")
        self.arguments = []
        self._subcommands: list["CLICommand"] = []
        self.subParserHook = None
        self._subCmdArgName = None

    def addArgument(self, *args, **kwargs):
        self.arguments.append((args, kwargs))
        if (not ("-" in args[0]) and self._subCmdArgName == None): self._subCmdArgName = args[0]

    def addSubCommand(self, cmd: "CLICommand"):
        """
            Adds a sub-command to this command.

            WARN: argparse is quite possibly the stupidest piece of shit I've ever seen after python itself.
            Sub-commands were already hard enough to implement, and I had to resort to break them from the regular flow,
            and sub-sub-commands are out of the fucking question. You'll have to edit the _call method and quite 
            possibly hijack the argparse default behavior through _CLIArgumentParser for it to work.
        """
        self._subcommands.append(cmd)

    def _call(self, args: argparse.Namespace, cliArgs: CLICommandArgs = None):
        """
            Method to be called after argparse processes the CLI arguments (rather horribly, might I add).

            As of the time of writing this documentation, it is, technically, prepared to handle sub-sub-commands, 
            however, due to argparse being utterly horrible at the one fucking job it has, it is rather broken. It can 
            possibly be fixed by modifying the argument parse behavior on _CLIArgumentParser, but at that point one 
            might as well just do it all themselves.
        """
        if (cliArgs == None): cliArgs = CLICommandArgs()
        cliArgs.nest(self.name)

        if (self._subCmdArgName != None):
            if (self._subCmdArgName in args.__dict__):
                scmdCandidate = args.__dict__[self._subCmdArgName]
                for scmd in self._subcommands:
                    if (scmd.name == scmdCandidate):
                        delattr(args, self._subCmdArgName)
                        return scmd._call(args, cliArgs)

        delattr(args, "_CLI_COMMAND_PARSE_FUNC_")
        for arg in args._get_kwargs():
            cliArgs.setArg(arg[0], arg[1])

        return cliArgs

    def hook(self, parentParserHook):
        """
            Registers this command on a given parent argument parser.
        """
        cmdParser = parentParserHook.add_parser(self.name, help=self.description)
        cmdParser.set_defaults(_CLI_COMMAND_PARSE_FUNC_=self._call)
        for arg in self.arguments:
            cmdParser.add_argument(*arg[0], **arg[1])
        
        if (len(self._subcommands) > 0):
            # self.subParserHook = cmdParser.add_subparsers(help='sub-sub-command help')
            self.subParserHook = cmdParser.add_subparsers(title="Subcommands", help="$DELETE")
            for cmd in self._subcommands:
                cmd.hook(self.subParserHook)
    

class CLI:
    def __init__(self, **kwargs):
        self.name = kwargs.get("name", "unknown")
        self.description = kwargs.get("description", "N/A")
        # self.parser = argparse.ArgumentParser(
        self.parser = _CLIArgumentParser(
            prog=self.name,
            description=self.description
        )
        # self.subParserHook = self.parser.add_subparsers(help='sub-command help')
        self.subParserHook = self.parser.add_subparsers(title="Subcommands", help="$DELETE")
        self._commands = []
        self._arguments = []

    def addArgument(self, *args, **kwargs):
        self._arguments.append((args, kwargs))
        self.parser.add_argument(*args, **kwargs)

    def addCommand(self, cmd: CLICommand):
        self._commands.append(cmd)
        cmd.hook(self.subParserHook)

    def parse(self, *args) -> CLICommandArgs:
        _args = self.parser.parse_args(*args)
        args = _args._CLI_COMMAND_PARSE_FUNC_(_args)
        return args
