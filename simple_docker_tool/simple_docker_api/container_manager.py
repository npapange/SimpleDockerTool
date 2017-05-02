#!/usr/bin/python

import ast
import logging
import os
import threading
import time

import docker
import numpy as np
from docker.errors import *

__author__ = 'Nikitas Papangelopoulos'

logger = logging.getLogger(__name__)

# A boolean to save the monitoring to an external file.
SAVE_MONITORING = True
# A boolean to print the raw output of the to generator from stats().
RAW_MONITORING = False


class ContainerManager(object):
    def __init__(self):
        """
        Constructor. it calls docker.from_env() to create the docker client for communicating with a Docker server.
        """
        self.__image_dict = {}
        self.__container_dict = {}

        # Checking if the required environment variables are in the system path
        if {'DOCKER_HOST', 'DOCKER_TLS_VERIFY', 'DOCKER_CERT_PATH'}.issubset(os.environ.keys()):
            self.docker_client = docker.from_env()
            logger.info("Successfully created the docker client")
        else:
            logger.warning("Missing environment variables from system path, attempting to set them.")
            env = {'DOCKER_HOST': 'tcp://192.168.99.100:2376', 'DOCKER_TLS_VERIFY': '1',
                   'DOCKER_CERT_PATH': 'C:\Users\{}\.docker\machine\machines\default'.format(os.environ['USERPROFILE'].
                                                                                             split('\\')[2])}
            try:
                self.docker_client = docker.from_env(environment=env)
                logger.info("Successfully created the docker client")
            except TLSParameterError:
                logger.error('Missing environment variables from system path. Failed to create the docker client.\n '
                             'Please run "docker-machine env <machine-name>"')

    def build_image(self, path, tag):
        """
        A method to create a docker image from a folder containing a Dockerfile.
        :param path: The path to the folder that contains the Dockerfile.
        :type path: str
        :param tag: The tag to assign to the image.
        :type tag: str
        :return: The created docker image.
        :rtype: DockerImage
        """
        docker_image = DockerImage(self.docker_client, path, tag)
        self.__image_dict[docker_image.id] = docker_image
        return docker_image

    def get_image(self, image_id):
        """
        A method to retrieve an image given an ID.
        :param image_id: TThe image ID to retrieve.
        :type image_id: str
        :return: The docker image.
        :rtype: DockerImage || None
        """
        try:
            logger.debug('Retrieved image: ' + image_id)
            return self.__image_dict[image_id]
        except KeyError:
            logger.error('Image: {}, was not found.'.format(image_id))
            logger.info('Available image ids: {}.'.format([image.id for image in self.__image_dict]))
            return None

    def remove_image(self, image_id):
        """
        A method to remove an image given an ID.
        :param image_id: TThe image ID to remove.
        :type image_id: str
        :return: A boolean signifying if the removal was successful.
        :rtype: bool
        """
        try:
            self.__image_dict.pop(image_id)
            # Also removing from the client
            self.docker_client.images.remove(image_id)
            logger.debug('Removed image: ' + image_id)
            return True
        except KeyError:
            logger.error('Unable to remove image: {}. It was not found.'.format(image_id))
            logger.info('Available image ids: {}.'.format(self.__image_dict.keys()))
            return False

    def available_images(self):
        """
        A method to return the dictionary of all available images that were created by the container manager.
        :return: A dictionary image_id:DockerImage
        :rtype: dict
        """
        return self.__image_dict

    def create_container(self, image_id, name='', port=None):
        """
        A method to create a docker container based on a specific image. If no port is provided the default 5000 will
        be used by the DockerContainer constructor.
        :param image_id: The image ID to use for creating the container.
        :type image_id: str
        :param name: A name to give to the container. Optional.
        :type name: str
        :param port: The port to map to the container web_app. Optional
        :type port: int
        :return: The container that was created or None, if there was an error during creation.
        :rtype: DockerContainer || None
        """
        if port:
            container = DockerContainer(self.docker_client, image_id, name, port)
        else:
            container = DockerContainer(self.docker_client, image_id, name
                                        )
        if container.created_successfully:
            self.__container_dict[container.id] = container
            return container
        else:
            return None

    def start_container(self, container_id):
        """
        A method to start the docker container of the specified container ID. It also updates the status of the
        container to 'running'.
        :param container_id: The ID of the container to start.
        :type container_id: str
        :return: A boolean signifying if the container was started successfully.
        :rtype: bool
        """
        try:
            logger.info('Starting container with id: ' + container_id)
            self.docker_client.containers.get(container_id).start()
            self.__container_dict[container_id].refresh_status(self.docker_client.containers.get(container_id).status)
            return True
        except APIError, e:
            logger.error("Error while starting container. Error message: {}".format(e))
            return False

    def stop_container(self, container_id):
        """
        A method to stop the docker container of the specified container ID. It also updates the status of the
        container to 'exited'.
        :param container_id: The ID of the container to stop.
        :type container_id: str
        :return: A boolean signifying if the container was stopped successfully.
        :rtype: bool
        """
        try:
            logger.debug('Stopping container with id: ' + container_id)
            self.docker_client.containers.get(container_id).kill()
            self.__container_dict[container_id].refresh_status(self.docker_client.containers.get(container_id).status)
            return True
        except APIError, e:
            logger.error("Error while stopping container. Error message: {}".format(e))
            return False

    def get_container(self, container_id):
        """
        A method to retrieve the container of the specified container ID.
        :param container_id: The ID of the container to retrieve.
        :type container_id: str
        :return: The container or None.
        :rtype: DockerContainer || None
        """
        try:
            logger.debug('Retrieving container: ' + container_id)
            return self.__container_dict[container_id]
        except KeyError:
            logger.error('Container: {}, was not found.'.format(container_id))
            logger.info('Available container ids: {}.'.format(self.__container_dict.keys()))
            return None

    def remove_container(self, container_id):
        """
        A method to remove the container of the specified container ID.
        :param container_id: The ID of the container to remove.
        :type container_id: str
        :return: A boolean signifying if the removal was successful.
        :rtype: bool
        """
        try:
            self.__container_dict.pop(container_id)
            # Also removing from the client
            self.docker_client.containers.remove(container_id)
            logger.debug('Removed container: ' + container_id)
            return True
        except (ValueError, APIError), e:
            logger.error('Error while removing container: ' + str(e))
            logger.info('Available container ids: {}.'.format(self.__container_dict.keys()))
            return False

    def container_status(self, container_id):
        """
        A method to retrieve the status of the container of the specified container ID.
        :param container_id: The ID of the container to check.
        :type container_id: str
        :return: The status of the container as a string.
        :rtype: str
        """
        return self.get_container(container_id).status

    def available_containers(self):
        """
        A method to return the dictionary of all available containers that were created by the container manager.
        :return: A dictionary image_id:DockerContainer
        :rtype: dict
        """
        return self.__container_dict

    def running_containers(self):
        """
        A method to return the list of all running containers that were created by the container manager.
        :return: A list of DockerContainers.
        :rtype: list
        """
        return [container for container in self.__container_dict.values() if container.status == 'running']

    def running_containers_on_server(self):
        """
        A method to return the list of all running containers currently on the server, regardless of whether they were
        started by an external process or not.
        :return: A list of tuples of (container name, container id).
        :rtype: list
        """
        return [(container.name, container.id) for container in self.docker_client.containers.list() if
                container.status == 'running']

    def monitoring_logging_start(self):
        """
        A method to start the logging and monitoring of the containers. Because the the logs() and stats() methods of
        the docker api each return a stream as a blocking generator, one thread is assigned to each stream so that both
        the logs and the stats of an arbitrary number of containers can be iterated.
        """
        # Only monitor/log for started containers
        threads = []
        for container_id in [container.id for container in self.running_containers()]:
            logging_thread = threading.Thread(target=self.logs_worker, args=(container_id,))
            monitoring_thread = threading.Thread(target=self.monitoring_worker, args=(container_id,))

            threads.append(logging_thread)
            threads.append(monitoring_thread)

            logging_thread.start()
            monitoring_thread.start()

    def monitoring_worker(self, container_id):
        """
        The worker that iterates over the stats() stream of a specific container. It produces an output similar to the
        'docker stats' command. The output is stdout and the data can also be saved in a file, Monitoring.log, if
        SAVE_MONITORING is True.
        :param container_id: The ID of the container to get the stats.
        :type container_id: str
        """
        with open('./Monitoring.log', 'a') as outfile:
            for line in self.docker_client.containers.get(container_id).stats(stream=True):
                # Option to print the complete line of the stats() output, for completion.
                if RAW_MONITORING:
                    print line
                stats_dict = ast.literal_eval(line)

                mem_usage = np.round(np.divide(stats_dict['memory_stats']['usage'], float(np.square(1024))), decimals=2)
                mem_limit = np.round(np.divide(stats_dict['memory_stats']['limit'], float(np.square(1024))), decimals=2)
                mem_percentage = np.multiply(np.round(np.divide(mem_usage, mem_limit), decimals=2), 100)
                cpu_kernel_usage = stats_dict["cpu_stats"]["cpu_usage"]["usage_in_kernelmode"]
                cpu_total_usage = stats_dict["cpu_stats"]["system_cpu_usage"]
                cpu_percentage = np.multiply(
                    np.round(np.divide(float(cpu_kernel_usage), int(cpu_total_usage)), decimals=4), 100)
                network_adapter = stats_dict['networks'].keys()[0]
                network_usage_i = np.round(np.divide(stats_dict['networks'][network_adapter]['rx_bytes'], float(1024)),
                                           decimals=2)
                network_usage_o = np.round(np.divide(stats_dict['networks'][network_adapter]['tx_bytes'], float(1024)),
                                           decimals=2)
                try:
                    block_i = np.round(
                        np.divide(stats_dict['blkio_stats']['io_service_bytes_recursive'][0]['value'], float(1024)),
                        decimals=2)
                    block_o = np.round(
                        np.divide(stats_dict['blkio_stats']['io_service_bytes_recursive'][1]['value'], float(1024)),
                        decimals=2)
                except IndexError:
                    block_i = 0.0
                    block_o = 0.0
                pids = stats_dict["pids_stats"]["current"]

                monitor_line = 'Container ID: {}\tCPU %: {}\tMem Usage/Limit: {} Mib/{} Mib\tMem %: {}\t' \
                               'Net I/O: {} kB/{} kB\tBlock I/O: {} kB/{} kB\tPIDS: {}'. \
                    format(container_id, cpu_percentage, mem_usage, mem_limit, mem_percentage,
                           network_usage_i, network_usage_o, block_i, block_o, pids)
                print monitor_line

                if SAVE_MONITORING:
                    outfile.write(monitor_line + '\n')
                    outfile.flush()

    def logs_worker(self, container_id):
        """
        The worker that iterates over the logs() stream of a specific container.
        The output is saved in the standard log file.
        :param container_id: The ID of the container to get the stats.
        :type container_id: str
        """
        docker_container = self.docker_client.containers.get(container_id)
        for line in docker_container.logs(stdout=True, stderr=True, since=int(time.time()), stream=True):
            logger.debug('{} : {}'.format(docker_container.name, line.strip()))


class DockerImage(object):
    def __init__(self, docker_client, path, tag):
        """
        Constructor. it calls docker_client.images.build() to create the docker image.
        :param docker_client: The client object.
        :type docker_client: DockerClient
        :param path: The path to the folder where a Dockerfile exists.
        :type path: str
        :param tag: The tag(name) to give to the created image.
        :type tag: str
        """
        # Building the image
        logger.info('Please wait while image is being built.')
        try:
            self.docker_image_obj = docker_client.images.build(path=path, tag=tag)
            self.short_id = self.docker_image_obj.short_id
            self.id = self.docker_image_obj.id
            self.tag = self.docker_image_obj.tags[0]
            logger.info('Docker image "{}" built successfully.'.format(self.tag))
            self.created_successfully = True
        except (TypeError, BuildError, APIError), e:
            logger.error('Docker image build failed with error message: {}'.format(e))
            self.created_successfully = False


class DockerContainer(object):
    def __init__(self, docker_client, image, name='', port=5000):
        """
        Constructor. it calls docker_client.containers.create() to create the docker container without starting it.
        :param docker_client: The client object.
        :type docker_client: DockerClient
        :param image: The image id to use for creating the container.
        :type image: str
        :param name: The name to give to the container
        :type name: str
        :param port: The port to that the web_app inside the container will use.
        :type port: str
        """
        self.created_successfully = False

        # Creating the container.
        logger.info('Creating container.')
        try:
            if name:
                self.container_obj = docker_client.containers.create(image, detach=True, name=name, ports={5000: port})
            else:
                self.container_obj = docker_client.containers.create(image, detach=True, ports={5000: port})
            self.short_id = self.container_obj.short_id
            self.id = self.container_obj.id
            self.name = self.container_obj.name
            self.status = self.container_obj.status
            logger.info('Container "{}" built successfully.'.format(self.name))
            self.created_successfully = True
            self.port = port
        except (TypeError, ImageNotFound, APIError), e:
            logger.error('Container creation failed with error message: {}'.format(e))

    def refresh_status(self, status):
        self.status = status
