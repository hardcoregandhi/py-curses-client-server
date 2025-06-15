import argparse
import subprocess
import sys
import os

def package(script_name):
    """Package the specified Python script using PyInstaller."""
    # Create a build directory if it doesn't exist
    build_dir = 'build'
    spec_dir = 'specs'  # Directory for .spec files
    os.makedirs(build_dir, exist_ok=True)
    os.makedirs(spec_dir, exist_ok=True)

    try:
        logging.info(f"Packaging {script_name}...")
        subprocess.run([
            'pyinstaller', 
            script_name, 
            '-F', 
            '--distpath', build_dir, 
            '--workpath', build_dir, 
            '--specpath', spec_dir
        ], check=True)
        logging.info(f"Packaging completed successfully for {script_name}.")
    except subprocess.CalledProcessError as e:
        logging.info(f"Error during packaging {script_name}: {e}")
        sys.exit(1)

def run():
    """Run the server.py and main.py scripts."""
    try:
        subprocess.run(['python', 'server.py'], check=True)
        subprocess.run(['python', 'main.py'], check=True)
        logging.info("Scripts executed successfully.")
    except subprocess.CalledProcessError as e:
        logging.info(f"Error during execution: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="A script to package and run Python scripts.")
    parser.add_argument('command', choices=['run', 'package'], help="Command to execute: 'run' or 'package'.")

    args = parser.parse_args()

    if args.command == 'package':
        package('server.py')
        package('main.py')
    elif args.command == 'run':
        run()

if __name__ == "__main__":
    main()
