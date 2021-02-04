from os import path
import numpy as np
import argparse

from multical.workspace import Workspace

from multical.interface import visualizer
from multical.io.logging import warning, info


def main(): 
    np.set_printoptions(precision=4, suppress=True)

    parser = argparse.ArgumentParser()
    parser.add_argument('workspace_file', help='workspace filename to load')

    args = parser.parse_args()

    ws = Workspace.load(args.workspace_file)

    visualizer.visualize(ws)


if __name__ == '__main__':
    main()
