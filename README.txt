## Script Purpose

The purpose of the script is to convert a plan into a command sequence for uplink to a satellite and store it as a .csv file for given start and end time based on the constraints. 
The script uses various inputs including TLE data, pass summaries, planetary data from 'de421.bsp', and a specific time window defined by a start and end time.

### Input Files

1. `TLE.txt`: Contains Two-Line Element set data for the satellite.
2. `Pass_Summary.csv`: Provides summaries of satellite passes.
3. `de421.bsp`: Planetary data file used with the `skyfield` library for astronomical calculations.
4. `Satellite_Commands.csv`: The output file where the satellite command sequence is stored.

### Time Window

The script operates within a specified time window, defined by a start and end time in UTC.

##  To Run the Script

A virtual environment in Python is used to manage project-specific dependencies and avoid conflicts between different projects.
Here's how you can create and use a virtual environment:


1. **Install Python**: Ensure Python is installed on your system. It usually comes with `pip` and `virtualenv`.
 
2. **Create a Virtual Environment**: Navigate to your project's directory and run `python -m venv env`.

### For Windows:
3. Activate the Virtual Environment**: Run `.\\env\\Scripts\\activate`.

### For macOS/Linux:
3. Activate the Virtual Environment : Run `source env/bin/activate`.

4. Install Packages: Run the following command to install the packages:  Run `pip install -r requirements.txt`

5. RUN the script -  Run `Python3 main.py'
This will  create a output file - Command_Sch_Output_starttime.csv

6. **Deactivate the Environment**: Run `deactivate` when done.

 


