"""
Your fly.py script should read in person’s info using command line arguments in the order given below and print
real-time drone positional data on the screen, as well as show video from drone's camera.  It should run like this:

fly.py john_doe student cas computer_science

Use underscore to type name here. Only the first argument (name) should be required, i.e. if the rest of the arguments
are not provided the script should still work (it will obvisously only print the info it knows). After your script is
launched it should start writing real time drone data on the screen, concatenated with John Doe’s info.  Feel free to
either incorporate TelloPy or modify it to make it work. You do not have to write all or any code from scratch.
Your script does not have to be written in python.



Your test_flight.py script should only show video on the screen but not collect or write any drone data. test.fly
should not take any command line arguments.
"""
import sys

name = None
role = None
college = None
major = None


# return an array of strings based on number of inputs
def get_user_info():
    global name
    global role
    global college
    global major
    num_arg = len(sys.argv) - 1
    if num_arg == 0:
        print("Input should look like:\n python fly.py [name] [role] [college] [major]\n Arguments after name are "
              "optional")
        exit(1)

    pos = 1
    while pos <= num_arg:
        if pos == 1:
            name = sys.argv[pos]
        if pos == 2:
            role = sys.argv[pos]
        if pos == 3:
            college = sys.argv[pos]
        if pos == 4:
            major = sys.argv[pos]
        pos += 1


def main():
    get_user_info()


if __name__ == '__main__':
    main()
