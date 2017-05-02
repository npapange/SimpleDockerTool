SimpleDockerTool


Description:
    An application to manage containers and images for Docker, using the python Docker API. It consists of a manager that
can handle images and containers. Two wrappers are provided for each of these types, DockerImage and DockerContainer,
respectively. The manager app can perform a variety of operations such as create images and containers, remove them,
start and stop containers. For more fine-tuned control, instead of the docker run command for containers, this is done
in two steps: first the container is created and then it is started.
    After some containers are verified to be running, the logging and monitoring mechanism is started to monitor the
resource usage of each container (similar to docker stats) and to consolidate logs from all the containers to a single
log file.
    For the purpose of this assignment, the image and subsequent containers will contain a single simple 'Hello World!'
flask web app. After a container is started this app can be found at: http://192.168.99.100:<container port>/


Notes on Implementation:
    The container_manager module contains the ContainerManager, DockerImage and DockerContainer classes. The main class
ContainerManager creates instances of the DockerImage and DockerContainer classes and contains all the methods that
perform various operations on the images and containers.
    For the monitoring and logging, the goal was to have the information in real time. As such, the methods stats() and
logs() were called with the argument "stream=True". This returns the output of each method as a blocking generator.
Since it was required at the same time to get the logs and monitoring statistics from an arbitrary number of containers,
threads were used to iterate over each generator (two threads per container, one for the logs, the other for the monitoring).
The application will continue to output the logs/resource data until the user exits the application.
    The logging configuration is located in the "logging.conf" file. It prints messages in the console as well as saves
the log messages in a file called SimpleDockerApi.log. So as not to "bombard" the user with too many logging information,
the log level for the console output is set to "INFO", whereas for the log file it is set to "DEBUG", so that all log
statements are saved in a file.
    More information and additional details on usage can be found in the doc strings.


Requirements:
    Tested on Windows 7
    Python 2.7 + (tested on 2.7.12)
    Docker Toolbox for Windows


Installation:
    To install the application just check out the code and run "setup.py install". Also a requirements.txt file is provided
that can be used to independently install all required packages by running the command "pip install -r requirements.txt".


Usage:
    Before attempting to use this tool, please verify that the docker server/daemon is running on the system.
    There is a command line script provided that allows a user to run this tool: "simple_docker_api_runner.py" (located
in the root package directory). This script takes a number of parameters, all of which are optional, so that the user
can quickly test it with the default values. The user can provide the number of the image to be built, the number of
containers, their name and the ports which the simple flask api inside the container will listen to.


Tests:
    For testing the application there are unit tests provided in the tests folder. Most of the tests are based on mocks
that were used in the early stage of the implementation, to adhere to Test Driven Development principles.
	To run all tests, a convenience method is provided in the root package directory: "test_runner.py". This will run
all tests for container_manager.py. Due to time constraints coverage is not 100%. Also tests can be run using "nose"
as following: "cd path/to/project" and "nosetests".
