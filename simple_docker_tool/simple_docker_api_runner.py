#!/usr/bin/python

import argparse
import logging
import logging.config
import sys

from simple_docker_tool.simple_docker_api.container_manager import ContainerManager

__author__ = 'Nikitas Papangelopoulos'

# Getting the logging settings
logging.config.fileConfig('logging.conf', disable_existing_loggers=False)

logger = logging.getLogger(__name__)


def main(image_name, container_number, container_ports, container_names):
    # Creating a ContainerManager
    cm = ContainerManager()
    image = cm.build_image('docker_image_files', image_name)

    use_custom_names = False
    if container_names:
        use_custom_names = True

    # Creating the containers
    for i in range(container_number):
        if use_custom_names:
            cm.create_container(image.id, name=container_names[i], port=container_ports[i])
        else:
            cm.create_container(image.id, port=container_ports[i])

    # Checking that all containers were created successfully
    all_success = all([container.created_successfully for container in cm.available_containers()])
    if all_success:
        logger.debug('All containers created successfully')
        # Starting the containers.

    # Starting the created containers
    for container in [container for container in cm.available_containers() if container.created_successfully]:
        cm.start_container(container.id)
        # Verifying that each one is running
        if cm.get_container(container.id).status == 'running':
            logger.info("Container: {} at: {} is running OK.".format(container.id, container.port))
        else:
            logger.info("Container: {} at: {} is failed to run.".format(container.id, container.port))

    # Starting the monitoring and logging. This is blocking.
    cm.monitoring_logging_start()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='A script to run a number of Docker containers based on an image.')
    parser.add_argument('-img', '--image-name', type=str, default='simple_flask:latest',
                        help='The name to give the image. It is good practice to give <name>:latest.')
    parser.add_argument('-n', '--container-number', type=int, default=3,
                        help='The number of container to start.')
    parser.add_argument('-ports', '--container-ports', type=list, default=[5001, 5002, 5003],
                        help='The port that each container should use. Must be same as the number of containers.')
    parser.add_argument('-names', '--container-names', type=list, default=[],
                        help='The name of the containers to be created. If none, auto-generated names will be used.')
    args = parser.parse_args()

    wrong_input = False
    if args.container_names:
        if len(args.container_number) != len(args.container_ports) and len(args.container_number) != len(
                args.container_names):
            wrong_input = True
    else:
        if len(args.container_number) != len(args.container_ports):
            wrong_input = True

    if wrong_input:
        logger.error('Number of containers, ports and names must be the same.')
        sys.exit(-1)

    main(args.image_name, args.container_number, args.container_ports, args.container_names)
