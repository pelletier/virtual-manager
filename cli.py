import sys
import inspect


class CLI(object):
    """
    The CLI is the main part of the script. It handles the different commands
    and their possible arguments.

    The idea is simple: you write functions (ie commands) and register them to
    the CLI using the cli.register decorator. You just have to call cli.main()
    to interact with the user.
    """

    actions = {}

    def help(self, msg=None):
        """
        Display the list of the commands and their arguments. Eventually it
        will also display an error message.
        """

        # Print the message if given.
        if not msg == None:
            print str(msg) + "\n"

        # Display the list of commands, in the alphabetical order.
        print "Use one of the following commands:"
        for action in sorted(self.actions.keys()):
            info = self.actions[action]
            joined_oblig = ' '.join(info['required'])
            if len(info['additional']) > 0:
                add = ["<%s>" % x for x in info['additional']]
                joined_add = '[' + ' '.join(add) + ']'
            else:
                joined_add = ''
            print "\t* %s %s %s" % (action, joined_oblig, joined_add)

    def register(self, *args):
        """Add the action the CLI"""
        def decorate(f):
            if not len(args) == 1:
                full = f.__name__
            else:
                full = args[0]

            # Gather some informations about the arguments of the function, to
            # display them in help() and check for the min / max number of
            # arguments on call.
            spec = inspect.getargspec(f)
            fargs = spec.args if spec.args else []
            nbr_args = len(fargs)
            nbr_filled = len(spec.defaults) if spec.defaults else 0
            reqs = fargs[:nbr_args-nbr_filled+1]
            adds = fargs[nbr_args-nbr_filled+1:]

            info = {
                'function'  : f,
                'required'  : reqs,
                'additional': adds,
            }

            self.actions[full] = info
            return f
        return decorate



    def main(self):
        """Entry point of the CLI"""

        # Make sure we have at least 2 arguments: the script name and
        # a command.
        if len(sys.argv) < 2:
            self.help()
            return 0

        # Gather the action and any parameter.
        action = sys.argv[1]
        params = sys.argv[2:]

        # If this is not a registered command, display an error and the
        # commands list.
        if not action in self.actions.keys():
            self.help("Wrong command")
            return -1

        # Grab information about the requested command.
        info = self.actions[action]
        func = info['function']
        min_args = len(info['required'])
        max_args = min_args + len(info['additional'])

        # Make sure the command receives the correct number of arguments.
        if len(params) > max_args or len(params) < min_args:
            msg = "Wrong number of arguments (want %s<x<%s, got %s)."\
                        % (min_args, max_args, len(params))
            self.help(msg)
            return -1

        # Run the command.
        # This could need some verification (the user input is given directly
        # to the function, without being sanitized, which is a bad practice). Yet
        # it's a hacker tool, yeah?
        return func(*params)


cli = CLI()
