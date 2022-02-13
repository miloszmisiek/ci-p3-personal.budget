import os
import sys
from termcolor import colored
import pyfiglet
import pyinputplus as pyip


class SystemMixin:
    """
    Mixin to clear terminal screen.
    """
    def clear_display(self):
        """
        Method to clear the display - logo remains.
        """
        os.system('clear')
        # Concept for pyfiglet styling comes from
        # https://www.youtube.com/watch?v=U1aUteSg2a4
        print(colored(pyfiglet.figlet_format("personal budget manager",
                                             font="graceful", justify="center",
                                             width=80), "green"))

    def restart_program(self):
        """
        Method to restart or quit the program.
        """
        # Code copied from
        # https://stackoverflow.com/questions/48129942/python-restart-program
        restart = pyip.inputYesNo("\nDo you want to go back to Main Menu? "
                                  "Type Yes or No:\n")

        if restart == "yes":
            os.execl(sys.executable, sys.executable, *sys.argv)
        else:
            self.clear_display()
            print("\nThe programm will be closed...")
            print("\nSee you next time!")
            sys.exit(0)
